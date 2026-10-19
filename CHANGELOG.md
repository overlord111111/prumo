# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versionamento semântico.

## [0.3.0] — 2026-10-19

Adaptador nativo de Windows e autoteste do instrumento.

### Adicionado

- **`prumo/adapters/windows.py`**: processo via ctypes (`OpenProcess`, `ReadProcessMemory`,
  `WriteProcessMemory`, `VirtualQueryEx`, `CreateToolhelp32Snapshot`), sem compilar e sem driver. Escrita
  opt-in, com reabertura do handle apenas quando necessário.
- **`prumo autoteste`**: exercita as seis capacidades contra o próprio processo — abrir, ler, escrever,
  observar mudança, varrer assinatura e recusar escrita sem permissão — e devolve `PASS`/`FALHOU` por linha.
- Lógica compartilhada entre adaptadores (`adapters/comum.py`): agrupamento de regiões em módulos e regra
  de região varável, testadas isoladamente.
- Seleção automática de adaptador por plataforma (`local` em Linux, `windows` em Windows).

### Alterado

- `abrir()` passa a escolher o adaptador da plataforma; a mensagem de extra do comando `map` aponta para o
  repositório (o nome `prumo` no PyPI pertence a outro projeto).
- Cinco testes novos (49 no total), incluindo o autoteste completo e a importação do módulo Windows fora
  do Windows.
- `python -m prumo` funcionar sem depender do script no PATH.

### Verificado

- `prumo autoteste` em **Windows 11, Python 3.14.4**: 6/6 `PASS` (41 módulos; leitura, escrita, mudança,
  varredura e recusa de escrita). Saída em `examples/autoteste-windows.txt`.
- `prumo autoteste` em **Linux 6.8**: 6/6 `PASS` em 0,17 s.

## [0.2.0] — 2026-10-19

Fecha o fluxo de processo vivo: os três checks que antes existiam como interface agora medem.

### Adicionado

- **Adaptadores** (`prumo/adapters`): contrato (`Adaptador`, `Modulo`, `Regiao`) e implementação de
  referência para Linux (`ProcessoLocal`), sobre `/proc/<pid>/maps` e `/proc/<pid>/mem`.
- **Checks vivos**: `processo` (pid, arquitetura lida do ELF, módulos, base), `campo` (observação de N
  amostras ou testemunho antes/depois) e `entidades` (contagem, posições distintas, NaN/inf).
- **CLI**: `prumo processo`, `prumo ler`, `prumo escrever` (exige `--confirmar`) e `prumo varrer`.
- Leitura e escrita tipadas: `int8/uint8/int16/uint16/int32/uint32/int64/uint64/float/double`.
- `examples/fluxo-completo-linux.py`: demonstração reprodutível de ponta a ponta, sem jogo e sem Cheat
  Engine. Sobe um processo filho, lê antes e depois da mudança, verifica o campo e varre a assinatura.
- Dez testes novos com processo real: leitura, escrita, mudança de valor, varredura e recusa de escrita.

### Alterado

- README reescrito com foco em uso e limites, mantendo a evidência numérica de cada afirmação.
- `docs/adaptadores.md` documenta as duas restrições de sistema (ptrace e processo protegido) e o protocolo
  externo em JSON.
- Varredura passa a considerar regiões anônimas e heap (antes só módulos mapeados em disco).

## [0.1.0] — 2026-10-19

Primeira versão: diagnóstico, playbooks, mapa de tipos e os sete checks.

### Adicionado

- `prumo diagnostico` — cruza motor × anti-cheat × modo de jogo e devolve plano com risco, alertas,
  alternativas e os checks exigidos em cada passo (4 motores, 5 anti-cheats).
- `prumo map` — leitor ECMA-335 que transforma um assembly .NET em dossiê de tipos ranqueado pelo alvo e
  cortado por orçamento de token. Provado num jogo real de código aberto: 957 classes, 3.658 campos,
  `OpenRA.Actor` no topo para o alvo `health`.
- `prumo verificar` — os sete checks, com `PASS`/`FAIL`/`INDETERMINADO`. De ponta a ponta desde o início:
  `estrutura`, `assinatura` (varredura ancorada), `projecao` (mundo→tela).
- `prumo docs` e `prumo dados` — documentação derivada dos dados e validação dos arquivos.
- Playbooks: Unity Mono, Unity IL2CPP, Unreal, Source 2.
- Matriz de anti-cheat: BattlEye, EAC, VAC, Vanguard, nenhum — com escada, custo em dias, risco e detecção.
- `AGENTS.md` com o contrato de uso por agentes; `CONTRIBUTING` e `SECURITY`.
- 34 testes (checks, diagnóstico, dados, documentação, decodificador .NET) e teste de integração opcional.
- CI: `ruff` + `pytest` + `prumo dados` + `prumo docs --check`.

### Medições registradas

- Varredura de assinatura com curinga: `bytes.find` 2.690 MB/s · **ancorada 1.525 MB/s** · regex 69 MB/s.
- Mapa de tipos (OpenRA.Game.dll, MIT): 957 classes, 3.658 campos, 1,4 s.
