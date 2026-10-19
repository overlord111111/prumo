---
title: Anti-cheat
---

<!-- GERADO por `prumo docs`. Não edite à mão: edite src/prumo/data/ e rode `prumo docs`. -->

# Matriz de anti-cheat

| anti-cheat | camadas | detecta | degraus na escada |
|---|---|---|---|
| **Sem anti-cheat** (`nenhum`) | servidor | 0 | 1 |
| **BattlEye** (`battleye`) | usuario, kernel, servidor | 5 | 5 |
| **Easy Anti-Cheat** (`eac`) | usuario, kernel, servidor | 4 | 4 |
| **Valve Anti-Cheat (VAC)** (`vac`) | usuario, kernel, servidor, politica | 4 | 3 |
| **Riot Vanguard** (`vanguard`) | usuario, kernel, servidor, hardware | 4 | 3 |

## Sem anti-cheat

Alvo de laboratório: jogo single-player, servidor LAN próprio ou servidor de comunidade sem AC.

**Não detecta:**
- qualquer leitura de memória ou overlay
- injeção de módulo
- alteração de valores

**Escada (custo × risco × detecção):**

| nível | caminho | custo (dias) | risco | detecção |
|---|---|---|---|---|
| 0 | Laboratório limpo | 0 | nenhum | n/a |

> É aqui que se aprende: sem AC, o único limite é a engine.
> Mesmo em servidor privado, se houver outros jogadores, a regra de respeito se aplica.

## BattlEye

Anti-cheat com componente de kernel (BEDaisy.sys) carregado junto com o jogo, além de varredura de memória e heartbeat para o servidor.

**Detecta:**
- handle externo de leitura/escrita no processo do jogo (ObRegisterCallbacks remove PROCESS_VM_READ/WRITE/OPERATION)
- módulo injetado na lista de módulos do processo
- alteração de arquivo do jogo (ASSINATURA de DLL trocada -> kick 'corrupted file')
- padrões de memória conhecidos (assinatura/heurística)
- driver não assinado / driver mapeado com rastros (quando a versão tem essa checagem ativa)

**Não detecta:**
- leitura de memória feita por driver próprio, se o callback for neutralizado e a leitura não gerar handle observável
- cliente Linux, onde o componente é apenas uma biblioteca de heartbeat
- comportamento do jogador que não infrinja heurística de servidor (ex.: ESP puro, sem aimlock)

**Escada (custo × risco × detecção):**

| nível | caminho | custo (dias) | risco | detecção |
|---|---|---|---|---|
| 0 | Sem AC no caminho | 0 | nenhum | n/a |
| 1 | Desligar o módulo do cliente | 1 | alto | servidores com verificação de integridade expulsam em minutos (kick por arquivo corrompido) e registram flag |
| 2 | Injeção por driver mapeado | 5 | alto | depende do build; rastros de driver mapeado são um vetor conhecido de detecção |
| 3 | Externo com driver próprio de leitura | 10 | médio | é o caminho de menor superfície: não há módulo no jogo; o vetor passa a ser o driver e o comportamento |
| 4 | Corrida contínua | 0 | alto | não existe 'pronto': é manutenção permanente e sempre há janela de ban |

> O componente de kernel é carregado sob demanda junto com o jogo e descarregado ao sair: a janela de análise é a partida.
> Kick por integridade de arquivo não é o mesmo que ban, mas gera flag.
> Em servidores oficiais, o risco de ban é permanente e pode alcançar o hardware (HWID).

## Easy Anti-Cheat

Anti-cheat com driver de kernel e forte peso em detecção por assinatura e integridade; comum em jogos competitivos.

**Detecta:**
- módulos injetados e handles de leitura/escrita no processo
- assinaturas de cheats conhecidos
- alteração de binários/arquivos do jogo
- depuradores e instrumentação anexada

**Não detecta:**
- técnicas externas por hardware (captura de vídeo e entrada sintética em outro dispositivo)
- comportamento discreto que não aciona heurística de servidor

**Escada (custo × risco × detecção):**

| nível | caminho | custo (dias) | risco | detecção |
|---|---|---|---|---|
| 0 | Sem AC no caminho | 0 | nenhum | n/a |
| 1 | Desligar componente do cliente | 1 | muito alto | a maioria dos títulos com EAC recusa iniciar sem o componente |
| 2 | Injeção por driver mapeado | 7 | muito alto | EAC investe pesado em detecção de driver e integridade; vida curta |
| 3 | Externo por kernel | 14 | alto | melhor superfície, ainda com ban wave |

> Títulos com EAC normalmente não oferecem modo offline: o laboratório honesto é escolher outro alvo.
> Ban wave significa que a punição não vem na hora: a conta pode ser perdida semanas depois.

## Valve Anti-Cheat (VAC)

Anti-cheat de modo usuário, com banimento atrasado (ban wave) e escopo por jogo; não usa driver de kernel.

**Detecta:**
- arquivos do jogo alterados
- assinaturas conhecidas de cheats
- injeção de DLL no processo
- comportamento impossível detectado pelo servidor

**Não detecta:**
- leitura externa de memória por ferramenta separada (mas o servidor ainda pode detectar comportamento)
- macro/entrada sintética por hardware externo

**Escada (custo × risco × detecção):**

| nível | caminho | custo (dias) | risco | detecção |
|---|---|---|---|---|
| 0 | Servidor local/LAN | 0 | nenhum | n/a |
| 1 | Partida casual com VAC ligado | 0 | alto | o ban não vem na hora: vem depois, por onda |
| 2 | Externo sem tocar no cliente | 3 | médio | menor para o AC, maior para o servidor (comportamento) |

> O ponto pedagógico do VAC é o ban atrasado: quem testa 'funcionou hoje' não sabe o resultado.
> Não cobre contorno de detecção server-side do jogo.

## Riot Vanguard

Anti-cheat que carrega o driver no boot do Windows e mantém vigilância permanente, inclusive fora do jogo.

**Detecta:**
- drivers não assinados ou conhecidos por cheats
- instrumentação e depuração no processo do jogo
- módulos injetados e leitura de memória suspeita
- máquina virtual / hypervisor não autorizado

**Não detecta:**
- nada prático em software: a superfície em modo usuário e kernel está coberta
- técnicas puramente externas por hardware (captura de vídeo de outro dispositivo)

**Escada (custo × risco × detecção):**

| nível | caminho | custo (dias) | risco | detecção |
|---|---|---|---|---|
| 0 | Sem AC no caminho | 0 | n/a | n/a |
| 1 | Desligar o driver | 1 | muito alto | o jogo não inicia; a conta é perdida |
| 2 | Burlar por software | 0 | muito alto | praticamente certa |

> Objetivo deste playbook: informar, para que o leitor escolha outro alvo. Não é um alvo de laboratório.
> Nenhuma técnica daqui deve ser aplicada em jogo com Vanguard.
