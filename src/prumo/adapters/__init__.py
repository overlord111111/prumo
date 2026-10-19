"""Adaptadores de processo.

Regra do projeto: nenhum check de processo vivo inventa resultado. Sem adaptador,
o veredito é `INDETERMINADO` com o requisito escrito.
"""

from __future__ import annotations

import os

from .base import Adaptador, AdaptadorIndisponivel, FalhaDeLeitura, Modulo, Regiao
from .comum import juntar_regioes_em_modulos, varrervavel
from .local import ProcessoLocal

__all__ = [
    "Adaptador",
    "AdaptadorIndisponivel",
    "FalhaDeLeitura",
    "Modulo",
    "ProcessoLocal",
    "Regiao",
    "abrir",
    "disponiveis",
    "juntar_regioes_em_modulos",
    "varrervavel",
]


def disponiveis() -> tuple[str, ...]:
    """Adaptadores que fazem sentido nesta plataforma."""
    if os.name == "nt":
        return ("windows",)
    if os.path.isdir("/proc"):
        return ("local",)
    return ()


def abrir(pid: int, nome: str | None = None) -> Adaptador:
    """Abre um adaptador. Sem nome, escolhe o da plataforma atual."""
    escolhido = nome or (disponiveis()[0] if disponiveis() else "")
    if escolhido == "local":
        return ProcessoLocal(pid)
    if escolhido == "windows":
        from .windows import ProcessoWindows  # import tardio: o módulo usa ctypes.WinDLL

        return ProcessoWindows(pid)
    raise AdaptadorIndisponivel(
        f"nenhum adaptador disponível para esta plataforma ({os.name}). "
        "Use um servidor MCP de memória (docs/adaptadores.md) e verifique pelos dados."
    )
