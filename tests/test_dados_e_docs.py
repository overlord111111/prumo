"""Integridade dos dados versionados e sincronização da documentação."""

from __future__ import annotations

from pathlib import Path

from prumo import dados, docs

RAIZ = Path(__file__).resolve().parents[1]


def test_todos_os_arquivos_validam():
    resultados = dados.validar_tudo()
    falhas = [r for r in resultados if not r.ok]
    assert not falhas, [f"{f.arquivo}: {f.problemas}" for f in falhas]


def test_motores_e_acs_esperados_existem():
    assert set(dados.ids_motores()) == {"unity-mono", "unity-il2cpp", "unreal", "source2"}
    assert set(dados.ids_acs()) == {"nenhum", "battleye", "eac", "vac", "vanguard"}


def test_sete_checks_registrados():
    assert len(dados.checks()) == 7


def test_escada_de_todo_ac_comeca_no_nivel_zero():
    for ac_id in dados.ids_acs():
        escada = dados.ac(ac_id)["escada"]
        assert escada[0]["nivel"] == 0, ac_id


def test_documentacao_sincronizada_com_os_dados():
    problemas = docs.verificar(RAIZ / "docs")
    assert not problemas, problemas
