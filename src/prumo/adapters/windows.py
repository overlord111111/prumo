"""Adaptador de processo para Windows, em ctypes puro (sem compilar nada).

Usa a API de processo do Windows diretamente: `OpenProcess`, `ReadProcessMemory`,
`WriteProcessMemory`, `VirtualQueryEx` e a lista de módulos por snapshot. O objetivo é
o mesmo do adaptador Linux — deixar o agente medir, não adivinhar — em ambiente onde
Cheat Engine e Frida podem nem estar instalados.

Limite conhecido e importante: processo protegido por anti-cheat de kernel recusa
`OpenProcess` com leitura. O adaptador devolve erro claro em vez de fingir sucesso.
"""

from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes
from dataclasses import dataclass

from .base import AdaptadorIndisponivel, FalhaDeLeitura, Modulo, Regiao
from .comum import juntar_regioes_em_modulos, varrervavel

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008

TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010

MEM_COMMIT = 0x1000
MEM_IMAGE = 0x1000000
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01

LEGIVEIS = {0x02, 0x04, 0x08, 0x20, 0x40, 0x80}
GRAVAVEIS = {0x04, 0x08, 0x40, 0x80}

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True) if os.name == "nt" else None


class MODULEENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("th32ModuleID", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("GlblcntUsage", wintypes.DWORD),
        ("ProccntUsage", wintypes.DWORD),
        ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
        ("modBaseSize", wintypes.DWORD),
        ("hModule", wintypes.HMODULE),
        ("szModule", wintypes.WCHAR * 256),
        ("szExePath", wintypes.WCHAR * 260),
    ]


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]


if kernel32 is not None:
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.ReadProcessMemory.argtypes = [
        wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
    ]
    kernel32.ReadProcessMemory.restype = wintypes.BOOL
    kernel32.WriteProcessMemory.argtypes = [
        wintypes.HANDLE, wintypes.LPVOID, wintypes.LPCVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
    ]
    kernel32.WriteProcessMemory.restype = wintypes.BOOL
    kernel32.VirtualQueryEx.argtypes = [
        wintypes.HANDLE, wintypes.LPCVOID, ctypes.POINTER(MEMORY_BASIC_INFORMATION), ctypes.c_size_t
    ]
    kernel32.VirtualQueryEx.restype = ctypes.c_size_t
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Module32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MODULEENTRY32W)]
    kernel32.Module32FirstW.restype = wintypes.BOOL
    kernel32.Module32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MODULEENTRY32W)]
    kernel32.Module32NextW.restype = wintypes.BOOL
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.IsWow64Process.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
    kernel32.IsWow64Process.restype = wintypes.BOOL

INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value


@dataclass
class _Camada:
    """Isola as chamadas de sistema para permitir teste da lógica sem Windows real."""

    handle: int

    def le(self, endereco: int, tamanho: int) -> bytes:
        buffer = ctypes.create_string_buffer(tamanho)
        lido = ctypes.c_size_t(0)
        ok = kernel32.ReadProcessMemory(
            self.handle, ctypes.c_void_p(endereco), buffer, tamanho, ctypes.byref(lido)
        )
        if not ok:
            erro = ctypes.get_last_error()
            raise FalhaDeLeitura(f"ReadProcessMemory falhou em 0x{endereco:X} (erro {erro})")
        return buffer.raw[: lido.value]

    def escreve(self, endereco: int, dados: bytes) -> int:
        escrito = ctypes.c_size_t(0)
        ok = kernel32.WriteProcessMemory(
            self.handle, ctypes.c_void_p(endereco), dados, len(dados), ctypes.byref(escrito)
        )
        if not ok:
            erro = ctypes.get_last_error()
            raise FalhaDeLeitura(f"WriteProcessMemory falhou em 0x{endereco:X} (erro {erro})")
        return escrito.value





