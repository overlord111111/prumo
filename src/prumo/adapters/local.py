"""Adaptador local para Linux: `/proc/<pid>/maps` e `/proc/<pid>/mem`.

É a implementação de referência do contrato. Não depende de Cheat Engine nem de
Frida e serve para duas coisas:

1. provar o fluxo completo (processo → leitura → varredura → verificação) num
   ambiente controlado;
2. validar qualquer técnica de assinatura antes de levar para o jogo.

Limite conhecido: exige o mesmo usuário e processo "dumpable". Em alvo protegido por
anti-cheat, este adaptador não serve — nem é a intenção.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from .base import AdaptadorIndisponivel, FalhaDeLeitura, Modulo, Regiao

_LINHA_MAPA = re.compile(
    r"^(?P<inicio>[0-9a-f]+)-(?P<fim>[0-9a-f]+)\s+(?P<perms>[rwxps-]{4})\s+"
    r"[0-9a-f]+\s+[0-9a-f]+:[0-9a-f]+\s+\d+\s*(?P<caminho>.*)$"
)


class ProcessoLocal:
    """Adaptador de processo na mesma máquina, via /proc."""

    nome = "local"

    def __init__(self, pid: int) -> None:
        if os.name != "posix" or not Path("/proc").is_dir():
            raise AdaptadorIndisponivel("o adaptador local exige /proc (Linux)")
        if pid <= 0:
            raise ValueError(f"pid inválido: {pid}")
        if not Path(f"/proc/{pid}").exists():
            raise AdaptadorIndisponivel(f"processo {pid} não existe")
        self.pid = pid
        self._fd: int | None = None
        self._modulos: list[Modulo] | None = None
        self._regioes: list[Regiao] | None = None
        self._somente_leitura = True

    # ------------------------------------------------------------------ ciclo de vida

    def __enter__(self) -> ProcessoLocal:
        return self

    def __exit__(self, *_excecao: object) -> None:
        self.fechar()

    def fechar(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def _arquivo(self) -> int:
        if self._fd is None:
            try:
                self._fd = os.open(f"/proc/{self.pid}/mem", os.O_RDWR)
            except PermissionError as exc:
                raise FalhaDeLeitura(
                    f"sem permissão para abrir a memória do processo {self.pid} "
                    "(mesmo usuário e processo não protegido são necessários)"
                ) from exc
        return self._fd

    # ------------------------------------------------------------------ consultas

    def processo(self) -> dict:
        executavel = os.readlink(f"/proc/{self.pid}/exe")
        return {
            "pid": self.pid,
            "arquitetura": self.arquitetura(),
            "executavel": executavel,
        }

    def arquitetura(self) -> str:
        """Lê a classe do ELF do executável (32 ou 64 bits)."""
        try:
            with open(f"/proc/{self.pid}/exe", "rb") as arquivo:
                cabecalho = arquivo.read(6)
        except OSError:
            return "desconhecida"
        if cabecalho[:4] != b"\x7fELF":
            return "desconhecida"
        return {1: "i386", 2: "x86_64"}.get(cabecalho[4], "desconhecida")

    def regioes(self) -> list[Regiao]:
        if self._regioes is not None:
            return self._regioes
        regioes: list[Regiao] = []
        try:
            texto = Path(f"/proc/{self.pid}/maps").read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise FalhaDeLeitura(f"não foi possível ler o mapa de memória: {exc}") from exc
        for linha in texto.splitlines():
            casamento = _LINHA_MAPA.match(linha)
            if not casamento:
                continue
            regioes.append(
                Regiao(
                    inicio=int(casamento.group("inicio"), 16),
                    fim=int(casamento.group("fim"), 16),
                    permissoes=casamento.group("perms")[:4],
                    caminho=casamento.group("caminho").strip(),
                )
            )
        self._regioes = regioes
        return regioes

    def modulos(self) -> list[Modulo]:
        if self._modulos is not None:
            return self._modulos
        agrupados: dict[str, Modulo] = {}
        for regiao in self.regioes():
            if not regiao.caminho.startswith("/"):
                continue
            atual = agrupados.get(regiao.caminho)
            if atual is None:
                agrupados[regiao.caminho] = Modulo(regiao.caminho, regiao.inicio, regiao.tamanho)
            else:
                novo_inicio = min(atual.base, regiao.inicio)
                novo_fim = max(atual.base + atual.tamanho, regiao.fim)
                agrupados[regiao.caminho] = Modulo(regiao.caminho, novo_inicio, novo_fim - novo_inicio)
        self._modulos = sorted(agrupados.values(), key=lambda m: m.base)
        return self._modulos

    def modulo(self, nome: str) -> Modulo | None:
        alvo = nome.lower()
        for modulo in self.modulos():
            if modulo.nome_modulo.lower() == alvo or modulo.nome.lower().endswith(alvo):
                return modulo
        return None

    def regiao_de(self, endereco: int) -> Regiao | None:
        for regiao in self.regioes():
            if regiao.inicio <= endereco < regiao.fim:
                return regiao
        return None

    # ------------------------------------------------------------------ leitura/escrita

    def ler(self, endereco: int, tamanho: int) -> bytes:
        if tamanho <= 0:
            raise ValueError("tamanho de leitura precisa ser positivo")
        try:
            return os.pread(self._arquivo(), tamanho, endereco)
        except OSError as exc:
            raise FalhaDeLeitura(f"leitura recusada em 0x{endereco:X}: {exc}") from exc

    def escrever(self, endereco: int, dados: bytes) -> int:
        if self._somente_leitura:
            raise PermissionError(
                "adaptador em modo somente leitura: escrever exige habilitar_escrita() de forma explícita"
            )
        try:
            return os.pwrite(self._arquivo(), dados, endereco)
        except OSError as exc:
            raise FalhaDeLeitura(f"escrita recusada em 0x{endereco:X}: {exc}") from exc

    def habilitar_escrita(self) -> None:
        """Escrita é opt-in explícito — coerente com a regra de higiene do projeto."""
        self._somente_leitura = False

    # ------------------------------------------------------------------ utilidades

    def varrer(self, padrao: list[int | None], limite_regiao: int = 64 * 1024 * 1024) -> list[int]:
        """Varre regiões legíveis atrás de uma assinatura e devolve endereços absolutos."""
        from ..checks import _varrer_ancorada

        achados: list[int] = []
        for regiao in self.regioes():
            if not regiao.legivel or regiao.tamanho > 512 * 1024 * 1024:
                continue
            if regiao.caminho in ("[vvar]", "[vsyscall]", "[vdso]"):
                continue
            lido = 0
            while lido < regiao.tamanho and lido < limite_regiao:
                bloco = min(4 * 1024 * 1024, regiao.tamanho - lido)
                try:
                    dados = self.ler(regiao.inicio + lido, bloco)
                except FalhaDeLeitura:
                    break
                if not dados:
                    break
                for deslocamento in _varrer_ancorada(dados, padrao):
                    achados.append(regiao.inicio + lido + deslocamento)
                lido += bloco
        return achados
