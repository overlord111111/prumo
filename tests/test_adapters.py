"""Adaptador local e checks de processo vivo — com processo real, não mock.

O teste sobe um processo filho que expõe um endereço de um array de inteiros,
muda o valor depois de meio segundo e dorme. A partir daí o teste prova, de ponta
a ponta: leitura de memória, escrita, detecção de mudança e varredura de assinatura.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

import pytest

from prumo import checks
from prumo.adapters import ProcessoLocal

pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux"), reason="o adaptador de referência é /proc (Linux)"
)

FILHO = r"""
import ctypes, os, time

valores = (ctypes.c_int32 * 4)(111, 222, 333, 444)
assinatura = ctypes.create_string_buffer(b"PRUMO-assinatura-de-teste-42")
print(os.getpid(), ctypes.addressof(valores), ctypes.addressof(assinatura), flush=True)
time.sleep(0.5)
valores[0] = 777
time.sleep(10)
"""


@pytest.fixture()
def alvo():
    processo = subprocess.Popen(
        [sys.executable, "-c", FILHO],
        stdout=subprocess.PIPE,
        text=True,
    )
    assert processo.stdout is not None
    linha = processo.stdout.readline().split()
    pid, endereco_valores, endereco_assinatura = int(linha[0]), int(linha[1]), int(linha[2])
    yield pid, endereco_valores, endereco_assinatura
    processo.kill()
    processo.wait(timeout=10)


def test_processo_descreve_alvo_real(alvo):
    pid, _, _ = alvo
    with ProcessoLocal(pid) as adaptador:
        info = adaptador.processo()
        assert info["pid"] == pid
        assert info["arquitetura"] in ("x86_64", "i386")
        assert "python" in os.path.basename(info["executavel"]).lower()
        modulos = adaptador.modulos()
        assert len(modulos) >= 2
        assert all(m.base > 0 and m.tamanho > 0 for m in modulos)
        assert adaptador.regioes(), "mapa de memória vazio"


def test_le_valor_tipado(alvo):
    pid, endereco, _ = alvo
    with ProcessoLocal(pid) as adaptador:
        assert checks.ler_valor(adaptador, endereco, "int32") == 111
        assert checks.ler_valor(adaptador, endereco + 4, "int32") == 222


def test_escrita_exige_habilitacao_e_funciona(alvo):
    pid, endereco, _ = alvo
    with ProcessoLocal(pid) as adaptador:
        with pytest.raises(PermissionError):
            adaptador.escrever(endereco + 8, b"\x01\x00\x00\x00")
        adaptador.habilitar_escrita()
        escritos = checks.escrever_valor(adaptador, endereco + 8, "int32", 999)
        assert escritos == 4
        assert checks.ler_valor(adaptador, endereco + 8, "int32") == 999


def test_check_processo_passa_em_alvo_real(alvo):
    pid, _, _ = alvo
    with ProcessoLocal(pid) as adaptador:
        resultado = checks.check_processo(adaptador)
        assert resultado.status == checks.PASS
        assert "modulos=" in resultado.medida


def test_check_processo_falha_com_modulo_ausente(alvo):
    pid, _, _ = alvo
    with ProcessoLocal(pid) as adaptador:
        resultado = checks.check_processo(adaptador, "libnaoexiste.so")
        assert resultado.status == checks.FAIL


def test_check_campo_detecta_mudanca_por_acao(alvo):
    pid, endereco, _ = alvo
    with ProcessoLocal(pid) as adaptador:
        antes = checks.ler_valor(adaptador, endereco, "int32")
        time.sleep(0.7)
        depois = checks.ler_valor(adaptador, endereco, "int32")
        assert (antes, depois) == (111, 777)
        resultado = checks.check_campo(antes=antes, depois=depois)
        assert resultado.status == checks.PASS
        assert "delta=+666" in resultado.medida


def test_check_campo_estavel_fica_indeterminado(alvo):
    pid, endereco, _ = alvo
    with ProcessoLocal(pid) as adaptador:
        resultado = checks.check_campo(adaptador, endereco + 4, "int32", amostras=3, intervalo=0.05)
        assert resultado.status == checks.INDETERMINADO
        assert "estável" in resultado.detalhe


def test_varredura_encontra_assinatura_no_processo(alvo):
    pid, _, endereco_assinatura = alvo
    padrao = checks.parse_padrao("50 52 55 4D 4F 2D 61 73 73 69 6E 61")
    with ProcessoLocal(pid) as adaptador:
        achados = adaptador.varrer(padrao, limite_regiao=64 * 1024 * 1024)
    assert achados, "assinatura não encontrada na memória do filho"
    assert endereco_assinatura in achados, "o endereço conhecido do buffer não apareceu na varredura"
    # O literal também existe no código-fonte carregado em memória: é exatamente por isso
    # que o check de assinatura exige unicidade em vez de aceitar o primeiro hit.
    assert len(achados) > 1


def test_check_entidades_valida_posicoes():
    ok = checks.check_entidades([(1.0, 2.0, 3.0), (4.0, 5.0, 6.0)])
    assert ok.status == checks.PASS
    iguais = checks.check_entidades([(1.0, 1.0, 1.0), (1.0, 1.0, 1.0)])
    assert iguais.status == checks.FAIL
    nan = checks.check_entidades([(1.0, float("nan"), 3.0), (4.0, 5.0, 6.0)])
    assert nan.status == checks.FAIL


def test_sem_adaptador_os_checks_vivos_sao_indeterminados():
    for check_id in ("processo", "campo", "entidades"):
        assert checks.executar(check_id).status == checks.INDETERMINADO
