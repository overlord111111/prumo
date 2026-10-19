# prumo

[![CI](https://github.com/overlord111111/prumo/actions/workflows/ci.yml/badge.svg)](https://github.com/overlord111111/prumo/actions/workflows/ci.yml)
[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

Ferramenta de linha de comando para quem faz engenharia reversa de jogos com agente de IA.
O prumo não dá acesso ao jogo — isso as ferramentas de memória já fazem. Ele dá **critério**:
decide o caminho antes de começar, executa os passos de leitura e **verifica** se o que o
agente encontrou é o que ele diz que é.

O nome é o instrumento: uma parede pode parecer reta, e é o fio de prumo que diz se está.

```
$ prumo diagnostico --motor unity-mono --ac battleye --modo online

# Plano — Unity (backend Mono) · BattlEye · servidor público / oficial

**Risco:** `alto`
- modo: servidor público / oficial — ban é permanente e pode alcançar o hardware (HWID); a conta é sua
- anti-cheat: BattlEye — camadas ativas: usuario, kernel, servidor

## Alertas
- BattlEye em servidor público significa corrida de detecção: nada aqui fica 'pronto', e ban é
  permanente (pode incluir HWID).

## Alternativas mais seguras
- reproduzir o mesmo estudo em single-player/LAN do mesmo motor
```

## Por que existe

Um agente com ferramenta de memória na mão escreve código de cheat de olho fechado: chuta o offset,
inventa o nome da classe e não sabe se o endereço que encontrou é a vida ou o contador de munição. O
resultado é hora perdida e conclusão errada com aparência de certa.

O prumo ataca a parte que falta, em três frentes:

1. **Diagnóstico** — cruza motor da engine, anti-cheat e modo de jogo e devolve o plano com o risco de
   cada degrau. Serve para não descobrir o custo depois de perder a conta.
2. **Playbooks** — o método por engine e por anti-cheat, guardado como dado versionado (não como texto
   solto): passo, verificação exigida e limitação declarada.
3. **Verificação** — sete checagens que devolvem `PASS`, `FAIL` ou `INDETERMINADO` com o número medido.
   Nenhum passo do plano avança sem o anterior em `PASS`.

## Instalação

O pacote **não** está publicado no PyPI (o nome `prumo` lá pertence a outro projeto). Instale do
repositório:

```bash
pipx install "git+https://github.com/overlord111111/prumo"

# com o leitor de assembly .NET (comando `map`):
pipx install "git+https://github.com/overlord111111/prumo"
pipx inject prumo dnfile
# ou, em um virtualenv:
pip install "prumo[map] @ git+https://github.com/overlord111111/prumo"
```

Requisitos: Python 3.11+, sem dependência obrigatória, sem conta, sem telemetria. O adaptador de processo
vivo é Linux (`/proc`); em Windows funcionam o diagnóstico, o mapa de tipos e os checks estáticos.

## Uso

**Diagnóstico** — não toca no alvo:

```bash
prumo diagnostico --motor unity-mono --ac nenhum --modo single
prumo diagnostico --motor unreal --ac eac --modo online --formato json
```

**Mapa de tipos** (requer o extra `dnfile`) — assembly .NET vira dossiê ranqueado pelo termo procurado,
cortado por orçamento de token (o agente recebe o essencial, não dez mil classes):

```bash
prumo map "…/Unturned_Data/Managed/Assembly-CSharp.dll" --alvo health --orcamento 3000
```

Saída medida num jogo de código aberto (OpenRA, MIT — 957 classes, 3.658 campos, 1,4 s):

| # | classe | campos | casados com o alvo |
|---|---|---|---|
| 1 | `OpenRA.Actor` | 35 | health:OpenRA.Traits.IHealth |
| 2 | `OpenRA.Traits.FrozenActor` | 30 | health:OpenRA.Traits.IHealth |

**Processo vivo** — adaptador próprio, sem Cheat Engine e sem Frida. Linux usa `/proc`; Windows usa
`OpenProcess` / `ReadProcessMemory` / `VirtualQueryEx` em ctypes, sem compilar nada:

```bash
prumo autoteste                                   # prova o adaptador nesta máquina
prumo processo --pid 1234 --modulo libc.so.6      # pid, arquitetura, módulos, check de processo
prumo ler      --pid 1234 --endereco 0x7f8a...    --tipo int32
prumo varrer   --pid 1234 --padrao "48 8B 05 ?? ?? 33 44 66 77" --max 5
prumo escrever --pid 1234 --endereco 0x7f8a...    --tipo int32 --valor 999 --confirmar
```

```
$ prumo autoteste
prumo autoteste · plataforma=Linux 6.8.0 · python=3.14.7
adaptadores disponíveis: local

PASS    processo   pid=83822 arch=x86_64 modulos=11 — PASS
PASS    leitura    int32 em 0x78D79E5274A0 = 11
PASS    escrita    4 byte(s) escritos, lido de volta = 999
PASS    mudanca    22 -> 29 (delta +7)
PASS    varredura  3 hit(s); buffer conhecido encontrado
PASS    higiene    recusou escrita sem habilitar_escrita()

RESULTADO: tudo funcionando
```

**Verificação** — cada check devolve veredito com o número:

```bash
prumo verificar --check campo      --antes 111 --depois 777
prumo verificar --check projecao   --matriz "$(cat matriz.txt)" --ponto 10,0,5 --tela 1920x1080 --esperado 960,540
prumo verificar --check assinatura --padrao "48 8B 05 ?? ?? 33 44 66 77" --buffer-arquivo dump.bin
prumo verificar --lista
```

```
PASS           campo       antes=111.0 depois=777.0 delta=+666.000 — o valor mudou com a ação
FAIL           assinatura  hits=2 fixos=11B total=13B — assinatura não é única: 2 hits
INDETERMINADO  projecao    sem medição — faltou --matriz, --ponto ou --tela.
```

## Os sete checks

| check | pergunta | implementação |
|---|---|---|
| `processo` | o alvo certo está aberto, com arquitetura e módulos esperados? | adaptador |
| `estrutura` | a classe existe e a forma dela é compatível com o alvo? | mapa de tipos |
| `campo` | o valor muda quando o jogo muda? | adaptador (observação) ou testemunho antes/depois |
| `entidades` | a lista tem entidades reais, com posições distintas? | dados extraídos |
| `projecao` | a matriz mundo→tela acerta um ponto conhecido? | cálculo |
| `assinatura` | a AOB é única e sobrevive ao próximo patch? | varredura |
| `ac` | qual anti-cheat está no caminho? | diagnóstico |

`INDETERMINADO` é estado de primeira classe: o instrumento prefere dizer que não sabe a devolver `PASS`
sem medição. Detalhe de cada check em [docs/checks.md](docs/checks.md), gerado dos dados.

## Cobertura

| motor | o que se lê | passos |
|---|---|---|
| Unity (Mono) | `Assembly-CSharp.dll` — metadados legíveis | 7 |
| Unity (IL2CPP) | `global-metadata.dat` + `GameAssembly.dll` | 5 |
| Unreal | GObjects/GNames, UWorld | 5 |
| Source 2 | schema do jogo + lista de entidades | 3 |

Anti-cheat documentado com escada de bypass, custo em dias, risco e detecção: BattlEye, Easy Anti-Cheat,
Valve Anti-Cheat, Riot Vanguard e "sem anti-cheat". Íntegra em [docs/matriz-ac.md](docs/matriz-ac.md).

## Integração com as ferramentas que você já usa

O prumo não reimplementa memória, AOB ou disassembler. Ele conversa com quem já faz isso:
`cheatengine-mcp-bridge` (Windows, cerca de 180 ferramentas), `frida-game-hacking-mcp`
(Linux/Android/Windows), `re-mcp` (Cheat Engine + x64dbg + Ghidra) e `rea` (investigação de binário).
O contrato de adaptador e como plugar cada um estão em [docs/adaptadores.md](docs/adaptadores.md).

## Qualidade e limites

Medido, não estimado:

- varredura de assinatura com curinga: **1.525 MB/s** ancorada no maior trecho fixo, contra 69 MB/s do
  regex equivalente (bloco real de 268 MB). Projeção para 2 GB: 1,3 s contra 30 s;
- fluxo completo em processo real — leitura tipada, escrita, detecção de mudança e varredura —
  reproduzível com `python examples/fluxo-completo-linux.py`;
- `prumo autoteste` executado em duas plataformas: **Linux 6.8** (6/6, 0,17 s) e **Windows 11 com Python 3.14**
  (6/6, 41 módulos) — saídas em `examples/autoteste-windows.txt`;
- 49 testes, incluindo adaptador com processo filho real, decodificador ECMA-335 e matemática de projeção;
- documentação derivada dos dados: `prumo docs --check` falha se playbook e documento divergirem.

Limites declarados:

- o adaptador é nativo em Linux (`/proc`) e em Windows (`OpenProcess`/`ReadProcessMemory`). Em Windows com
  anti-cheat de kernel, `OpenProcess` é recusado — e o erro diz isso em vez de fingir sucesso;
- playbook é método, não mágica: jogo com símbolos ofuscados exige mais disassembler e menos nome;
- passar nos checks significa "não caiu nestas verificações", não "é indetectável". Anti-cheat é corrida
  de detecção, não estado.

## Contribuir

A contribuição mais útil é playbook: um arquivo JSON em `src/prumo/data/` com passo, check e limitação.
Regras e checklist em [CONTRIBUTING.md](CONTRIBUTING.md). Não entram: offset de jogo vivo, binário de
bypass de anti-cheat e qualquer coisa que automatize dano a terceiro.

## Aviso

Ferramenta de pesquisa em segurança de software e engenharia reversa. O uso pode violar Termos de Serviço
de jogos e resultar em banimento permanente; a responsabilidade é de quem usa. Não use em servidor onde
isso prejudica outras pessoas. Ver [LICENSE](LICENSE).

MIT © Over — [@overlord111111](https://github.com/overlord111111).

---

**English summary.** `prumo` is the judgement layer for AI agents doing game reverse engineering: a
diagnostic (engine × anti-cheat × play mode), method playbooks stored as versioned data, and seven checks
that return `PASS` / `FAIL` / `INDETERMINATE` with the measured number. It ships a Linux process adapter as
reference and plugs into existing MCP tools for memory access; it does not ship game offsets or
anti-cheat bypasses. Documentation is generated from the same data the CLI reads, so the two cannot drift.
