# Arquitetura

Três camadas, com fronteira explícita para não reescrever o que já existe bem feito.

```
┌────────────────────────────────────────────────────────────────────┐
│ CAMADA 3 — CÉREBRO E JUIZ (este projeto)                           │
│  diagnostico · playbooks (data/motores, data/ac) · 7 checks        │
│  dossiê de tipos (dotnet.py) · CLI                                 │
└───────────────────────────┬────────────────────────────────────────┘
                            │ MCP / stdio ou API local
┌───────────────────────────▼────────────────────────────────────────┐
│ CAMADA 2 — MÃOS (projetos de terceiros, plugados)                  │
│  cheatengine-mcp-bridge · frida-game-hacking-mcp · re-mcp · rea    │
└───────────────────────────┬────────────────────────────────────────┘
                            │ leitura/escrita de processo, disasm
┌───────────────────────────▼────────────────────────────────────────┐
│ CAMADA 1 — ALVO                                                     │
│  processo, assembly, metadata, binário                              │
└────────────────────────────────────────────────────────────────────┘
```

## Por que a camada 2 é de terceiros

Reimplementar memória/AOB/disasm significaria competir com `cheatengine-mcp-bridge` (~1,5 mil estrelas,
~180 ferramentas) sem entregar nada novo. O valor do prumo está em decidir, medir e reduzir contexto — e essas
três coisas ninguém entrega.

Código próprio na camada 2 só onde **não existe equivalente**:

- **`dotnet.py`** — leitor ECMA-335 que produz dossiê ranqueado e cortado por orçamento de token. Nenhuma
  ferramenta entrega o mapa de tipos *com ranking por alvo* para o agente.
- **varredura ancorada** — implementação de AOB com curinga usada nos checks, para funcionar sem depender de
  processo externo.

## Fluxo de uma sessão

```
1. prumo diagnostico --motor X --ac Y --modo Z
      → plano com risco, alertas, alternativas e os checks exigidos por passo

2. prumo map <assembly> --alvo health --orcamento 3000
      → candidatos ranqueados (classe, campo, tipo) dentro do orçamento

3. prumo verificar --check estrutura --mapa-arquivo mapa.json --classe Actor --alvo health
      → PASS/FAIL com o número

4. (com adaptador) checks de processo vivo: processo, campo, entidades
      → cada passo só avança com PASS
```

## Estrutura de arquivos

```
src/prumo/
├── cli.py            argparse + despacho
├── dados.py          carregamento e validação dos JSON
├── diagnostico.py    cruzamento motor × AC × modo → plano
├── checks.py         os 7 checks + varredura ancorada + projeção
├── dotnet.py         leitor ECMA-335 + ranqueamento + dossiê
├── docs.py           geração/verificação da documentação derivada
└── data/             FONTE DE VERDADE (motores, ACs, checks)
```

## Decisões de projeto

| decisão | motivo |
|---|---|
| dados em JSON dentro do pacote | validação com schema própria, sem dependência, e geração de docs |
| documentação gerada | playbook e doc não podem divergir; CI garante |
| `INDETERMINADO` como estado de primeira classe | honestidade do instrumento: não sei ≠ passou |
| dependência opcional só no `map` | `pip install prumo` funciona sem nada; `[map]` traz `dnfile` |
| sem telemetria, sem conta, sem nuvem | o dado é do usuário; a ferramenta não precisa saber de nada |
| nada de offset de jogo no repositório | evita DMCA e evita virar estoque de cheat pronto |
