---
title: Documentação
---

# Verificar antes de construir

`prumo` é uma ferramenta de linha de comando para engenharia reversa de jogos com agente de IA. Ela
decide o caminho, executa os passos de leitura e **verifica** se o que o agente encontrou é o que ele diz
que é.

Versão **0.2.0** · adaptador de referência em Linux · quatro motores e cinco anti-cheats documentados.

```
$ prumo diagnostico --motor unity-mono --ac battleye --modo online

# Plano — Unity (Mono) · BattlEye · servidor público

**Risco:** alto
- modo: servidor público — ban permanente, pode alcançar o hardware
- anti-cheat: BattlEye — camadas ativas: usuario, kernel, servidor

## Alertas
- aviso: aqui não existe "pronto": é corrida de detecção
```

## Comece por aqui

<div class="cartoes">
  <a class="cartao" href="{{ '/metodologia.html' | relative_url }}">
    <strong>Metodologia</strong>
    <span>O que é medido, como e por quê. Os números por trás de cada decisão.</span>
  </a>
  <a class="cartao" href="{{ '/adaptadores.html' | relative_url }}">
    <strong>Adaptadores</strong>
    <span>Contrato de processo e como plugar Cheat Engine, Frida, x64dbg.</span>
  </a>
  <a class="cartao" href="{{ '/checks.html' | relative_url }}">
    <strong>Os sete checks</strong>
    <span>Pergunta, implementação e requisito de cada verificação.</span>
  </a>
  <a class="cartao" href="{{ '/motores.html' | relative_url }}">
    <strong>Motores</strong>
    <span>Playbooks por engine: Unity Mono, Unity IL2CPP, Unreal, Source 2.</span>
  </a>
  <a class="cartao" href="{{ '/matriz-ac.html' | relative_url }}">
    <strong>Anti-cheat</strong>
    <span>O que cada AC detecta, escada de bypass, custo em dias e risco.</span>
  </a>
  <a class="cartao" href="{{ '/arquitetura.html' | relative_url }}">
    <strong>Arquitetura</strong>
    <span>As três camadas e por que as "mãos" são de terceiros.</span>
  </a>
</div>

## Instalação

```bash
pipx install "git+https://github.com/overlord111111/prumo"
pipx inject prumo dnfile     # opcional: comando `map` (assembly .NET)
```

O pacote não está no PyPI — o nome `prumo` lá é de outro projeto. Instale sempre do repositório.

## Para contribuir

O material mais útil é playbook: um arquivo JSON em `src/prumo/data/` com passo, check e limitação.
As regras estão no [CONTRIBUTING](https://github.com/overlord111111/prumo/blob/main/CONTRIBUTING.md); o
contrato de uso por agentes, no [AGENTS.md](https://github.com/overlord111111/prumo/blob/main/AGENTS.md).

Esta documentação é gerada a partir dos mesmos dados que a CLI lê — `prumo docs --check` falha se o
documento divergir do playbook.
