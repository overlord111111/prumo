# Adaptadores (as "mãos")

O prumo decide e verifica. Para **agir** no processo, ele usa ferramentas de terceiros via MCP. Esta página
diz o que cada uma cobre e o que muda no fluxo.

## O que cada adaptador entrega

| adaptador | plataforma | entrega | quando usar |
|---|---|---|---|
| [`cheatengine-mcp-bridge`](https://github.com/miscusi-peek/cheatengine-mcp-bridge) | Windows | memória, AOB, ponteiro, breakpoint, disasm, RTTI | fluxo completo no Windows, com Cheat Engine aberto |
| [`frida-game-hacking-mcp`](https://github.com/0xhackerfren/frida-game-hacking-mcp) | Linux / Android / Windows | scan, AOB, read/write, hook, inject | quando não há Cheat Engine (Linux, Android, emulador) |
| [`re-mcp`](https://github.com/Travers9483/mcp-cheat-engine) | Windows | CE + x64dbg + Ghidra num servidor só | quando você quer disasm estático e debug dinâmico juntos |
| [`rea`](https://github.com/morluto/rea) | cross | investigação de binário guiada por skill | quando o alvo é binário fechado, não engine conhecida |

## O que o prumo espera de um adaptador

Para rodar os checks de processo vivo, o adaptador precisa responder a cinco perguntas:

| pergunta | usado por |
|---|---|
| qual é o PID e o módulo base do alvo? | `processo` |
| leia N bytes em `endereço` | `campo`, `entidades` |
| qual é a arquitetura (x86/x64)? | `processo` |
| liste os módulos carregados | `ac` |
| qual é o endereço de um símbolo/assinatura? | `campo`, `entidades` |

Se o adaptador não responde, o check devolve `INDETERMINADO` — nunca `PASS`.

## Fluxo com adaptador

```bash
# 1. prumo decide (sem tocar no alvo)
prumo diagnostico --motor unity-mono --ac nenhum --modo single

# 2. mapa de tipos (não precisa de processo)
prumo map "C:/.../Unturned_Data/Managed/Assembly-CSharp.dll" --alvo health --saida-json mapa.json
prumo verificar --check estrutura --mapa-arquivo mapa.json --classe Player --alvo life

# 3. com o MCP do adaptador conectado ao agente, os checks de processo vivo passam a ter dado:
#    processo → campo (prova por ação) → entidades → projecao → assinatura
```

## Ordem recomendada (aprendizado)

1. **single-player / servidor próprio sem AC** — aprende-se a engine, sem risco de conta.
2. **mesmo motor, servidor privado** — variação de layout, mapa de tipos atualizado.
3. **só depois** avaliar servidor com AC, relendo `docs/matriz-ac.md` e aceitando o risco com número.

## Segurança

- Rode o adaptador em máquina de teste/quando possível em VM.
- Antivírus vai sinalizar leitura de memória: exceção de pasta estreita é diferente de desligar proteção.
- Nenhum adaptador aqui é nosso; leia o código antes de rodar. A regra do projeto é: **fonte legível ou não
  roda**.
