"""Testes do leitor de metadados .NET.

Os testes unitários não dependem de binário externo: exercitam o decodificador de
tipos e o ranqueador. O teste de integração roda só quando PRUMO_TEST_DLL aponta
para um assembly real (ver docs/metodologia.md § como reproduzir).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from prumo import dotnet


def test_primitive_decode_cobre_os_basicos():
    # assinatura de campo: 0x06 (FIELD) + elemento
    for elemento, esperado in ((0x08, "int"), (0x0C, "float"), (0x0D, "double"), (0x0E, "string")):
        dados = bytes([0x06, elemento])
        tipo, indice = dotnet._decodificar_tipo(None, dados, 1)
        assert tipo == esperado
        assert indice == 2


def test_szarray_decode():
    dados = bytes([0x06, 0x1D, 0x08])
    tipo, _ = dotnet._decodificar_tipo(None, dados, 1)
    assert tipo == "int[]"


def test_uint_comprimido_1_byte():
    assert dotnet._ler_uint_comprimido(b"\x7f", 0) == (0x7F, 1)


def test_uint_comprimido_2_bytes():
    valor, proximo = dotnet._ler_uint_comprimido(b"\x80\x84", 0)
    assert valor == 0x84
    assert proximo == 2


def test_ranqueador_prioriza_campo_exato():
    mapa = {
        "classes": [
            {"nome": "Player", "namespace": "G", "metodos": 3, "campos": [
                {"nome": "health", "tipo": "float", "publico": False},
                {"nome": "name", "tipo": "string", "publico": True},
            ]},
            {"nome": "HealthSystem", "namespace": "G", "metodos": 1, "campos": [
                {"nome": "maxHealth", "tipo": "float", "publico": True},
            ]},
        ]
    }
    ranking = dotnet.pontuar(mapa, "health")
    assert ranking[0]["classe"]["nome"] == "Player"
    assert ranking[0]["pontos"] > ranking[1]["pontos"]


def test_dossie_respeita_orcamento_de_tokens():
    classes = [
        {"nome": f"C{i}", "namespace": "N", "metodos": 1,
         "campos": [{"nome": f"health{i}", "tipo": "float", "publico": True} for _ in range(20)]}
        for i in range(60)
    ]
    mapa = {"assembly": "fake.dll", "sha256": "0" * 64, "classes_total": 60, "campos_total": 1200,
            "classes": classes}
    texto, total, usados = dotnet.dossie(mapa, "health", orcamento=200)
    assert total == 60
    assert usados <= 200
    assert len(texto) < 200 * 4 * 8  # cortado de fato


@pytest.mark.skipif(not os.environ.get("PRUMO_TEST_DLL"), reason="PRUMO_TEST_DLL não definido")
def test_integracao_com_assembly_real():
    caminho = Path(os.environ["PRUMO_TEST_DLL"])
    mapa = dotnet.ler(caminho)
    assert mapa["classes_total"] > 100
    assert mapa["campos_total"] > 500
    assert len(mapa["sha256"]) == 64
    # todo campo tem nome e tipo não vazio
    for classe in mapa["classes"][:50]:
        for campo in classe["campos"]:
            assert campo["nome"]
            assert campo["tipo"]
    texto, _, _ = dotnet.dossie(mapa, "health", orcamento=2000)
    assert "Mapa de tipos" in texto
