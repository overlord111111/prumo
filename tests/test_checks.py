"""Testes dos checks — a parte que precisa de prova real."""

from __future__ import annotations

import math

import pytest

from prumo import checks

MATRIZ_IDENTIDADE = [
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0,
]


def test_parse_padrao_com_curingas():
    assert checks.parse_padrao("48 8B ?? 05") == [0x48, 0x8B, None, 0x05]


def test_parse_padrao_aceita_bloco_colado():
    assert checks.parse_padrao("488B05") == [0x48, 0x8B, 0x05]


def test_parse_padrao_rejeita_vazio():
    with pytest.raises(ValueError):
        checks.parse_padrao("   ")


PADRAO = "48 8B 05 ?? ?? 33 44 66 77 88 99 AA BB"
ALVO = bytes.fromhex("488b051122334466778899aabb")


def test_assinatura_unica_passa():
    padrao = PADRAO
    alvo = ALVO
    buffer = bytes(64) + alvo + bytes(64)
    resultado = checks.check_assinatura(padrao, buffer)
    assert resultado.status == checks.PASS
    assert resultado.medida.startswith("hits=1")


def test_assinatura_repetida_falha():
    padrao = PADRAO
    alvo = ALVO
    buffer = bytes(16) + alvo + bytes(16) + alvo + bytes(16)
    resultado = checks.check_assinatura(padrao, buffer)
    assert resultado.status == checks.FAIL
    assert "não é única" in resultado.detalhe


def test_assinatura_com_poucos_bytes_fixos_falha():
    resultado = checks.check_assinatura("48 ?? ?? ?? 99", bytes(32) + b"\x48\x00\x00\x00\x99" + bytes(32))
    assert resultado.status == checks.FAIL
    assert "bytes fixos" in resultado.detalhe


def test_projecao_identidade_leva_origem_ao_centro():
    x, y, visivel = checks.mundo_para_tela(MATRIZ_IDENTIDADE, (0.0, 0.0, 0.5), 1920, 1080)
    assert visivel
    assert math.isclose(x, 960.0, abs_tol=1e-6)
    assert math.isclose(y, 540.0, abs_tol=1e-6)


def test_projecao_ponto_dentro_da_tolerancia_passa():
    resultado = checks.check_projecao(MATRIZ_IDENTIDADE, (0.0, 0.0, 0.5), 1920, 1080, esperado=(960, 540))
    assert resultado.status == checks.PASS


def test_projecao_ponto_fora_da_tolerancia_falha():
    resultado = checks.check_projecao(MATRIZ_IDENTIDADE, (0.0, 0.0, 0.5), 1920, 1080, esperado=(100, 100))
    assert resultado.status == checks.FAIL


def test_projecao_atras_da_camera_falha():
    matriz = [1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, -1.0, 0]
    resultado = checks.check_projecao(matriz, (0.0, 0.0, 1.0), 1920, 1080)
    assert resultado.status == checks.FAIL


def test_estrutura_encontra_classe_e_campo_do_alvo():
    mapa = {
        "classes": [
            {"nome": "Player", "namespace": "Game", "campos": [
                {"nome": "health", "tipo": "float"},
                {"nome": "name", "tipo": "string"},
            ], "metodos": 4}
        ]
    }
    resultado = checks.check_estrutura(mapa, "Player", "health")
    assert resultado.status == checks.PASS
    assert "health:float" in resultado.detalhe


def test_estrutura_falha_quando_classe_nao_existe():
    mapa = {"classes": [{"nome": "Outra", "namespace": "", "campos": [], "metodos": 0}]}
    resultado = checks.check_estrutura(mapa, "Player")
    assert resultado.status == checks.FAIL


def test_checks_de_processo_vivo_sao_indeterminados():
    for check_id in ("processo", "campo", "entidades"):
        resultado = checks.executar(check_id)
        assert resultado.status == checks.INDETERMINADO
        assert "Requer:" in resultado.detalhe


def test_check_desconhecido_levanta_erro():
    with pytest.raises(ValueError):
        checks.executar("inexistente")
