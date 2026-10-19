"""Os 7 checks do prumo.

Regra do projeto: um passo só avança com o check anterior em PASS. Quando o check
depende de processo vivo e não há adaptador conectado, o resultado é INDETERMINADO
com o motivo — nunca um PASS inventado.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import dados

NUMERICOS_SIMPLES = ("float", "double", "int", "uint", "short", "long")

PASS = "PASS"
FAIL = "FAIL"
INDETERMINADO = "INDETERMINADO"


@dataclass
class Resultado:
    check: str
    status: str
    medida: str
    detalhe: str

    def como_dict(self) -> dict[str, str]:
        return {"check": self.check, "status": self.status, "medida": self.medida, "detalhe": self.detalhe}

    def __str__(self) -> str:  # pragma: no cover - formatação
        icone = {PASS: "✔", FAIL: "✘", INDETERMINADO: "?"}[self.status]
        return f"{icone} {self.status:<14} {self.check:<11} {self.medida} — {self.detalhe}"


def registro() -> list[dict[str, Any]]:
    return dados.checks()


def _definicao(check_id: str) -> dict[str, Any]:
    for item in dados.checks():
        if item["id"] == check_id:
            return item
    raise ValueError(f"check desconhecido: {check_id}")


def indeterminado(check_id: str, motivo: str) -> Resultado:
    definicao = _definicao(check_id)
    return Resultado(
        check=check_id,
        status=INDETERMINADO,
        medida="sem medição",
        detalhe=f"{motivo} Requer: {definicao['requer']}.",
    )


# --------------------------------------------------------------------------- assinatura


def parse_padrao(padrao: str) -> list[int | None]:
    """Converte '48 8B ?? 05' em [0x48, 0x8B, None, 0x05]."""
    partes = padrao.replace(",", " ").split()
    if not partes:
        raise ValueError("padrão vazio")
    valores: list[int | None] = []
    for parte in partes:
        token = parte.strip().lower()
        if token in ("??", "?", "xx", "**"):
            valores.append(None)
            continue
        if token.startswith("0x"):
            token = token[2:]
        if len(token) not in (2, 4) and len(token) % 2 != 0:
            raise ValueError(f"byte inválido: {parte!r}")
        if len(token) > 2:
            # aceita bloco colado (ex.: 488B05) quebrando em bytes
            for i in range(0, len(token), 2):
                valores.append(int(token[i : i + 2], 16))
            continue
        valores.append(int(token, 16))
    return valores


def _varrer_ancorada(buffer: bytes, padrao: list[int | None]) -> list[int]:
    """Varredura ancorada no maior trecho fixo — O(n) na prática.

    Regex com curinga é a alternativa óbvia e é ~20x mais lenta; medição registrada
    em docs/metodologia.md.
    """
    trechos: list[tuple[int, int]] = []
    inicio: int | None = None
    for indice, valor in enumerate(padrao):
        if valor is None:
            if inicio is not None:
                trechos.append((inicio, indice))
                inicio = None
        elif inicio is None:
            inicio = indice
    if inicio is not None:
        trechos.append((inicio, len(padrao)))
    if not trechos:
        raise ValueError("padrão só com curingas: nada para ancorar")
    ancora_inicio, ancora_fim = max(trechos, key=lambda t: t[1] - t[0])
    ancora = bytes(v for v in padrao[ancora_inicio:ancora_fim] if v is not None)

    achados: list[int] = []
    posicao = 0
    while True:
        achado = buffer.find(ancora, posicao)
        if achado < 0:
            return achados
        base = achado - ancora_inicio
        if base >= 0:
            valido = True
            for deslocamento, valor in enumerate(padrao):
                if valor is None:
                    continue
                if base + deslocamento >= len(buffer) or buffer[base + deslocamento] != valor:
                    valido = False
                    break
            if valido:
                achados.append(base)
        posicao = achado + 1


def check_assinatura(padrao: str, buffer: bytes, min_fixos: int = 8) -> Resultado:
    """Unicidade + robustez da assinatura contra o próximo patch."""
    valores = parse_padrao(padrao)
    fixos = sum(1 for v in valores if v is not None)
    hits = _varrer_ancorada(buffer, valores)
    medida = f"hits={len(hits)} fixos={fixos}B total={len(valores)}B"
    if fixos < min_fixos:
        return Resultado(
            "assinatura",
            FAIL,
            medida,
            f"apenas {fixos} bytes fixos (mínimo {min_fixos}): quebra no próximo patch",
        )
    if len(hits) != 1:
        return Resultado(
            "assinatura",
            FAIL,
            medida,
            "assinatura não é única: " + ("nenhum hit" if not hits else f"{len(hits)} hits"),
        )
    return Resultado("assinatura", PASS, medida, f"única em 0x{hits[0]:X} com {fixos} bytes fixos")


# --------------------------------------------------------------------------- projeção


def _multiplicar(matriz: list[float], vetor: list[float]) -> list[float]:
    saida = []
    for linha in range(4):
        base = linha * 4
        saida.append(sum(matriz[base + coluna] * vetor[coluna] for coluna in range(4)))
    return saida


def mundo_para_tela(
    matriz: list[float], ponto: tuple[float, float, float], largura: int, altura: int
) -> tuple[float, float, bool]:
    """Projeta ponto de mundo em pixel. Matriz row-major (linha 0 = primeira)."""
    if len(matriz) != 16:
        raise ValueError(f"matriz precisa de 16 valores, recebidos {len(matriz)}")
    x, y, z = ponto
    clip = _multiplicar(matriz, [x, y, z, 1.0])
    w = clip[3]
    if w <= 0:
        return float("nan"), float("nan"), False
    ndc_x, ndc_y = clip[0] / w, clip[1] / w
    tela_x = (ndc_x * 0.5 + 0.5) * largura
    tela_y = (0.5 - ndc_y * 0.5) * altura
    visivel = 0.0 <= tela_x <= largura and 0.0 <= tela_y <= altura
    return tela_x, tela_y, visivel


def check_projecao(
    matriz: list[float],
    ponto: tuple[float, float, float],
    largura: int,
    altura: int,
    esperado: tuple[float, float] | None = None,
    tolerancia: float = 0.02,
) -> Resultado:
    tela_x, tela_y, visivel = mundo_para_tela(matriz, ponto, largura, altura)
    if not visivel:
        return Resultado("projecao", FAIL, "fora da tela", "o ponto projetado caiu fora (ou atrás da câmera)")
    if esperado is None:
        return Resultado(
            "projecao", PASS, f"({tela_x:.1f}, {tela_y:.1f})", "projetou dentro da tela (sem valor esperado)"
        )
    erro = max(abs(tela_x - esperado[0]) / largura, abs(tela_y - esperado[1]) / altura)
    medida = f"({tela_x:.1f}, {tela_y:.1f}) erro={erro * 100:.2f}%"
    if erro <= tolerancia:
        return Resultado("projecao", PASS, medida, f"dentro da tolerância de {tolerancia * 100:.0f}%")
    return Resultado("projecao", FAIL, medida, f"acima da tolerância de {tolerancia * 100:.0f}%")


# --------------------------------------------------------------------------- estrutura


def check_estrutura(mapa: dict[str, Any], classe: str, alvo: str | None = None) -> Resultado:
    """Confere se a classe existe no mapa e se a forma dela é plausível para o alvo."""
    classes = mapa.get("classes", [])
    if not classes:
        return Resultado("estrutura", FAIL, "0 classes", "mapa vazio: nenhum tipo lido do assembly")
    alvo_lower = (alvo or "").lower()
    candidatas = [c for c in classes if c.get("nome", "").lower() == classe.lower()]
    if not candidatas:
        candidatas = [c for c in classes if classe.lower() in c.get("nome", "").lower()]
    if not candidatas:
        return Resultado(
            "estrutura", FAIL, f"0 de {len(classes)} classes", f"classe {classe!r} não encontrada"
        )
    escolhida = candidatas[0]
    campos = escolhida.get("campos", [])
    if not campos:
        return Resultado(
            "estrutura",
            FAIL,
            f"{escolhida['nome']}: 0 campos",
            "classe sem campos: provavelmente não é a entidade",
        )
    achados = [c for c in campos if alvo_lower and alvo_lower in c.get("nome", "").lower()]
    medida = f"{escolhida['nome']}: {len(campos)} campos"
    if alvo_lower:
        medida += f", {len(achados)} com {alvo_lower!r}"
        if achados:
            nomes = ", ".join(f"{c['nome']}:{c['tipo']}" for c in achados[:4])
            return Resultado("estrutura", PASS, medida, f"campos candidatos: {nomes}")
        numericos = [c for c in campos if c.get("tipo") in NUMERICOS_SIMPLES]
        if numericos:
            nomes = ", ".join(f"{c['nome']}:{c['tipo']}" for c in numericos[:4])
            return Resultado("estrutura", PASS, medida, f"sem nome casando; campos numéricos: {nomes}")
        return Resultado("estrutura", FAIL, medida, "nenhum campo compatível com o alvo")
    return Resultado("estrutura", PASS, medida, "classe existe com campos (sem alvo informado)")


def executar(check_id: str, **kwargs: Any) -> Resultado:
    """Despacha um check. Os que exigem processo vivo devolvem INDETERMINADO honesto."""
    if check_id == "assinatura":
        buffer = kwargs.get("buffer")
        padrao = kwargs.get("padrao")
        if buffer is None or padrao is None:
            return indeterminado(check_id, "faltou --padrao e/ou --buffer-arquivo.")
        return check_assinatura(padrao, buffer, kwargs.get("min_fixos", 8))
    if check_id == "projecao":
        matriz = kwargs.get("matriz")
        ponto = kwargs.get("ponto")
        tela = kwargs.get("tela")
        if not matriz or not ponto or not tela:
            return indeterminado(check_id, "faltou --matriz, --ponto ou --tela.")
        largura, altura = tela
        return check_projecao(
            [float(v) for v in matriz],
            (float(ponto[0]), float(ponto[1]), float(ponto[2])),
            int(largura),
            int(altura),
            kwargs.get("esperado"),
            float(kwargs.get("tolerancia", 0.02)),
        )
    if check_id == "estrutura":
        mapa = kwargs.get("mapa")
        classe = kwargs.get("classe")
        if mapa is None or classe is None:
            return indeterminado(check_id, "faltou --mapa-arquivo e --classe.")
        return check_estrutura(mapa, classe, kwargs.get("alvo"))
    if check_id in ("processo", "campo", "entidades"):
        return indeterminado(
            check_id, "este check precisa de processo vivo e não há adaptador conectado nesta execução."
        )
    if check_id == "ac":
        return indeterminado(check_id, "rode `prumo diagnostico` para o cruzamento de motor + AC + modo.")
    raise ValueError(f"check desconhecido: {check_id}")
