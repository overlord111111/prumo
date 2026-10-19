"""Autoteste: prova, na máquina do usuário, que o adaptador realmente funciona.

Existe por um motivo prático: o adaptador de processo depende de chamadas de sistema
que não podem ser simuladas de verdade. Em vez de pedir "confie", o prumo executa
contra o próprio processo — leitura, escrita, observação de mudança e varredura — e
devolve um veredito por capacidade.

Windows: `prumo autoteste`
Linux/macOS: `prumo autoteste`
"""

from __future__ import annotations

import ctypes
import os
import platform
import sys

from . import checks
from .adapters import AdaptadorIndisponivel, FalhaDeLeitura, abrir, disponiveis

ASSINATURA = b"prumo-autoteste-assinatura-2026"


def _cabecalho() -> list[str]:
    adaps = ", ".join(disponiveis()) or "nenhum"
    return [
        f"prumo autoteste · plataforma={platform.system()} {platform.release()} · "
        f"python={platform.python_version()}",
        f"adaptadores disponíveis: {adaps}",
        "",
    ]


def executar() -> tuple[bool, list[str]]:
    """Roda a bateria e devolve (tudo passou, linhas para imprimir)."""
    linhas = _cabecalho()
    if not disponiveis():
        linhas.append("FALHOU: nenhum adaptador de processo nesta plataforma.")
        return False, linhas

    tudo_ok = True

    def registrar(nome: str, ok: bool, detalhe: str) -> None:
        nonlocal tudo_ok
        tudo_ok = tudo_ok and ok
        linhas.append(f"{'PASS' if ok else 'FALHOU':<7} {nome:<10} {detalhe}")

    # Buffers do próprio processo: nenhum toque fora daqui.
    valores = (ctypes.c_int32 * 4)(11, 22, 33, 44)
    endereco = ctypes.addressof(valores)
    assinatura = ctypes.create_string_buffer(ASSINATURA + b"\x00")
    endereco_assinatura = ctypes.addressof(assinatura)

    try:
        with abrir(os.getpid()) as adaptador:
            # 1. processo
            info = adaptador.processo()
            modulos = adaptador.modulos()
            resultado = checks.check_processo(adaptador)
            detalhe = (
                f"pid={info['pid']} arch={info['arquitetura']} modulos={len(modulos)}"
                f" — {resultado.status}"
            )
            registrar("processo", resultado.status == checks.PASS, detalhe)

            # 2. leitura tipada
            try:
                lido = checks.ler_valor(adaptador, endereco, "int32")
                ok = lido == 11
                detalhe = f"int32 em 0x{endereco:X} = {lido}"
            except (FalhaDeLeitura, ValueError) as exc:
                ok, detalhe = False, f"leitura recusada: {exc}"
            registrar("leitura", ok, detalhe)

            # 3. escrita (opt-in) e leitura de volta
            try:
                if hasattr(adaptador, "habilitar_escrita"):
                    adaptador.habilitar_escrita()
                escritos = checks.escrever_valor(adaptador, endereco, "int32", 999)
                devolvido = checks.ler_valor(adaptador, endereco, "int32")
                ok = escritos == 4 and devolvido == 999
                detalhe = f"{escritos} byte(s) escritos, lido de volta = {devolvido}"
            except (FalhaDeLeitura, PermissionError, ValueError) as exc:
                ok, detalhe = False, f"escrita recusada: {exc}"
            registrar("escrita", ok, detalhe)

            # 4. observação de mudança (o adaptador enxerga alteração feita pelo dono do buffer)
            try:
                antes = checks.ler_valor(adaptador, endereco + 4, "int32")
                valores[1] = antes + 7
                depois = checks.ler_valor(adaptador, endereco + 4, "int32")
                resultado = checks.check_campo(antes=antes, depois=depois)
                ok = resultado.status == checks.PASS and depois == antes + 7
                detalhe = f"{antes} -> {depois} (delta {depois - antes:+d})"
            except (FalhaDeLeitura, ValueError) as exc:
                ok, detalhe = False, f"observação recusada: {exc}"
            registrar("mudanca", ok, detalhe)

            # 5. varredura de assinatura
            try:
                padrao = checks.parse_padrao(" ".join(f"{b:02X}" for b in ASSINATURA[:12]))
                achados = adaptador.varrer(
                    padrao, limite_regiao=16 * 1024 * 1024, limite_total=64 * 1024 * 1024
                )
                ok = endereco_assinatura in achados
                estado = "encontrado" if ok else "NÃO encontrado"
                detalhe = f"{len(achados)} hit(s); buffer conhecido {estado}"
            except (FalhaDeLeitura, ValueError) as exc:
                ok, detalhe = False, f"varredura recusada: {exc}"
            registrar("varredura", ok, detalhe)

            # 6. recusa de escrita sem permissão explícita (higiene)
            try:
                novo = abrir(os.getpid())
                try:
                    novo.escrever(endereco, b"\x00\x00\x00\x00")
                    ok, detalhe = False, "escrita passou sem habilitar_escrita (defeito de segurança)"
                except PermissionError:
                    ok, detalhe = True, "recusou escrita sem habilitar_escrita()"
                finally:
                    novo.fechar()
            except AdaptadorIndisponivel as exc:
                ok, detalhe = False, f"não foi possível reabrir: {exc}"
            registrar("higiene", ok, detalhe)
    except AdaptadorIndisponivel as exc:
        linhas.append(f"FALHOU: {exc}")
        return False, linhas

    linhas.append("")
    linhas.append(f"RESULTADO: {'tudo funcionando' if tudo_ok else 'há falha — veja as linhas FALHOU'}")
    return tudo_ok, linhas


def main(argv: list[str] | None = None) -> int:
    ok, linhas = executar()
    print("\n".join(linhas))
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
