"""Adaptadores de processo.

Regra do projeto: nenhum check de processo vivo inventa resultado. Sem adaptador,
o veredito é `INDETERMINADO` com o requisito escrito.
"""

from __future__ import annotations

from .base import Adaptador, AdaptadorIndisponivel, FalhaDeLeitura, Modulo, Regiao
from .local import ProcessoLocal

__all__ = [
    "Adaptador",
    "AdaptadorIndisponivel",
    "FalhaDeLeitura",
    "Modulo",
    "ProcessoLocal",
    "Regiao",
    "abrir",
]


def abrir(pid: int, nome: str = "local") -> Adaptador:
    """Abre um adaptador pelo nome. Hoje existe um de referência: `local`."""
    if nome == "local":
        return ProcessoLocal(pid)
    raise AdaptadorIndisponivel(
        f"adaptador {nome!r} não é interno; conecte-o pelo protocolo externo (docs/adaptadores.md)"
    )
