"""Peças compartilhadas entre adaptadores (lógica pura, testável em qualquer plataforma)."""

from __future__ import annotations

from .base import Modulo, Regiao

NAO_VARRER = ("[vvar]", "[vsyscall]", "[vdso]")


def juntar_regioes_em_modulos(regioes: list[Regiao]) -> list[Modulo]:
    """Agrupa regiões contíguas do mesmo arquivo em um único módulo.

    Cada sistema descreve memória de um jeito, mas a pergunta do check é sempre a mesma:
    onde começa o módulo e qual o tamanho total mapeado.
    """
    agrupados: dict[str, Modulo] = {}
    for regiao in regioes:
        if not regiao.caminho:
            continue
        atual = agrupados.get(regiao.caminho)
        if atual is None:
            agrupados[regiao.caminho] = Modulo(regiao.caminho, regiao.inicio, regiao.tamanho)
        else:
            inicio = min(atual.base, regiao.inicio)
            fim = max(atual.base + atual.tamanho, regiao.fim)
            agrupados[regiao.caminho] = Modulo(regiao.caminho, inicio, fim - inicio)
    return sorted(agrupados.values(), key=lambda modulo: modulo.base)


def varrervavel(regiao: Regiao) -> bool:
    """Região que vale a pena varrer: legível, de tamanho razoável e não de sistema."""
    return (
        regiao.legivel
        and 0 < regiao.tamanho <= 512 * 1024 * 1024
        and regiao.caminho not in NAO_VARRER
    )
