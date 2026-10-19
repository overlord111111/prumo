# Como contribuir

A contribuição mais valiosa é **conhecimento estruturado**, não código: um playbook de motor ou de anti-cheat.

## Regras do projeto (não negociáveis)

1. **Nada de offset de jogo vivo** no repositório. Offset envelhece e transforma o projeto em estoque de cheat
   pronto.
2. **Nada de binário de bypass** de anti-cheat. Documenta-se o método e o custo, não se distribui a arma.
3. **Toda afirmação tem número ou fonte.** "Funciona bem" não entra; "1.525 MB/s em 268 MB" entra.
4. **Documentação é gerada.** Se você mexeu em `src/prumo/data/`, rode `prumo docs` e commite o resultado.
5. **Fonte legível ou não roda.** Script/binário de terceiro só entra se o código for auditável.

## Adicionar um playbook de motor

1. Copie `src/prumo/data/motores/unity-mono.json` como modelo.
2. Preencha: `id`, `nome`, `resumo`, `como_funciona`, `acesso`, `passos`, `limitacoes`, `referencias`.
3. **Cada passo precisa de pelo menos um check** existente (`processo`, `estrutura`, `campo`, `entidades`,
   `projecao`, `assinatura`, `ac`). A validação falha se você citar um check inexistente.
4. Adicione o novo id em `MOTORES` (`src/prumo/dados.py`) e no teste `test_motores_e_acs_esperados_existem`.
5. Rode:

```bash
prumo dados          # valida
prumo docs           # regenera documentação
pytest -q            # testes
```

6. Abra o PR com **um exemplo verificável**: a saída de `prumo diagnostico` para o seu motor, ou um trecho de
   evidência que sustente cada passo.

## Adicionar um anti-cheat

Mesmo caminho, em `src/prumo/data/ac/`. Regras específicas:

- A `escada` **começa obrigatoriamente no nível 0** (é o único degrau sem AC no caminho).
- Cada degrau tem `custo_dias`, `risco` e `detectabilidade`. Se você não mediu, escreva `desconhecido` — não
   invente número.
- Separe **detecta** de **não detecta**. A parte "não detecta" é a mais útil para quem lê.

## Checklist do PR

- [ ] `pytest -q` verde
- [ ] `ruff check src tests` limpo
- [ ] `prumo dados` sem falha
- [ ] `prumo docs --check` verde
- [ ] cada passo novo cita só checks existentes
- [ ] nenhuma afirmação sem número/fonte
- [ ] sem offset de jogo vivo, sem binário de bypass

## Código

- Python 3.11+, sem dependência obrigatória.
- Estilo: `ruff` (linha 110). Tipos onde ajuda a leitura.
- Teste junto com a mudança. Os checks precisam de teste com **caso que passa e caso que falha** — teste que
  só cobre o caminho feliz não prova nada.

## Reportar problema

Abra issue com: o que você esperava, o que aconteceu, e a saída crua do comando. Se for falha de check, inclua
a entrada (padrão/matriz/mapa) — sem isso não é reproduzível.
