"""Diagnóstico: cruza motor, anti-cheat e modo de jogo e devolve o plano com risco.

O diagnóstico não executa nada e não toca no alvo. Ele decide **qual caminho faz
sentido** (e qual queima conta) antes do primeiro passo — a parte que falta em toda
ferramenta que dá acesso mas não dá critério.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import dados

MODOS = {
    "single": {
        "rotulo": "single-player / offline",
        "risco_base": "nenhum",
        "explicacao": "nada sai da sua máquina: é o ambiente de aprendizado",
    },
    "lan": {
        "rotulo": "LAN / servidor próprio",
        "risco_base": "baixo",
        "explicacao": "servidor é seu, mas ainda é um jogo rodando: cuidado com outros jogadores",
    },
    "privado": {
        "rotulo": "servidor de comunidade (seu)",
        "risco_base": "baixo",
        "explicacao": "você controla as regras; se houver outros jogadores, a regra de respeito vale",
    },
    "online": {
        "rotulo": "servidor público / oficial",
        "risco_base": "alto",
        "explicacao": "ban é permanente e pode alcançar o hardware (HWID); a conta é sua",
    },
}

ORDEM_RISCO = ("nenhum", "baixo", "medio", "alto", "muito alto")


@dataclass
class Plano:
    motor: dict[str, Any]
    ac: dict[str, Any]
    modo: str
    resumo: str
    risco: str
    risco_por_que: list[str] = field(default_factory=list)
    pre_requisitos: list[str] = field(default_factory=list)
    passos: list[dict[str, Any]] = field(default_factory=list)
    alertas: list[str] = field(default_factory=list)
    nao_faz: list[str] = field(default_factory=list)
    alternativas: list[str] = field(default_factory=list)
    degrau_sugerido: dict[str, Any] | None = None

    def como_dict(self) -> dict[str, Any]:
        return {
            "motor": self.motor["id"],
            "ac": self.ac["id"],
            "modo": self.modo,
            "resumo": self.resumo,
            "risco": self.risco,
            "risco_por_que": self.risco_por_que,
            "pre_requisitos": self.pre_requisitos,
            "passos": self.passos,
            "alertas": self.alertas,
            "nao_faz": self.nao_faz,
            "alternativas": self.alternativas,
            "degrau_sugerido": self.degrau_sugerido,
        }


def _pior_risco(a: str, b: str) -> str:
    ia = ORDEM_RISCO.index(a) if a in ORDEM_RISCO else 0
    ib = ORDEM_RISCO.index(b) if b in ORDEM_RISCO else 0
    return ORDEM_RISCO[max(ia, ib)]


def _normalizar_risco(valor: str) -> str:
    return valor.replace("médio", "medio").replace("muito alto", "muito alto").strip().lower()


def gerar_plano(motor_id: str, ac_id: str, modo: str) -> Plano:
    """Monta o plano completo. Levanta ValueError para entrada inválida."""
    if modo not in MODOS:
        raise ValueError(f"modo inválido: {modo} (válidos: {', '.join(MODOS)})")
    motor_d = dados.motor(motor_id)
    ac_d = dados.ac(ac_id)
    info_modo = MODOS[modo]

    risco = _normalizar_risco(info_modo["risco_base"])
    motivos = [f"modo: {info_modo['rotulo']} — {info_modo['explicacao']}"]

    # A escada do AC informa o risco real de cada degrau; o degrau 0 é o único sem AC no caminho.
    degrau0 = next((d for d in ac_d["escada"] if d["nivel"] == 0), None)
    risco_ac = _normalizar_risco(degrau0["risco"]) if degrau0 else "alto"
    if degrau0 and degrau0["risco"] == "n/a":
        risco_ac = "alto"
    risco = _pior_risco(risco, risco_ac)
    motivos.append(
        f"anti-cheat: {ac_d['nome']} — camadas ativas: "
        + ", ".join(k for k, v in ac_d["camadas"].items() if v and v != "nenhuma")
    )

    passos = []
    for passo in motor_d["passos"]:
        passos.append(
            {
                "id": passo["id"],
                "titulo": passo["titulo"],
                "detalhe": passo["detalhe"],
                "checks": passo["checks"],
                "risco": passo["risco"],
                "gate": "obrigatório" if passo["risco"] in ("nenhum", "baixo") else "avaliar",
            }
        )

    alertas: list[str] = []
    alternativas: list[str] = []
    nao_faz: list[str] = []

    if ac_id == "vanguard":
        alertas.append(
            "Vanguard carrega no boot do Windows e não é alvo de laboratório: "
            "não existe configuração segura para experimentar neste jogo."
        )
        alternativas.append("escolher outro alvo (single-player ou servidor privado sem AC)")
    elif ac_id in ("battleye", "eac") and modo == "online":
        alertas.append(
            f"{ac_d['nome']} em servidor público significa corrida de detecção: "
            "nada aqui fica 'pronto', e ban é permanente (pode incluir HWID)."
        )
        alternativas.append("reproduzir o mesmo estudo em single-player/LAN do mesmo motor")
    elif ac_id == "vac" and modo == "online":
        alertas.append(
            "VAC pune por onda e com atraso: 'funcionou hoje' não é resultado — "
            "o ban pode vir semanas depois."
        )

    if modo == "online":
        nao_faz.append("usar o resultado deste plano em servidor com outros jogadores como teste")

    pre_requisitos = [
        f"acesso ao alvo: {motor_d['acesso']['alvo']}",
        f"via de leitura: {motor_d['acesso']['tipo']}",
        "adaptador de processo instalado se o passo exigir leitura viva (ver docs/adaptadores.md)",
        "sandbox/VM recomendada para qualquer binário não verificado",
    ]

    degrau = next((d for d in ac_d["escada"] if d["nivel"] == 0), None)

    resumo = (
        f"{motor_d['nome']} · {ac_d['nome']} · {info_modo['rotulo']} → "
        f"{len(passos)} passos, risco {risco}"
    )

    return Plano(
        motor=motor_d,
        ac=ac_d,
        modo=modo,
        resumo=resumo,
        risco=risco,
        risco_por_que=motivos,
        pre_requisitos=pre_requisitos,
        passos=passos,
        alertas=alertas,
        nao_faz=nao_faz,
        alternativas=alternativas,
        degrau_sugerido=degrau,
    )


def render_markdown(plano: Plano) -> str:
    """Plano em markdown — formato que o agente carrega como contexto."""
    linhas: list[str] = []
    add = linhas.append
    add(f"# Plano — {plano.motor['nome']} · {plano.ac['nome']} · {MODOS[plano.modo]['rotulo']}")
    add("")
    add(f"**Risco:** `{plano.risco}`")
    for motivo in plano.risco_por_que:
        add(f"- {motivo}")
    add("")
    add("## Pré-requisitos")
    for item in plano.pre_requisitos:
        add(f"- {item}")
    add("")
    add("## Passos (cada um exige o check em PASS antes do próximo)")
    add("")
    add("| # | passo | checks obrigatórios | risco |")
    add("|---|---|---|---|")
    for passo in plano.passos:
        add(f"| {passo['id']} | {passo['titulo']} | {', '.join(passo['checks'])} | {passo['risco']} |")
    add("")
    for passo in plano.passos:
        add(f"### {passo['id']} — {passo['titulo']}")
        add(passo["detalhe"])
        add("")
    if plano.alertas:
        add("## Alertas")
        for alerta in plano.alertas:
            add(f"- aviso: {alerta}")
        add("")
    if plano.nao_faz:
        add("## Não faz")
        for item in plano.nao_faz:
            add(f"- não: {item}")
        add("")
    if plano.alternativas:
        add("## Alternativas mais seguras")
        for item in plano.alternativas:
            add(f"- {item}")
        add("")
    add("## Limitações deste motor")
    for item in plano.motor["limitacoes"]:
        add(f"- {item}")
    return "\n".join(linhas)
