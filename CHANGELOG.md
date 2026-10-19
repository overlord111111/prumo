# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versionamento semântico.

## [0.1.0] — 2026-10-19

Primeira versão pública. Entrega o **cérebro** e o **juiz**; as mãos continuam sendo as ferramentas de terceiros.

### Adicionado

- **`prumo diagnostico`** — cruza motor × anti-cheat × modo de jogo e devolve plano com risco, alertas,
  alternativas e os checks exigidos em cada passo. 4 motores × 5 anti-cheats.
- **`prumo map`** — leitor ECMA-335 que transforma um assembly .NET em dossiê de tipos **ranqueado pelo alvo**
  e cortado por orçamento de token. Provado num jogo real de código aberto: 957 classes, 3.658 campos,
  `OpenRA.Actor` no topo para o alvo `health`.
- **`prumo verificar`** — os 7 checks, com `PASS`/`FAIL`/`INDETERMINADO`. Implementados de ponta a ponta:
  `estrutura`, `assinatura` (varredura ancorada), `projecao` (mundo→tela). Os de processo vivo existem como
  interface e devolvem `INDETERMINADO` com o requisito explícito.
- **`prumo docs`** — geração e verificação da documentação derivada dos dados; `--check` falha se divergir.
- **`prumo dados`** — valida todos os JSON versionados.
- Playbooks: Unity Mono, Unity IL2CPP, Unreal, Source 2.
- Matriz de anti-cheat: BattlEye, EAC, VAC, Vanguard, nenhum — com escada, custo em dias, risco e detecção.
- `AGENTS.md` com o contrato de uso por agentes.
- 34 testes (checks, diagnóstico, dados, documentação, decodificador .NET) + teste de integração opcional.
- CI: `ruff` + `pytest` + `prumo dados` + `prumo docs --check`.

### Medições registradas

- Varredura de assinatura com curinga: `bytes.find` 2.690 MB/s · **ancorada 1.525 MB/s** · regex 69 MB/s.
- Mapa de tipos (OpenRA.Game.dll, MIT): 957 classes, 3.658 campos, 1,4 s.
