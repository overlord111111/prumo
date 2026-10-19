"""Mapa de tipos de um assembly .NET (ECMA-335) — o atalho dos jogos Unity/Mono.

Por que existe: um jogo Unity com backend Mono entrega `Assembly-CSharp.dll`, e nesse
formato os nomes de classe e campo continuam legíveis. Em vez de despejar o assembly
inteiro no contexto do agente (caro e ruidoso), o `map` produz um dossiê **ranqueado
pelo alvo** e cortado por orçamento de tokens.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PRIMITIVOS = {
    0x01: "void",
    0x02: "bool",
    0x03: "char",
    0x04: "sbyte",
    0x05: "byte",
    0x06: "short",
    0x07: "ushort",
    0x08: "int",
    0x09: "uint",
    0x0A: "long",
    0x0B: "ulong",
    0x0C: "float",
    0x0D: "double",
    0x0E: "string",
    0x18: "intptr",
    0x19: "uintptr",
    0x1C: "object",
}
NUMERICOS = {"float", "double", "int", "uint", "short", "ushort", "long", "ulong", "byte", "sbyte"}


@dataclass
class Campo:
    nome: str
    tipo: str
    publico: bool = False
    estatico: bool = False


@dataclass
class Classe:
    nome: str
    namespace: str
    campos: list[Campo] = field(default_factory=list)
    metodos: int = 0

    @property
    def nome_completo(self) -> str:
        return f"{self.namespace}.{self.nome}" if self.namespace else self.nome


def disponivel() -> bool:
    try:
        import dnfile  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def _ler_uint_comprimido(dados: bytes, indice: int) -> tuple[int, int]:
    primeiro = dados[indice]
    if primeiro & 0x80 == 0:
        return primeiro, indice + 1
    if primeiro & 0xC0 == 0x80:
        valor = ((primeiro & 0x3F) << 8) | dados[indice + 1]
        return valor, indice + 2
    if primeiro & 0xE0 == 0xC0:
        valor = (
            ((primeiro & 0x1F) << 24)
            | (dados[indice + 1] << 16)
            | (dados[indice + 2] << 8)
            | dados[indice + 3]
        )
        return valor, indice + 4
    raise ValueError("inteiro comprimido inválido na assinatura")


def _nome_tipo(pe: Any, valor: int, tipo_ref: bool) -> str:
    """Resolve TypeDefOrRef (código 2 bits + índice)."""
    rid = valor >> 2
    if not tipo_ref:
        tabela = pe.net.mdtables.TypeDef
        if 1 <= rid <= len(tabela.rows):
            linha = tabela.rows[rid - 1]
            nome = str(linha.TypeName)
            espaco = str(linha.TypeNamespace or "")
            return f"{espaco}.{nome}" if espaco else nome
        return f"typedef#{rid}"
    tabela = pe.net.mdtables.TypeRef
    if 1 <= rid <= len(tabela.rows):
        linha = tabela.rows[rid - 1]
        nome = str(linha.TypeName)
        espaco = str(linha.TypeNamespace or "")
        return f"{espaco}.{nome}" if espaco else nome
    return f"typeref#{rid}"


def _decodificar_tipo(pe: Any, dados: bytes, indice: int) -> tuple[str, int]:
    elemento = dados[indice]
    indice += 1
    if elemento in PRIMITIVOS:
        return PRIMITIVOS[elemento], indice
    if elemento in (0x11, 0x12):  # VALUETYPE / CLASS
        valor, indice = _ler_uint_comprimido(dados, indice)
        tag = valor & 0x3
        return _nome_tipo(pe, valor, tipo_ref=(tag == 1)), indice
    if elemento == 0x1D:  # SZARRAY
        interno, indice = _decodificar_tipo(pe, dados, indice)
        return f"{interno}[]", indice
    if elemento == 0x14:  # ARRAY
        interno, indice = _decodificar_tipo(pe, dados, indice)
        _, indice = _ler_uint_comprimido(dados, indice)
        _, indice = _ler_uint_comprimido(dados, indice)
        _, indice = _ler_uint_comprimido(dados, indice)
        return f"{interno}[,]", indice
    if elemento == 0x15:  # GENERICINST
        _, indice = _decodificar_tipo(pe, dados, indice)
        quantidade, indice = _ler_uint_comprimido(dados, indice)
        for _ in range(quantidade):
            _, indice = _decodificar_tipo(pe, dados, indice)
        return "generic", indice
    if elemento == 0x0F:  # PTR
        interno, indice = _decodificar_tipo(pe, dados, indice)
        return f"{interno}*", indice
    return f"tipo0x{elemento:02X}", indice


def ler(assembly: str | Path) -> dict[str, Any]:
    """Lê o assembly e devolve a estrutura (classes + campos + tipos)."""
    if not disponivel():
        raise RuntimeError(
            "o comando `map` requer o extra dnfile: pipx inject prumo dnfile "
            "(ou pip install 'prumo[map] @ git+https://github.com/overlord111111/prumo')"
        )
    import dnfile

    caminho = Path(assembly)
    if not caminho.is_file():
        raise FileNotFoundError(f"assembly não encontrado: {caminho}")
    bruto = caminho.read_bytes()
    pe = dnfile.dnPE(str(caminho))
    if not pe.net:
        raise ValueError(f"{caminho.name} não é um assembly .NET (ECMA-335)")

    classes: list[Classe] = []
    tabela_def = pe.net.mdtables.TypeDef
    for linha in tabela_def.rows:
        classe = Classe(nome=str(linha.TypeName), namespace=str(linha.TypeNamespace or ""))
        for referencia in linha.FieldList or []:
            try:
                campo = referencia.row
            except Exception:  # pragma: no cover - linha inválida em assembly exótico
                continue
            nome_bruto = getattr(campo, "Name", None)
            if not nome_bruto:
                continue
            nome = str(nome_bruto)
            tipo = "?"
            try:
                assinatura = campo.Signature.value
                if assinatura and assinatura[0] == 0x06:
                    tipo, _ = _decodificar_tipo(pe, bytes(assinatura), 1)
            except Exception:  # pragma: no cover - assinatura não decodificável
                pass
            flags = getattr(campo, "Flags", None)
            classe.campos.append(
                Campo(
                    nome=nome,
                    tipo=tipo,
                    publico=bool(getattr(flags, "fdPublic", False)),
                    estatico=bool(getattr(flags, "fdStatic", False)),
                )
            )
        classe.metodos = len(linha.MethodList or [])
        classes.append(classe)

    return {
        "assembly": caminho.name,
        "sha256": hashlib.sha256(bruto).hexdigest(),
        "tamanho_bytes": len(bruto),
        "classes_total": len(classes),
        "campos_total": sum(len(c.campos) for c in classes),
        "classes": [
            {
                "nome": c.nome,
                "namespace": c.namespace,
                "nome_completo": c.nome_completo,
                "metodos": c.metodos,
                "campos": [
                    {"nome": f.nome, "tipo": f.tipo, "publico": f.publico, "estatico": f.estatico}
                    for f in c.campos
                ],
            }
            for c in classes
        ],
    }


def pontuar(mapa: dict[str, Any], alvo: str) -> list[dict[str, Any]]:
    """Rankeia classes pelo alvo: nome do campo > nome da classe > tipo numérico."""
    termo = alvo.lower()
    pontuadas: list[tuple[float, dict[str, Any], list[dict[str, Any]]]] = []
    for classe in mapa.get("classes", []):
        casados = []
        pontos = 0.0
        nome_classe = classe["nome"].lower()
        if nome_classe == termo:
            pontos += 3.0
        elif termo in nome_classe:
            pontos += 1.0
        for campo in classe.get("campos", []):
            nome = campo["nome"].lower()
            if nome == termo:
                pontos += 4.0
                casados.append(campo)
            elif termo in nome:
                pontos += 1.5
                casados.append(campo)
            elif campo["tipo"] in NUMERICOS:
                pontos += 0.1
        if pontos > 0:
            pontuadas.append((pontos, classe, casados))
    pontuadas.sort(key=lambda trio: (-trio[0], -len(trio[1].get("campos", []))))
    return [
        {"pontos": round(p, 2), "classe": c, "campos_casados": casados} for p, c, casados in pontuadas
    ]


def dossie(mapa: dict[str, Any], alvo: str, orcamento: int = 3000) -> tuple[str, int, int]:
    """Texto markdown ranqueado, cortado por orçamento de tokens (estimativa chars/4)."""
    linhas: list[str] = []
    linhas.append(f"# Mapa de tipos — {mapa['assembly']}")
    linhas.append("")
    linhas.append(
        f"`sha256 {mapa['sha256'][:16]}…` · {mapa['classes_total']} classes · "
        f"{mapa['campos_total']} campos · alvo: **{alvo}**"
    )
    linhas.append("")
    linhas.append("| # | classe | campos | casados com o alvo |")
    linhas.append("|---|---|---|---|")
    ranqueadas = pontuar(mapa, alvo)
    usados = 0
    incluidas: list[dict[str, Any]] = []
    for indice, item in enumerate(ranqueadas, start=1):
        classe = item["classe"]
        casados = ", ".join(f"{c['nome']}:{c['tipo']}" for c in item["campos_casados"][:5]) or "—"
        nome_completo = classe.get("nome_completo") or (
            f"{classe['namespace']}.{classe['nome']}" if classe.get("namespace") else classe["nome"]
        )
        linha = f"| {indice} | `{nome_completo}` | {len(classe['campos'])} | {casados} |"
        estimativa = len(linha) // 4 + 1
        if usados + estimativa > orcamento:
            break
        usados += estimativa
        linhas.append(linha)
        incluidas.append(item)
    linhas.append("")
    for item in incluidas[:8]:
        classe = item["classe"]
        nome_completo = classe.get("nome_completo") or (
            f"{classe['namespace']}.{classe['nome']}" if classe.get("namespace") else classe["nome"]
        )
        linhas.append(f"## {nome_completo}  (pontos {item['pontos']})")
        linhas.append(f"métodos: {classe['metodos']} · campos: {len(classe['campos'])}")
        linhas.append("")
        for campo in classe["campos"][:24]:
            marca = " ⬅" if campo in item["campos_casados"] else ""
            linhas.append(f"- `{campo['nome']}` : {campo['tipo']}{marca}")
        linhas.append("")
    texto = "\n".join(linhas)
    return texto, len(ranqueadas), usados
