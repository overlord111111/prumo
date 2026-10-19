"""Testes do diagnóstico: risco, alertas e integridade do plano."""

from __future__ import annotations

import pytest

from prumo import diagnostico


def test_plano_single_sem_ac_tem_risco_nenhum():
    plano = diagnostico.gerar_plano("unity-mono", "nenhum", "single")
    assert plano.risco == "nenhum"
    assert plano.passos
    assert any("obrigatório" == p["gate"] for p in plano.passos)


def test_plano_online_com_battleye_sobe_o_risco_e_alerta():
    plano = diagnostico.gerar_plano("unity-mono", "battleye", "online")
    assert plano.risco in ("alto", "muito alto")
    assert any("corrida de detecção" in a for a in plano.alertas)
    assert plano.alternativas


def test_vanguard_sempre_alerta_e_oferece_alternativa():
    plano = diagnostico.gerar_plano("source2", "vanguard", "single")
    assert any("Vanguard" in a for a in plano.alertas)
    assert plano.alternativas


def test_vac_online_alerta_ban_atrasado():
    plano = diagnostico.gerar_plano("source2", "vac", "online")
    assert any("onda" in a or "atrasado" in a for a in plano.alertas)


def test_modo_invalido_levanta_erro():
    with pytest.raises(ValueError):
        diagnostico.gerar_plano("unity-mono", "nenhum", "servidor-publico")


def test_todo_passo_tem_check_valido():
    from prumo import dados

    ids = {c["id"] for c in dados.checks()}
    for motor_id in dados.ids_motores():
        plano = diagnostico.gerar_plano(motor_id, "nenhum", "single")
        for passo in plano.passos:
            assert passo["checks"], f"{motor_id}/{passo['id']} sem check"
            assert set(passo["checks"]).issubset(ids)


def test_markdown_contem_secoes_obrigatorias():
    plano = diagnostico.gerar_plano("unity-mono", "battleye", "lan")
    texto = diagnostico.render_markdown(plano)
    for secao in ("## Pré-requisitos", "## Passos", "## Limitações deste motor"):
        assert secao in texto
    assert "| # | passo | checks obrigatórios | risco |" in texto


def test_json_serializavel():
    import json

    plano = diagnostico.gerar_plano("unreal", "eac", "online")
    json.dumps(plano.como_dict())
