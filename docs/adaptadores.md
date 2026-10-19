# Adaptadores

O prumo não abre processo no Windows nem injeta nada. Ele define um contrato e usa adaptadores. Há um
implementado no projeto (Linux, `/proc`) e um protocolo aberto para plugar o que você já usa.

## Contrato

Qualquer objeto que responda a estes cinco métodos serve como adaptador:

| método | devolve | usado por |
|---|---|---|
| `processo()` | `{"pid", "arquitetura", "executavel"}` | check `processo` |
| `modulos()` | lista de `Modulo(nome, base, tamanho)` | check `processo`, resolução de base |
| `regioes()` | lista de `Regiao(inicio, fim, permissoes, caminho)` | varredura, validação de endereço |
| `ler(endereco, tamanho)` | `bytes` (levanta `FalhaDeLeitura` se recusado) | checks `campo`, `entidades`, `varrer` |
| `escrever(endereco, dados)` | número de bytes escritos | só após `habilitar_escrita()` |

Implementação de referência: `src/prumo/adapters/local.py`, classe `ProcessoLocal`.

## Adaptador local (Linux)

Monta o mapa com `/proc/<pid>/maps` e acessa a memória por `/proc/<pid>/mem`, com `pread`/`pwrite` por
endereço — sem laço de bloco e sem buffer intermediário.

```python
from prumo.adapters import ProcessoLocal

with ProcessoLocal(pid) as alvo:
    print(alvo.processo())            # pid, arquitetura (lida do ELF), executável
    print(alvo.modulos()[:3])         # base e tamanho por módulo mapeado
    valor = alvo.ler(0x7F8A0000, 4)   # bytes crus
```

Duas restrições reais, ambas do sistema operacional e não do prumo:

1. **Permissão de leitura.** O kernel exige acesso por ptrace. Com `kernel.yama.ptrace_scope = 1` (padrão em
   muitas distribuições), apenas o processo-pai lê. Se outro processo precisa ler, o alvo libera com
   `prctl(PR_SET_PTRACER, PR_SET_PTRACER_ANY)` — é o que `examples/fluxo-completo-linux.py` faz em uma
   linha, e o motivo de a demonstração funcionar com a CLI.
2. **Processo protegido.** Alvo com anti-cheat de kernel não é acessível por este caminho, e não é a
   intenção do adaptador local. Para esse caso existe outro caminho, documentado na matriz de anti-cheat.

Escrita é opt-in: `ProcessoLocal` recusa `escrever` até receber `habilitar_escrita()`, e a CLI exige
`--confirmar`. É a única operação do projeto que altera o alvo.

## Ferramentas que já falam MCP

Cheat Engine, Frida, x64dbg e Ghidra já têm servidor MCP pronto. Nesse caso não há adaptador nosso no meio:
o agente usa as ferramentas delas para ler e escrever, e usa o prumo para decidir e verificar.

| ferramenta | plataforma | o que entrega |
|---|---|---|
| [`cheatengine-mcp-bridge`](https://github.com/miscusi-peek/cheatengine-mcp-bridge) | Windows | memória, AOB, ponteiro, breakpoint, disasm, RTTI |
| [`frida-game-hacking-mcp`](https://github.com/0xhackerfren/frida-game-hacking-mcp) | Linux / Android / Windows | scan, AOB, read/write, hook, inject |
| [`re-mcp`](https://github.com/Travers9483/mcp-cheat-engine) | Windows | Cheat Engine + x64dbg + Ghidra num servidor só |
| [`rea`](https://github.com/morluto/rea) | multiplataforma | investigação de binário guiada por skill |

O que o prumo precisa receber de qualquer uma delas é só o resultado:

```json
{
  "processo": {"pid": 4321, "arquitetura": "x86_64", "executavel": "C:/Games/x.exe"},
  "modulos": [{"nome": "x.exe", "base": "0x7FF6A1000000", "tamanho": 18223104}],
  "leituras": [{"endereco": "0x7FF6A1001000", "bytes": "0A000000"}]
}
```

Para um adaptador próprio (ponte em Python, cliente de named pipe, driver), implemente os cinco métodos e
registre em `prumo.adapters.abrir`. O contrato é pequeno de propósito: quem tem o driver não deveria
precisar entender o resto da ferramenta.

## Ordem recomendada

1. single-player ou servidor próprio sem anti-cheat — aprende a engine sem risco de conta;
2. mesmo motor, servidor privado — variação de layout, mapa de tipos atualizado;
3. servidor com anti-cheat — só depois de ler `docs/matriz-ac.md` e aceitar o custo com número na mão.

## Higiene

- Ferramenta de terceiro só entra com fonte legível. Binário ofuscado não roda.
- Antivírus vai sinalizar leitura de memória; o correto é exceção de pasta estreita, não desligar proteção.
- Prefira máquina de teste ou VM: o que você lê é memória de um processo que pode ser hostil.
