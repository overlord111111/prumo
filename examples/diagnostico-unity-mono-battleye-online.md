# Plano — Unity (backend Mono) · BattlEye · servidor público / oficial

**Risco:** `alto`
- modo: servidor público / oficial — ban é permanente e pode alcançar o hardware (HWID); a conta é sua
- anti-cheat: BattlEye — camadas ativas: usuario, kernel, servidor

## Pré-requisitos
- acesso ao alvo: <jogo>_Data/Managed/Assembly-CSharp.dll
- via de leitura: metadata
- adaptador de processo instalado se o passo exigir leitura viva (ver docs/adaptadores.md)
- sandbox/VM recomendada para qualquer binário não verificado

## Passos (cada um exige o check em PASS antes do próximo)

| # | passo | checks obrigatórios | risco |
|---|---|---|---|
| M1 | Confirmar o backend (Mono ou IL2CPP) | processo | nenhum |
| M2 | Extrair o mapa de tipos e campos | estrutura | nenhum |
| M3 | Escolher a classe do objeto do mundo | estrutura | nenhum |
| M4 | Provar o campo por ação | campo | baixo |
| M5 | Enumerar a lista de entidades | campo, entidades | baixo |
| M6 | Projetar mundo para tela | projecao | baixo |
| M7 | Fixar a assinatura | assinatura | baixo |

### M1 — Confirmar o backend (Mono ou IL2CPP)
Procure a pasta Managed com Assembly-CSharp.dll. Se existir, é Mono. Se houver global-metadata.dat em <jogo>_Data/il2cpp_data/Metadata, é IL2CPP e este playbook não se aplica.

### M2 — Extrair o mapa de tipos e campos
Rode `prumo map Assembly-CSharp.dll --alvo <termo>` para obter as classes candidatas, com campos e tipos, dentro de um orçamento de tokens.

### M3 — Escolher a classe do objeto do mundo
A entidade do jogador costuma ser a classe que carrega posição (Vector3), vida/health e nome. Confirme pela contagem de campos e pelos métodos que a referenciam.

### M4 — Provar o campo por ação
Com o jogo rodando, tome dano/mova e observe o valor mudar exatamente como esperado. Sem essa prova, o campo é hipótese, não fato.

### M5 — Enumerar a lista de entidades
Com o endereço do objeto local e a estrutura confirmados, suba a hierarquia até o contêiner (manager/lista) e conte as entidades. Contagem > 1 e posições distintas = lista válida.

### M6 — Projetar mundo para tela
Obtenha a matriz de view-projection da câmera e valide com `prumo verificar projecao`: o ponto do próprio jogador tem de cair no centro da tela com erro < 2%.

### M7 — Fixar a assinatura
Gere uma assinatura AOB com >= 8 bytes fixos e confirme unicidade (`prumo verificar assinatura`). Assinatura com 1 hit sobrevive a patch; com vários, não.

## Alertas
- ⚠️ BattlEye em servidor público significa corrida de detecção: nada aqui fica 'pronto', e ban é permanente (pode incluir HWID).

## Não faz
- ⛔ usar o resultado deste plano em servidor com outros jogadores como teste

## Alternativas mais seguras
- reproduzir o mesmo estudo em single-player/LAN do mesmo motor

## Limitações deste motor
- Campo privado pode estar inlinado em struct; nem toda entidade tem nome de classe óbvio.
- Jogos com ofuscação (Cecil/ConfuserEx) reduzem a leitura a nomes genéricos: aí o caminho vira disasm, não metadata.
- Backend Mono não é garantia: checar M1 antes de tudo.
