# Metodologia

Este projeto existe por causa de uma regra: **medir, não opinar**. Toda afirmação aqui ou tem número, ou está
marcada como hipótese.

## 1. Varredura de assinatura (AOB) com curinga

O caso real: achar um padrão de bytes numa região de memória, onde alguns bytes mudam a cada execução
(`48 8B 05 ?? ?? ?? ??`) e outros não.

Medido em 2026-10-19, nesta máquina (bloco de 268 MB, assinatura de 12 bytes com 5 bytes de curinga, 3
ocorrências plantadas):

| abordagem | velocidade | projeção para 2 GB |
|---|---|---|
| `bytes.find` (exato) | 2.690 MB/s | 0,8 s |
| **ancorada no maior trecho fixo** | **1.525 MB/s** | **1,3 s** |
| regex com `(?=…)` e `.{5}` | 69 MB/s | 30 s |

**Decisão que a medição tomou:** regex está fora do caminho crítico (23× mais lento), e a implementação usa
âncora no maior trecho fixo com verificação byte a byte. Reproduzir:

```bash
prumo verificar --check assinatura --padrao "48 8B 05 ?? ?? 33 44 66 77 88 99 AA BB" --buffer-arquivo dump.bin
```

## 2. Dados como fonte de verdade

`src/prumo/data/` guarda motor, anti-cheat e checks em JSON. Três documentos são **gerados** deles:

| documento | origem |
|---|---|
| `docs/motores.md` | `data/motores/*.json` |
| `docs/matriz-ac.md` | `data/ac/*.json` |
| `docs/checks.md` | `data/checks.json` |

A CI roda `prumo docs --check` e falha se o documento não bater com o dado. Consequência prática: **playbook e
documentação não podem divergir** — o modo mais comum de um projeto assim apodrecer.

## 3. Os checks e o que cada um realmente prova

| check | prova | não prova |
|---|---|---|
| `estrutura` | o tipo existe e a forma é compatível com o alvo | que o campo escolhido é o certo |
| `campo` | o valor muda com a ação, na direção esperada | que o efeito visual está correto |
| `entidades` | existem várias entidades com posições distintas | que a lista é completa |
| `projecao` | a matriz acerta um ponto conhecido | que a matriz continua válida depois de trocar de câmera |
| `assinatura` | o padrão é único e tem bytes fixos | que o patch seguinte não muda o código ao redor |
| `ac` | qual AC está no caminho | se ele vai te detectar |

**Regra de gate:** um passo do playbook só avança com o check anterior em `PASS`. `INDETERMINADO` não é
passagem — é pendência explícita.

## 4. Por que `INDETERMINADO` existe

Os checks `processo`, `campo` e `entidades` precisam de processo vivo. Sem adaptador conectado, o prumo
devolve `INDETERMINADO` com o motivo e o requisito. A alternativa — devolver `PASS` por padrão — tornaria o
instrumento pior que inútil: ele daria confiança sem prova.

## 5. Reproduzir a prova de campo

O teste de integração roda contra um assembly real, e o binário usado no exemplo é público e de código aberto
(OpenRA, MIT):

```bash
# baixe o release portable do OpenRA, extraia OpenRA.Game.dll e rode:
PRUMO_TEST_DLL=/caminho/OpenRA.Game.dll pytest tests/test_dotnet.py -q
prumo map /caminho/OpenRA.Game.dll --alvo health --orcamento 2500
```

Resultado medido nessa execução: **957 classes, 3.658 campos**, com `OpenRA.Actor` no topo do ranking para o
alvo `health` (campo `health` do tipo `OpenRA.Traits.IHealth`). Saída íntegra em
[`examples/mapa-openra-health.md`](../examples/mapa-openra-health.md).
