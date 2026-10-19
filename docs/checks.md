<!-- GERADO por `prumo docs`. Não edite à mão: edite src/prumo/data/ e rode `prumo docs`. -->

# Os 7 checks

| check | pergunta | implementação | requer |
|---|---|---|---|
| `processo` | O processo alvo está aberto, com a arquitetura correta e o módulo base identificado? | processo-vivo | adaptador de processo (Cheat Engine bridge ou Frida MCP) ou execução local com permissão |
| `estrutura` | O tipo/classe que eu escolhi existe e tem forma plausível para o que eu procuro? | estatica | assembly .NET (mapa de tipos) ou lista de tipos da engine |
| `campo` | Este campo é mesmo a vida/posição que eu procuro? | processo-vivo | execução de uma ação no jogo (tomar dano, mover) e leitura antes/depois |
| `entidades` | A lista que eu encontrei contém entidades reais do mundo? | processo-vivo | leitura da cadeia de contêiner + permissão de leitura no processo |
| `projecao` | A matriz mundo->tela projeta um ponto conhecido no lugar certo? | estatica | matriz 4x4 de view-projection, ponto de mundo e tamanho da tela |
| `assinatura` | A assinatura (AOB) é única e tem bytes fixos suficientes para sobreviver a um patch? | estatica | padrão com curingas + buffer ou região de memória |
| `ac` | Qual anti-cheat está no caminho e o que ele detecta? | conhecimento | motor + AC + modo de jogo (o diagnóstico já cruza isso) |

## `processo`

**Pergunta:** O processo alvo está aberto, com a arquitetura correta e o módulo base identificado?

**Por que importa:** Todo o resto depende de estar no processo certo: módulo errado invalida qualquer endereço.

**Requer:** adaptador de processo (Cheat Engine bridge ou Frida MCP) ou execução local com permissão

## `estrutura`

**Pergunta:** O tipo/classe que eu escolhi existe e tem forma plausível para o que eu procuro?

**Por que importa:** Nome parecido não é prova: contagem de campos e tipos plausíveis separam candidato de coincidência.

**Requer:** assembly .NET (mapa de tipos) ou lista de tipos da engine

## `campo`

**Pergunta:** Este campo é mesmo a vida/posição que eu procuro?

**Por que importa:** É a única prova aceitável: o valor tem de mudar com a ação, na direção e na magnitude esperadas.

**Requer:** execução de uma ação no jogo (tomar dano, mover) e leitura antes/depois

## `entidades`

**Pergunta:** A lista que eu encontrei contém entidades reais do mundo?

**Por que importa:** Contagem > 1 e posições distintas separam uma lista de verdade de um array qualquer.

**Requer:** leitura da cadeia de contêiner + permissão de leitura no processo

## `projecao`

**Pergunta:** A matriz mundo->tela projeta um ponto conhecido no lugar certo?

**Por que importa:** Sem essa checagem, caixas aparecem deslocadas e o erro é atribuído ao código errado.

**Requer:** matriz 4x4 de view-projection, ponto de mundo e tamanho da tela

## `assinatura`

**Pergunta:** A assinatura (AOB) é única e tem bytes fixos suficientes para sobreviver a um patch?

**Por que importa:** Assinatura com múltiplos hits ou poucos bytes fixos quebra no próximo patch.

**Requer:** padrão com curingas + buffer ou região de memória

## `ac`

**Pergunta:** Qual anti-cheat está no caminho e o que ele detecta?

**Por que importa:** Escolher o alvo errado queima conta: a matriz de AC define o risco antes do primeiro passo.

**Requer:** motor + AC + modo de jogo (o diagnóstico já cruza isso)
