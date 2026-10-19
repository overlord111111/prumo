"""Contrato de adaptador: a fronteira entre o prumo e as "mãos".

O prumo não implementa leitura de processo para cada plataforma. Ele define o que um
adaptador precisa responder e confia no que voltar — por isso todo dado carrega origem
e todo check devolve `INDETERMINADO` quando o adaptador não está disponível.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class AdaptadorIndisponivel(Exception):
    """O adaptador existe no projeto, mas não pode operar neste ambiente."""


class FalhaDeLeitura(Exception):
    """Leitura recusada pelo sistema ou endereço inválido."""


@dataclass(frozen=True)
class Modulo:
    nome: str
    base: int
    tamanho: int

    def contem(self, endereco: int) -> bool:
        return self.base <= endereco < self.base + self.tamanho

    @property
    def nome_modulo(self) -> str:
        return self.nome.rsplit("/", 1)[-1]


@dataclass(frozen=True)
class Regiao:
    inicio: int
    fim: int
    permissoes: str
    caminho: str = ""

    @property
    def tamanho(self) -> int:
        return self.fim - self.inicio

    @property
    def legivel(self) -> bool:
        return "r" in self.permissoes

    @property
    def gravavel(self) -> bool:
        return "w" in self.permissoes


@runtime_checkable
class Adaptador(Protocol):
    """O que qualquer adaptador precisa entregar.

    Implementações de referência: `prumo.adapters.local` (Linux) e o protocolo
    externo descrito em docs/adaptadores.md (Cheat Engine, Frida, qualquer bridge).
    """

    nome: str

    def processo(self) -> dict:
        """`pid`, `arquitetura` ("x86_64", "i386", ...), `executavel`."""
        ...

    def modulos(self) -> list[Modulo]:
        """Módulos carregados, com base e tamanho. O primeiro costuma ser o executável."""
        ...

    def regioes(self) -> list[Regiao]:
        """Mapa de memória do processo, em ordem de endereço."""
        ...

    def ler(self, endereco: int, tamanho: int) -> bytes:
        """Lê `tamanho` bytes. Levanta `FalhaDeLeitura` se o sistema recusar."""
        ...

    def escrever(self, endereco: int, dados: bytes) -> int:
        """Escreve e devolve quantos bytes entraram. Adaptador somente-leitura recusa."""
        ...
