<!-- GERADO por `prumo docs`. Não edite à mão: edite src/prumo/data/ e rode `prumo docs`. -->

# Motores cobertos

| motor | backend | o que se lê | passos | limitações |
|---|---|---|---|---|
| **Unity (backend Mono)** (`unity-mono`) | metadata | `<jogo>_Data/Managed/Assembly-CSharp.dll` | 7 | 3 |
| **Unity (backend IL2CPP)** (`unity-il2cpp`) | metadata+nativo | `global-metadata.dat + GameAssembly.dll` | 5 | 3 |
| **Unreal Engine** (`unreal`) | nativo | `GObjects/GNames + UWorld` | 5 | 3 |
| **Source 2** (`source2`) | schema+ponteiro | `lista de entidades por classe + schema do jogo` | 3 | 2 |

## Unity (backend Mono)

O jogo é C# compilado em MSIL dentro de Assembly-CSharp.dll: nomes de classe, campo e método continuam legíveis.

**Como funciona:** Unity com backend Mono entrega os assemblies em <jogo>_Data/Managed/*.dll. O IL é reversível por leitura (dnSpy/ILSpy/prumo map): não há ofuscação por padrão.

| # | passo | checks | risco |
|---|---|---|---|
| M1 | Confirmar o backend (Mono ou IL2CPP) | processo | nenhum |
| M2 | Extrair o mapa de tipos e campos | estrutura | nenhum |
| M3 | Escolher a classe do objeto do mundo | estrutura | nenhum |
| M4 | Provar o campo por ação | campo | baixo |
| M5 | Enumerar a lista de entidades | campo, entidades | baixo |
| M6 | Projetar mundo para tela | projecao | baixo |
| M7 | Fixar a assinatura | assinatura | baixo |

**Limitações declaradas:**
- Campo privado pode estar inlinado em struct; nem toda entidade tem nome de classe óbvio.
- Jogos com ofuscação (Cecil/ConfuserEx) reduzem a leitura a nomes genéricos: aí o caminho vira disasm, não metadata.
- Backend Mono não é garantia: checar M1 antes de tudo.

## Unity (backend IL2CPP)

O C# é convertido para C++ e compilado nativo; os nomes sobrevivem em global-metadata.dat, e o código em GameAssembly.dll.

**Como funciona:** IL2CPP gera <jogo>_Data/il2cpp_data/Metadata/global-metadata.dat (nomes e assinaturas) e GameAssembly.dll (código nativo). Dá para recuperar a estrutura de tipos lendo a metadata; os endereços vêm do binário nativo.

| # | passo | checks | risco |
|---|---|---|---|
| I1 | Confirmar IL2CPP | processo | nenhum |
| I2 | Recuperar a estrutura de tipos | estrutura | nenhum |
| I3 | Ligar tipo a endereço | assinatura, campo | baixo |
| I4 | Provar o campo por ação | campo | baixo |
| I5 | Enumerar entidades e projetar | entidades, projecao | baixo |

**Limitações declaradas:**
- Sem a metadata correspondente à versão exata do jogo, os índices de tipo não batem.
- Deslocamentos nativos mudam a cada patch: tudo que for endereço precisa de assinatura, não de constante.
- Este playbook cobre leitura de estrutura; não cobre contorno de anti-cheat.

## Unreal Engine

Objetos do jogo (UObject) são instâncias de classes C++ com RTTI e uma tabela global de nomes; a lista de atores do mundo é acessível por ponteiro.

**Como funciona:** UE mantém GNames (ou o equivalente por versão) e GObjects/UObjectArray. Cada UObject tem vtable, e o nome da classe vem por FName -> índice -> tabela de strings. A partir daí dá para atravessar o mundo (UWorld -> Level -> Actors).

| # | passo | checks | risco |
|---|---|---|---|
| U1 | Localizar GObjects e GNames | assinatura | baixo |
| U2 | Resolver o nome de uma classe conhecida | estrutura | baixo |
| U3 | Chegar no UWorld | entidades | baixo |
| U4 | Ler a raiz do componente | campo | baixo |
| U5 | Projetar e fixar assinatura | projecao, assinatura | baixo |

**Limitações declaradas:**
- Layout de UObject varia por versão da engine e por build customizada do estúdio.
- Jogos com ofuscação de símbolos exigem mais disasm e menos nome.
- Não cobre contorno de anti-cheat.

## Source 2

Engine da Valve (CS2, Dota 2). Entidades ficam numa árvore de cenas com schema de tipos publicado nos arquivos do jogo.

**Como funciona:** Source 2 usa schemas (arquivos de tipo do próprio jogo) e uma lista de entidades por classe. O schema dá nomes de campo sem engenharia reversa pesada; o que exige trabalho é chegar no ponteiro da lista e na matriz da câmera.

| # | passo | checks | risco |
|---|---|---|---|
| S1 | Ler o schema | estrutura | nenhum |
| S2 | Achar a lista de entidades | assinatura, entidades | baixo |
| S3 | Validar posição e projeção | campo, projecao | baixo |

**Limitações declaradas:**
- Atualizações frequentes quebram assinatura: o playbook exige refixar a cada patch.
- Jogos competitivos da Valve têm VAC e detecção server-side: leia antes o playbook ac-vac.
