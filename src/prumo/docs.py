"""Geração de documentação a partir dos dados.

Regra do projeto: documentação não é escrita à mão quando pode ser derivada. Assim
playbook e documento não divergem — e a CI falha se alguém editar um sem o outro.
"""

from __future__ import annotations

from pathlib import Path

from . import dados

CABECALHO = "<!-- GERADO por `prumo docs`. Não edite à mão: edite src/prumo/data/ e rode `prumo docs`. -->\n"


def _tabela_motores() -> str:
    linhas = [
        CABECALHO,
        "# Motores cobertos\n",
        "| motor | backend | o que se lê | passos | limitações |",
        "|---|---|---|---|---|",
    ]
    for motor_id in dados.ids_motores():
        motor = dados.motor(motor_id)
        linhas.append(
            f"| **{motor['nome']}** (`{motor['id']}`) | {motor['acesso']['tipo']} | "
            f"`{motor['acesso']['alvo']}` | {len(motor['passos'])} | {len(motor['limitacoes'])} |"
        )
    linhas.append("")
    for motor_id in dados.ids_motores():
        motor = dados.motor(motor_id)
        linhas.append(f"## {motor['nome']}")
        linhas.append("")
        linhas.append(motor["resumo"])
        linhas.append("")
        linhas.append(f"**Como funciona:** {motor['como_funciona']}")
        linhas.append("")
        linhas.append("| # | passo | checks | risco |")
        linhas.append("|---|---|---|---|")
        for passo in motor["passos"]:
            linhas.append(
                f"| {passo['id']} | {passo['titulo']} | {', '.join(passo['checks'])} | {passo['risco']} |"
            )
        linhas.append("")
        linhas.append("**Limitações declaradas:**")
        for item in motor["limitacoes"]:
            linhas.append(f"- {item}")
        linhas.append("")
    return "\n".join(linhas)


def _tabela_ac() -> str:
    linhas = [
        CABECALHO,
        "# Matriz de anti-cheat\n",
        "| anti-cheat | camadas | detecta | degraus na escada |",
        "|---|---|---|---|",
    ]
    for ac_id in dados.ids_acs():
        ac = dados.ac(ac_id)
        camadas = ", ".join(chave for chave, valor in ac["camadas"].items() if valor and valor != "nenhuma")
        linhas.append(
            f"| **{ac['nome']}** (`{ac['id']}`) | {camadas or '—'} | "
            f"{len(ac['detecta'])} | {len(ac['escada'])} |"
        )
    linhas.append("")
    for ac_id in dados.ids_acs():
        ac = dados.ac(ac_id)
        linhas.append(f"## {ac['nome']}")
        linhas.append("")
        linhas.append(ac["resumo"])
        linhas.append("")
        if ac["detecta"]:
            linhas.append("**Detecta:**")
            for item in ac["detecta"]:
                linhas.append(f"- {item}")
            linhas.append("")
        if ac["nao_detecta"]:
            linhas.append("**Não detecta:**")
            for item in ac["nao_detecta"]:
                linhas.append(f"- {item}")
            linhas.append("")
        linhas.append("**Escada (custo × risco × detecção):**")
        linhas.append("")
        linhas.append("| nível | caminho | custo (dias) | risco | detecção |")
        linhas.append("|---|---|---|---|---|")
        for degrau in ac["escada"]:
            linhas.append(
                f"| {degrau['nivel']} | {degrau['nome']} | {degrau['custo_dias']} | "
                f"{degrau['risco']} | {degrau['detectabilidade']} |"
            )
        linhas.append("")
        if ac["notas"]:
            for nota in ac["notas"]:
                linhas.append(f"> {nota}")
            linhas.append("")
    return "\n".join(linhas)


def _checks_md() -> str:
    linhas = [
        CABECALHO,
        "# Os 7 checks\n",
        "| check | pergunta | implementação | requer |",
        "|---|---|---|---|",
    ]
    for item in dados.checks():
        linhas.append(f"| `{item['id']}` | {item['pergunta']} | {item['implementacao']} | {item['requer']} |")
    linhas.append("")
    for item in dados.checks():
        linhas.append(f"## `{item['id']}`")
        linhas.append("")
        linhas.append(f"**Pergunta:** {item['pergunta']}")
        linhas.append("")
        linhas.append(f"**Por que importa:** {item['por_que']}")
        linhas.append("")
        linhas.append(f"**Requer:** {item['requer']}")
        linhas.append("")
    return "\n".join(linhas)


DOCUMENTOS = {
    "matriz-ac.md": _tabela_ac,
    "motores.md": _tabela_motores,
    "checks.md": _checks_md,
}


def gerar(destino: Path) -> list[Path]:
    destino.mkdir(parents=True, exist_ok=True)
    escritos = []
    for nome, fabrica in DOCUMENTOS.items():
        caminho = destino / nome
        caminho.write_text(fabrica(), encoding="utf-8")
        escritos.append(caminho)
    return escritos


def verificar(destino: Path) -> list[str]:
    """Devolve a lista de documentos desatualizados (vazia = tudo sincronizado)."""
    problemas = []
    for nome, fabrica in DOCUMENTOS.items():
        caminho = destino / nome
        esperado = fabrica()
        if not caminho.is_file():
            problemas.append(f"{nome}: ausente")
            continue
        atual = caminho.read_text(encoding="utf-8")
        if atual != esperado:
            problemas.append(f"{nome}: desatualizado (rode `prumo docs`)")
    return problemas
