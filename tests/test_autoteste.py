"""Autoteste do adaptador e da lógica compartilhada."""

from __future__ import annotations

import os

import pytest

from prumo import autoteste
from prumo.adapters import juntar_regioes_em_modulos, varrervavel
from prumo.adapters.base import Regiao


def test_autoteste_passa_na_plataforma_atual():
    ok, linhas = autoteste.executar()
    relatorio = "\n".join(linhas)
    assert ok, relatorio
    for capacidade in ("processo", "leitura", "escrita", "mudanca", "varredura", "higiene"):
        assert f"PASS    {capacidade}" in relatorio, f"capacidade {capacidade} não reportada como PASS"


def test_autoteste_nao_explode_sem_adaptador(monkeypatch):
    monkeypatch.setattr(autoteste, "disponiveis", lambda: ())
    ok, linhas = autoteste.executar()
    assert not ok
    assert any("nenhum adaptador" in linha for linha in linhas)


def test_juntar_regioes_agrupa_por_arquivo():
    regioes = [
        Regiao(0x1000, 0x2000, "r--p", "/lib/a.so"),
        Regiao(0x2000, 0x3000, "rw-p", "/lib/a.so"),
        Regiao(0x5000, 0x6000, "r-xp", "/lib/b.so"),
        Regiao(0x7000, 0x8000, "rw-p", ""),
    ]
    modulos = juntar_regioes_em_modulos(regioes)
    assert len(modulos) == 2
    assert modulos[0].base == 0x1000 and modulos[0].tamanho == 0x2000
    assert modulos[1].nome_modulo == "b.so"


def test_varrervavel_descarta_regiao_de_sistema_e_gigante():
    assert varrervavel(Regiao(0x1000, 0x2000, "r--p", "/lib/a.so"))
    assert not varrervavel(Regiao(0x1000, 0x2000, "-w-p", "/lib/a.so"))
    assert not varrervavel(Regiao(0, 0, "r--p", "/lib/a.so"))
    assert not varrervavel(Regiao(0x1000, 0x2000, "r--p", "[vdso]"))


def test_adaptador_windows_e_importavel_fora_do_windows():
    """O módulo existe e importa em qualquer plataforma; só recusa operar fora do Windows."""
    from prumo.adapters.base import AdaptadorIndisponivel
    from prumo.adapters.windows import ProcessoWindows

    if os.name == "nt":  # pragma: no cover - coberto no Windows
        pytest.skip("no Windows o adaptador abre normalmente")
    with pytest.raises(AdaptadorIndisponivel):
        ProcessoWindows(1)
