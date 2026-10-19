# prumo

> **O prumo do agente.** Diagnóstico, playbooks e verificação para engenharia reversa de jogos com agentes de IA.

[![CI](https://github.com/overlord111111/prumo/actions/workflows/ci.yml/badge.svg)](https://github.com/overlord111111/prumo/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

---

## O problema, em três linhas

O agente de IA hoje escreve código de cheat de olho fechado: chuta o offset, inventa o nome da classe, não
sabe se o que achou é a vida ou o contador de munição. Ele tem acesso a ferramenta de sobra — **o que ele não
tem é critério**.

Na construção civil, a parede pode parecer reta. É o **prumo** — o fio com peso — que diz se ela está. Este
projeto é isso para o trabalho do agente: **o fio que mede se o passo está reto antes de construir em cima**.

## O que o prumo é — e o que ele NÃO é

| é | não é |
|---|---|
| **diagnóstico**: qual caminho faz sentido para motor + anti-cheat + modo de jogo | não é cheat pronto de jogo específico |
| **playbooks**: o método por engine (Unity Mono/IL2CPP, Unreal, Source 2) e por AC (BattlEye, EAC, VAC, Vanguard) | não é lista de offsets que envelhece em uma semana |
| **verificação**: 7 checks com `PASS`/`FAIL`/`INDETERMINADO` e o número medido | não é "confia, funciona" |
| **dossiê de tipos**: um assembly .NET vira um mapa ranqueado pelo alvo, cortado por orçamento de token | não é despejo de 10 mil classes no contexto do agente |

**As mãos já existem e são boas** — `cheatengine-mcp-bridge` (~1,5 mil estrelas), `frida-game-hacking-mcp`,
`re-mcp` (Cheat Engine + x64dbg + Ghidra) e `rea`. O prumo **não reescreve** nenhuma delas: ele entrega o
cérebro e o juiz que faltam, e roda em cima do que você já tem.

## Instalação

```bash
pipx install git+https://github.com/overlord111111/prumo   # CLI
pip install "prumo[map]"                                    # + leitor de assemblies .NET
```

Requer Python 3.11+. Sem telemetria, sem conta, sem nuvem.

## Demo em 3 minutos

**1. Qual é o plano para este jogo?** (não toca em nada, só decide)

```bash
prumo diagnostico --motor unity-mono --ac battleye --modo online
```

```
# Plano — Unity (backend Mono) · BattlEye · servidor público / oficial

**Risco:** `alto`
- modo: servidor público / oficial — ban é permanente e pode alcançar o hardware (HWID); a conta é sua
- anti-cheat: BattlEye — camadas ativas: usuario, kernel, servidor

## Alertas
- ⚠️ BattlEye em servidor público significa corrida de detecção: nada aqui fica 'pronto', e ban é
  permanente (pode incluir HWID).

## Alternativas mais seguras
- reproduzir o mesmo estudo em single-player/LAN do mesmo motor
```

**2. O assembly do jogo vira um mapa, ranqueado pelo que você procura**

```bash
prumo map /caminho/Assembly-CSharp.dll --alvo health --orcamento 3000
```

Saída real (medida num jogo aberto, 957 classes, 3.658 campos — ver `examples/mapa-openra-health.md`):

| # | classe | campos | casados com o alvo |
|---|---|---|---|
| 1 | `OpenRA.Actor` | 35 | health:OpenRA.Traits.IHealth |
| 2 | `OpenRA.Traits.FrozenActor` | 30 | health:OpenRA.Traits.IHealth |

**3. Antes de acreditar, mede**

```bash
prumo verificar --check assinatura --padrao "48 8B 05 ?? ?? 33 44 66 77" --buffer-arquivo dump.bin
prumo verificar --check projecao --matriz "$(cat matriz.txt)" --ponto 10,0,5 --tela 1920x1080 --esperado 960,540
```

```
✔ PASS    assinatura    hits=1 fixos=10B total=12B — única em 0x1F4A0 com 10 bytes fixos
✘ FAIL    assinatura    hits=3 fixos=10B total=12B — assinatura não é única: 3 hits
? INDETERMINADO  campo  sem medição — precisa de processo vivo e não há adaptador conectado nesta execução.
```

O `INDETERMINADO` é deliberado: **o prumo prefere dizer "não sei" a inventar um PASS.**

## Os 7 checks

| check | pergunta | como mede |
|---|---|---|
| `processo` | o alvo certo está aberto, com a arquitetura certa? | PID, módulo base, bitness |
| `estrutura` | essa classe existe e tem forma plausível? | mapa de tipos: nome, campos, tipos |
| `campo` | esse campo é mesmo a vida? | **prova por ação**: toma dano e o valor muda |
| `entidades` | a lista tem entidades de verdade? | contagem > 1, posições distintas |
| `projecao` | o mundo→tela acerta o pixel? | erro medido contra ponto conhecido (< 2%) |
| `assinatura` | a AOB sobrevive ao próximo patch? | unicidade + nº de bytes fixos |
| `ac` | qual anti-cheat está no caminho? | matriz motor × AC × modo |

Detalhe de cada um: [`docs/checks.md`](docs/checks.md) (gerado dos dados).

## Cobertura hoje

| motor | leitura | passos |
|---|---|---|
| Unity (Mono) | `Assembly-CSharp.dll` — metadados legíveis | 7 |
| Unity (IL2CPP) | `global-metadata.dat` + `GameAssembly.dll` | 5 |
| Unreal | GObjects/GNames, UWorld | 5 |
| Source 2 | schema do jogo + lista de entidades | 3 |

Anti-cheat documentado: **BattlEye · EAC · VAC · Vanguard · nenhum** — com a escada de bypass, o custo em dias
e o risco de cada degrau.

| anti-cheat | camadas | degraus na escada |
|---|---|---|
| BattlEye | usuário, kernel, servidor | 5 |
| Easy Anti-Cheat | usuário, kernel, servidor | 4 |
| Valve Anti-Cheat | usuário, servidor, política | 3 |
| Riot Vanguard | usuário, kernel, servidor, hardware | 3 |
| Sem anti-cheat | — | 1 |

## Como o prumo se encaixa no que você já usa

```
        prumo  (diagnóstico · playbooks · verificação · dossiê de tipos)   ← este projeto
          │
          ├── cheatengine-mcp-bridge   (memória, AOB, disasm, breakpoints)
          ├── frida-game-hacking-mcp   (cross-platform: Linux/Android)
          ├── re-mcp                   (CE + x64dbg + Ghidra num servidor só)
          └── rea                      (investigação de binário com o agente)
```

O prumo não substitui nenhum deles. Ele decide **o que fazer**, diz **como saber se deu certo** e entrega
**contexto cirúrgico** em vez de despejar o binário inteiro no agente.

## Metodologia: medir, não opinar

- **Varredura ancorada**: assinatura com curinga ancorada no maior trecho fixo. Medido em 268 MB reais:
  `bytes.find` exato **2.690 MB/s**, ancorada **1.525 MB/s**, regex **69 MB/s** (2 GB: 0,8 s · 1,3 s · 30 s).
  Por isso não há regex no caminho crítico.
- **Dados → documentação**: `docs/matriz-ac.md`, `docs/motores.md` e `docs/checks.md` são **gerados** do
  `src/prumo/data/`. A CI falha se alguém editar um sem o outro: documento e playbook não podem divergir.
- **Teste do próprio instrumento**: 34 testes, incluindo o decodificador ECMA-335 e a matemática de projeção.
  Integração com assembly real roda quando `PRUMO_TEST_DLL` aponta para um binário.

## Como contribuir

Contribuição mais valiosa: **playbook de motor ou de AC** (um arquivo JSON em `src/prumo/data/`), com exemplo
verificável. Regras e checklist em [`CONTRIBUTING.md`](CONTRIBUTING.md).

O que **não** entra, por decisão de projeto: offset de jogo vivo, binário de bypass de anti-cheat, qualquer
coisa que automatize dano a terceiro.

## Aviso

Ferramenta de pesquisa em segurança de software e engenharia reversa. Viola Termos de Serviço de jogos, pode
resultar em banimento permanente e é de responsabilidade exclusiva de quem usa. Não use em servidor onde isso
prejudica outras pessoas. Ver [`LICENSE`](LICENSE).

## Licença

MIT © Over ([@overlord111111](https://github.com/overlord111111)).

---

## English summary

**prumo** is the missing *judgement layer* for AI agents doing game reverse engineering: a diagnostic that
decides the path for a given engine + anti-cheat + play mode, playbooks that encode the method per engine and
per AC, and seven verifiable checks that return `PASS` / `FAIL` / `INDETERMINATE` with the measured number.
It does not ship cheats, offsets or AC bypasses — it plugs into existing MCP tools (`cheatengine-mcp-bridge`,
`frida-game-hacking-mcp`, `re-mcp`, `rea`) and adds the brain and the verdict. Docs are generated from data,
so playbook and documentation cannot drift. MIT.
