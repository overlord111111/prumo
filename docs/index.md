# Documentação do prumo

O prumo decide o caminho, executa os passos de leitura e verifica se o resultado é o que o agente diz que é.
Comece pelo [README](../README.md) para instalar e usar.

## Para usar

- [Metodologia](metodologia.md) — o que é medido, como é medido e o que cada número significa.
- [Adaptadores](adaptadores.md) — como o prumo fala com Cheat Engine, Frida, x64dbg e afins.
- [Checks](checks.md) — os sete checks, com pergunta, implementação e requisito. Gerado dos dados.
- [Motores](motores.md) — playbooks por engine. Gerado dos dados.
- [Matriz de anti-cheat](matriz-ac.md) — o que cada AC detecta, escada de bypass, custo e risco. Gerado dos dados.

## Para contribuir

- [Como contribuir](../CONTRIBUTING.md) — regras, checklist e o que não entra no projeto.
- [Arquitetura](arquitetura.md) — as três camadas e por que as "mãos" são de terceiros.
- [AGENTS.md](../AGENTS.md) — o contrato que um agente de IA segue ao usar o prumo.
- [Segurança](../SECURITY.md) — escopo, riscos conhecidos e como reportar falha.

## Estado

Versão 0.2.0. O adaptador de referência é Linux. Em Windows, o caminho é plugar uma ferramenta MCP de
memória; o contrato de adaptador está descrito em [adaptadores.md](adaptadores.md).