class ProcessoWindows:
    """Adaptador de referência em Windows."""

    nome = "windows"

    def __init__(self, pid: int) -> None:
        if os.name != "nt":
            raise AdaptadorIndisponivel("o adaptador windows exige Windows")
        if pid <= 0:
            raise ValueError(f"pid inválido: {pid}")
        self.pid = pid
        self._somente_leitura = True
        self._camada: _Camada | None = None
        self._regioes: list[Regiao] | None = None

    # ------------------------------------------------------------------ ciclo de vida

    def __enter__(self) -> ProcessoWindows:
        return self

    def __exit__(self, *_excecao: object) -> None:
        self.fechar()

    def fechar(self) -> None:
        if self._camada is not None:
            kernel32.CloseHandle(self._camada.handle)
            self._camada = None

    def _abrir(self) -> _Camada:
        if self._camada is not None:
            return self._camada
        direitos = PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ
        if not self._somente_leitura:
            direitos |= PROCESS_VM_WRITE | PROCESS_VM_OPERATION
        handle = kernel32.OpenProcess(direitos, False, self.pid)
        if not handle:
            erro = ctypes.get_last_error()
            raise AdaptadorIndisponivel(
                f"OpenProcess recusou o pid {self.pid} (erro {erro}). "
                "Processo inexistente, outro usuário, elevação necessária "
                "ou alvo protegido por anti-cheat."
            )
        self._camada = _Camada(handle)
        return self._camada

    # ------------------------------------------------------------------ consultas

    def processo(self) -> dict:
        camada = self._abrir()
        tamanho = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(tamanho.value)
        caminho = ""
        if kernel32.QueryFullProcessImageNameW(camada.handle, 0, buffer, ctypes.byref(tamanho)):
            caminho = buffer.value
        return {"pid": self.pid, "arquitetura": self.arquitetura(), "executavel": caminho or "desconhecido"}

    def arquitetura(self) -> str:
        camada = self._abrir()
        if sys.maxsize > 2**32:
            base = "x86_64"
        else:
            base = "i386"
        wow64 = wintypes.BOOL()
        if kernel32.IsWow64Process(camada.handle, ctypes.byref(wow64)) and wow64.value and base == "x86_64":
            return "i386"  # processo 32 bits rodando em Windows 64
        return base

    def regioes(self) -> list[Regiao]:
        if self._regioes is not None:
            return self._regioes
        camada = self._abrir()
        regioes: list[Regiao] = []
        endereco = 0
        informacao = MEMORY_BASIC_INFORMATION()
        tamanho_estrutura = ctypes.sizeof(MEMORY_BASIC_INFORMATION)
        while endereco < (1 << 47):  # espaço de usuário de 64 bits
            consultado = kernel32.VirtualQueryEx(
                camada.handle, ctypes.c_void_p(endereco), ctypes.byref(informacao), tamanho_estrutura
            )
            if not consultado:
                break
            base = informacao.BaseAddress or 0
            tamanho = informacao.RegionSize or 0
            if tamanho == 0:
                break
            if informacao.State == MEM_COMMIT and informacao.Protect not in (PAGE_NOACCESS, PAGE_GUARD):
                permissoes = ""
                permissoes += "r" if informacao.Protect in LEGIVEIS else "-"
                permissoes += "w" if informacao.Protect in GRAVAVEIS else "-"
                permissoes += "x" if informacao.Protect & 0x10 or informacao.Protect & 0x20 else "-"
                permissoes += "p"
                if informacao.Type == MEM_IMAGE:
                    caminho = f"image_0x{informacao.AllocationBase or base:X}"
                else:
                    caminho = ""
                regioes.append(
                    Regiao(inicio=base, fim=base + tamanho, permissoes=permissoes, caminho=caminho)
                )
            endereco = base + tamanho
        self._regioes = regioes
        return regioes

    def modulos(self) -> list[Modulo]:
        modulos = self._modulos_por_snapshot()
        if modulos:
            return modulos
        # Sem snapshot (cross-bitness ou restrição): agrupa regiões de imagem, sem nome de arquivo.
        return juntar_regioes_em_modulos(self.regioes())

    def _modulos_por_snapshot(self) -> list[Modulo]:
        snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, self.pid)
        if not snapshot or snapshot == INVALID_HANDLE_VALUE:
            return []
        try:
            entrada = MODULEENTRY32W()
            entrada.dwSize = ctypes.sizeof(MODULEENTRY32W)
            modulos: list[Modulo] = []
            if not kernel32.Module32FirstW(snapshot, ctypes.byref(entrada)):
                return []
            while True:
                base = ctypes.cast(entrada.modBaseAddr, ctypes.c_void_p).value or 0
                if base:
                    modulos.append(Modulo(entrada.szExePath or entrada.szModule, base, entrada.modBaseSize))
                if not kernel32.Module32NextW(snapshot, ctypes.byref(entrada)):
                    break
            return sorted(modulos, key=lambda m: m.base)
        finally:
            kernel32.CloseHandle(snapshot)

    def modulo(self, nome: str) -> Modulo | None:
        alvo = nome.lower()
        for modulo in self.modulos():
            if modulo.nome_modulo.lower() == alvo or modulo.nome.lower().endswith(alvo):
                return modulo
        return None

    def regiao_de(self, endereco: int) -> Regiao | None:
        for regiao in self.regioes():
            if regiao.inicio <= endereco < regiao.fim:
                return regiao
        return None

    # ------------------------------------------------------------------ leitura/escrita

    def ler(self, endereco: int, tamanho: int) -> bytes:
        if tamanho <= 0:
            raise ValueError("tamanho de leitura precisa ser positivo")
        return self._abrir().le(endereco, tamanho)

    def escrever(self, endereco: int, dados: bytes) -> int:
        if self._somente_leitura:
            raise PermissionError(
                "adaptador em modo somente leitura: escrever exige habilitar_escrita() de forma explícita"
            )
        return self._abrir().escreve(endereco, dados)

    def habilitar_escrita(self) -> None:
        self._somente_leitura = False
        self.fechar()  # reabre com os direitos de escrita
        self._abrir()

    # ------------------------------------------------------------------ utilidades

    def varrer(
        self,
        padrao: list[int | None],
        limite_regiao: int = 64 * 1024 * 1024,
        limite_total: int = 256 * 1024 * 1024,
    ) -> list[int]:
        from ..checks import _varrer_ancorada

        achados: list[int] = []
        lido_total = 0
        for regiao in self.regioes():
            if not varrervavel(regiao):
                continue
            if lido_total >= limite_total:
                break
            lido = 0
            while lido < regiao.tamanho and lido < limite_regiao:
                bloco = min(4 * 1024 * 1024, regiao.tamanho - lido)
                try:
                    dados = self.ler(regiao.inicio + lido, bloco)
                except FalhaDeLeitura:
                    break
                if not dados:
                    break
                for deslocamento in _varrer_ancorada(dados, padrao):
                    achados.append(regiao.inicio + lido + deslocamento)
                lido += bloco
                lido_total += bloco
        return achados
