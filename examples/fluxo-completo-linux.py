#!/usr/bin/env python3
"""Demonstração reprodutível do fluxo completo, sem jogo e sem Cheat Engine.

Sobe um processo filho que expõe um array de inteiros em memória, muda o primeiro
valor depois de meio segundo, e roda os comandos do prumo contra ele. Serve como
prova de que o adaptador local, a leitura tipada, o check de campo e a varredura de
assinatura funcionam de ponta a ponta.

Uso:  python examples/fluxo-completo-linux.py [saida.txt]
Requer Linux (usa /proc). Não altera nada fora do processo filho.
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import time
from pathlib import Path

FILHO = r"""
import ctypes, os, time

# Permite que outro processo do mesmo usuário (o prumo) leia esta memória.
# Sem isso, o Yama (ptrace_scope=1) só deixa o processo-pai ler.
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.prctl(0x59616D61, ctypes.c_ulong(-1), 0, 0, 0)  # PR_SET_PTRACER, PR_SET_PTRACER_ANY

valores = (ctypes.c_int32 * 4)(111, 222, 333, 444)
assinatura = ctypes.create_string_buffer(b"PRUMO-assinatura-de-teste-42")
print(os.getpid(), ctypes.addressof(valores), ctypes.addressof(assinatura), flush=True)
time.sleep(0.5)
valores[0] = 777
time.sleep(10)
"""


def executar(comando: list[str]) -> str:
    resultado = subprocess.run(comando, capture_output=True, text=True, check=False)
    saida = (resultado.stdout + resultado.stderr).rstrip()
    return saida


def main() -> int:
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("examples/fluxo-completo-linux.txt")
    filho = subprocess.Popen([sys.executable, "-c", FILHO], stdout=subprocess.PIPE, text=True)
    assert filho.stdout is not None
    linha = filho.stdout.readline().split()
    pid, endereco = int(linha[0]), int(linha[1])

    linhas: list[str] = [
        "# Fluxo completo num processo real (Linux, adaptador local)",
        "",
        "Processo filho expõe um array de inteiros e muda o primeiro valor 0,5 s depois.",
        f"PID {pid} · endereço do array 0x{endereco:X}",
        "",
        "## prumo processo",
        executar(["prumo", "processo", "--pid", str(pid), "--limite", "6"]),
        "",
        "## prumo ler (antes da ação)",
        executar(["prumo", "ler", "--pid", str(pid), "--endereco", hex(endereco), "--tipo", "int32"]),
        "",
    ]
    time.sleep(0.7)
    linhas += [
        "## prumo ler (depois da ação)",
        executar(["prumo", "ler", "--pid", str(pid), "--endereco", hex(endereco), "--tipo", "int32"]),
        "",
        "## prumo verificar --check campo (testemunho antes/depois)",
        executar(["prumo", "verificar", "--check", "campo", "--antes", "111", "--depois", "777"]),
        "",
        "## prumo varrer (assinatura com 12 bytes fixos)",
        executar(
            [
                "prumo", "varrer", "--pid", str(pid),
                "--padrao", "50 52 55 4D 4F 2D 61 73 73 69 6E 61", "--max", "5",
            ]
        ),
        "",
    ]
    filho.kill()
    filho.wait(timeout=10)
    texto = "\n".join(linhas)
    destino.write_text(texto, encoding="utf-8")
    print(texto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
