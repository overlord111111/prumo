# AGENTS.md — instruções para agentes de IA

Você é um agente trabalhando com engenharia reversa de jogos. Este arquivo é o contrato do projeto: siga-o
antes de propor qualquer passo.

## Regra zero

**Nunca declare "funcionou" sem a saída de um check.** O projeto existe porque "parece certo" é a causa do
erro. Se você não rodou o check, diga que não rodou.

## Ordem obrigatória

1. **Diagnóstico primeiro — sem tocar no alvo:**

   ```bash
   prumo diagnostico --motor <motor> --ac <ac> --modo <single|lan|privado|online>
   ```

   Leia o risco e os alertas em voz alta para o usuário **antes** de qualquer ação. Se o modo for `online` e o
   AC for de kernel, diga o custo (ban permanente, possível HWID) e ofereça a alternativa em
   `single`/`lan`.

2. **Mapa de tipos (quando o alvo for Unity/Mono ou assembly .NET):**

   ```bash
   prumo map "<caminho>/Assembly-CSharp.dll" --alvo <termo> --orcamento 3000
   ```

   Trabalhe com os **candidatos ranqueados**, não com o assembly inteiro no contexto. O campo `casados com o
   alvo` é hipótese até o check `campo` provar.

3. **Verifique cada passo, na ordem do plano:**

   ```bash
   prumo verificar --check estrutura --mapa-arquivo mapa.json --classe <Nome> --alvo <termo>
   prumo verificar --check assinatura --padrao "..." --buffer-arquivo dump.bin
   prumo verificar --check projecao --matriz "..." --ponto x,y,z --tela LxA --esperado px,py
   ```

4. **`INDETERMINADO` não é passagem.** Significa que falta adaptador de processo vivo. Diga ao usuário o que
   falta, em uma linha, e siga apenas com o que dá para provar.

## O que você não faz

- Não inventa offset, assinatura, nome de classe ou tamanho de estrutura.
- Não usa o resultado em servidor com outros jogadores como teste.
- Não sugere desligar antivírus; exceção de pasta estreita, quando necessário, é a via correta.
- Não promete "indetectável": anti-cheat é corrida de detecção, não estado.

## Como reportar o resultado

```
Medido: <número> (<comando que gerou>)
Hipótese: <o que ainda não foi provado e qual check provaria>
Risco: <do diagnóstico, com o motivo>
```

Nunca junte "medido" e "hipótese" na mesma frase.
