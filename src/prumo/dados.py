"""Leitura e validação dos dados (motores, anti-cheats e checks).

Os dados são JSON versionados dentro do pacote: uma única fonte de verdade que gera
tanto o diagnóstico quanto a documentação (ver `prumo.docs`). Fonte de verdade
editável = `src/prumo/data/`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Any

MOTORES = ("unity-mono", "unity-il2cpp", "unreal", "source2")
ACS = ("nenhum", "battleye", "eac", "vac", "vanguard")
CAMPOS_OBRIGATORIOS_MOTOR = ("id", "nome", "resumo", "acesso", "passos", "limitacoes")
CAMPOS_OBRIGATORIOS_AC = ("id", "nome", "resumo", "camadas", "detecta", "escada")


class DadosInvalidos(Exception):
    """Erro de integridade nos dados versionados."""


@dataclass(frozen=True)
class ResultadoValidacao:
    arquivo: str
    ok: bool
    problemas: tuple[str, ...] = ()


def _ler(caminho: str) -> dict[str, Any]:
    try:
        texto = resources.files("prumo.data").joinpath(caminho).read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError) as exc:  # pragma: no cover - ambiente quebrado
        raise DadosInvalidos(f"arquivo de dados ausente: {caminho}") from exc
    try:
        return json.loads(texto)
    except json.JSONDecodeError as exc:
        raise DadosInvalidos(f"JSON inválido em {caminho}: {exc}") from exc


@lru_cache(maxsize=32)
def motor(motor_id: str) -> dict[str, Any]:
    """Carrega e valida o playbook de um motor."""
    if motor_id not in MOTORES:
        raise DadosInvalidos(f"motor desconhecido: {motor_id} (válidos: {', '.join(MOTORES)})")
    dados = _ler(f"motores/{motor_id}.json")
    _validar(dados, CAMPOS_OBRIGATORIOS_MOTOR, f"motores/{motor_id}.json")
    if dados["id"] != motor_id:
        raise DadosInvalidos(f"id interno {dados['id']!r} não bate com o arquivo {motor_id!r}")
    return dados


@lru_cache(maxsize=32)
def ac(ac_id: str) -> dict[str, Any]:
    """Carrega e valida o playbook de um anti-cheat."""
    if ac_id not in ACS:
        raise DadosInvalidos(f"anti-cheat desconhecido: {ac_id} (válidos: {', '.join(ACS)})")
    dados = _ler(f"ac/{ac_id}.json")
    _validar(dados, CAMPOS_OBRIGATORIOS_AC, f"ac/{ac_id}.json")
    if dados["id"] != ac_id:
        raise DadosInvalidos(f"id interno {dados['id']!r} não bate com o arquivo {ac_id!r}")
    return dados


@lru_cache(maxsize=1)
def checks() -> list[dict[str, Any]]:
    """Carrega o registro dos 7 checks."""
    dados = _ler("checks.json")
    lista = dados.get("checks", [])
    if len(lista) != 7:
        raise DadosInvalidos(f"esperados 7 checks, encontrados {len(lista)}")
    ids = [c["id"] for c in lista]
    if len(set(ids)) != len(ids):
        raise DadosInvalidos("ids de check repetidos")
    return lista


def ids_motores() -> tuple[str, ...]:
    return MOTORES


def ids_acs() -> tuple[str, ...]:
    return ACS


def validar_tudo() -> list[ResultadoValidacao]:
    """Valida todos os arquivos de dados (usado pela CI e pelo `prumo docs --check`)."""
    resultados: list[ResultadoValidacao] = []
    for motor_id in MOTORES:
        try:
            motor(motor_id)
            resultados.append(ResultadoValidacao(f"motores/{motor_id}.json", True))
        except DadosInvalidos as exc:
            resultados.append(ResultadoValidacao(f"motores/{motor_id}.json", False, (str(exc),)))
    for ac_id in ACS:
        try:
            ac(ac_id)
            resultados.append(ResultadoValidacao(f"ac/{ac_id}.json", True))
        except DadosInvalidos as exc:
            resultados.append(ResultadoValidacao(f"ac/{ac_id}.json", False, (str(exc),)))
    try:
        checks()
        resultados.append(ResultadoValidacao("checks.json", True))
    except DadosInvalidos as exc:
        resultados.append(ResultadoValidacao("checks.json", False, (str(exc),)))
    return resultados


def _validar(dados: dict[str, Any], campos: tuple[str, ...], arquivo: str) -> None:
    faltando = [c for c in campos if c not in dados]
    if faltando:
        raise DadosInvalidos(f"{arquivo}: campos ausentes: {', '.join(faltando)}")
    for passo in dados.get("passos", []):
        for campo in ("id", "titulo", "detalhe", "checks"):
            if campo not in passo:
                raise DadosInvalidos(f"{arquivo}: passo {passo.get('id', '?')} sem campo {campo!r}")
        validos = {c["id"] for c in checks()}
        invalidos = [c for c in passo["checks"] if c not in validos]
        if invalidos:
            raise DadosInvalidos(f"{arquivo}: passo {passo['id']} cita checks inexistentes: {invalidos}")
