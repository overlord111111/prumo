# Segurança

## Escopo

O prumo é ferramenta de pesquisa em segurança de software e engenharia reversa. Ele **não** executa código do
alvo, **não** coleta dados e **não** se comunica com servidor algum.

## Postura do projeto

| o prumo faz | o prumo não faz |
|---|---|
| lê arquivos locais que você indicar (assembly, dump, matriz) | não envia nada para a rede |
| valida dados e devolve veredito com número | não telefona para casa, não tem telemetria |
| documenta método e risco de anti-cheat | não distribui offset de jogo vivo nem binário de bypass |

## Riscos conhecidos do uso

1. **Antivírus**: ler memória de outro processo é comportamento que antivírus sinaliza — inclusive em
   ferramentas legítimas. Solução correta é **exceção de pasta estreita**, não desligar a proteção.
2. **Anti-cheat**: qualquer técnica aqui documentada pode gerar ban permanente, inclusive por hardware (HWID).
   Use em ambiente próprio (single-player/LAN) para aprender.
3. **Ferramentas de terceiros (adaptadores)**: não são nossas. Leia o código antes de rodar. Regra do projeto:
   fonte legível ou não roda.
4. **Binários não confiáveis**: rode em VM/sandbox. O prumo lê metadados, mas o arquivo que você abre pode ser
   hostil.

## Reportar vulnerabilidade no prumo

Abra uma issue privada (Security → Report a vulnerability) ou mande contato pelo perfil do mantenedor. Inclua:
versão, comando, entrada e comportamento observado. Não publique exploit antes da correção.

Alvos aceitos: falha que faça o prumo executar código do arquivo analisado, escrever fora do diretório de
saída, ou reportar `PASS` sem medição. O último é o mais grave: um check que mente destrói o propósito do
projeto.
