# Guia 01 — coleta, ingestão e dataset

Este guia acompanha a primeira transformação de uma amostra da sua letra em
um registro que pode ser auditado e, mais adiante, usado pelo gerador. O fluxo
é local: a imagem e os dados derivados são pessoais e não devem ser enviados à
rede nem versionados no Git.

> **Limite de uso:** o projeto aprende somente a letra do próprio titular, com
> consentimento explícito. Não colete assinaturas e não use amostras de outra
> pessoa.

## 1. Objetivo da etapa

A etapa precisa preservar três coisas juntas:

- **conteúdo:** o texto que foi escrito;
- **imagem:** a página ou o recorte que contém a escrita;
- **proveniência:** como, quando e de qual arquivo aquele registro veio.

Isso permite responder depois “qual texto corresponde a esta imagem?” e
“qual amostra originou este glifo?”. Também permite medir o que ainda não foi
capturado, em vez de escolher novas folhas às cegas.

O resultado esperado é um **manifesto JSONL** (JSON Lines): um arquivo UTF-8
com um objeto JSON por linha. Ele não é uma coleção de imagens soltas. Cada
registro é um `ManifestEntry`, com página, região, texto, confiança e
proveniência.

### Entrada, transformação e saída

| Parte | O que entra | O que acontece | O que sai |
|---|---|---|---|
| Coleta | Folha preenchida pelo titular, digitalizada | A imagem é guardada localmente | Arquivo em `samples/` |
| Normalização | `Pillow Image` ou `numpy.ndarray` | Orientação EXIF, tons de cinza e contraste | `numpy.ndarray` 2-D em tons de cinza |
| Segmentação | Página normalizada | Linhas escuras são agrupadas por projeção horizontal | `list[LineRegion]` |
| Associação | Regiões e seus textos conhecidos | A relação imagem–texto é validada | Entradas GOLD |
| Manifesto | Entradas `ManifestEntry` | Registros elegíveis são serializados | JSONL em `dataset/` ou caminho escolhido |
| Cobertura | Texto existente ou candidato | Caracteres, tokens e operadores são contados | `CoverageReport` ou relatório JSON |

A associação e a segmentação são contratos separados. A função
`ingest_source_pair` não faz OCR nem segmenta: recebe as regiões e os textos
fornecidos pelo chamador, valida-os e cria os registros.

## 2. Termos essenciais

- **Amostra:** uma observação da escrita, normalmente uma página ou uma região
  recortada.
- **Página (`PageMetadata`):** identificação e dimensões da imagem de origem:
  `page_id`, `source_path`, `width`, `height`, `dpi` opcional e
  `provenance`.
- **Região (`LineRegion`):** retângulo em pixels da página. Tem `x`, `y`,
  `width`, `height` e `line_index`. Coordenadas começam em zero; largura e
  altura devem ser positivas e o retângulo precisa caber na imagem.
- **Texto correspondente:** sequência exata que aparece na região. Não
  “corrija” pontuação, acentos ou operadores para deixar o resultado mais
  bonito.
- **Proveniência:** metadados que explicam a origem e o método de criação do
  registro. No caminho `source-pair`, inclui `method=source-pair-gold`, o
  caminho do `source.py`, seu SHA-256 e `owner_consent=true`.
- **Confiança:** número entre `0` e `1` usado para classificar uma entrada.
  `gold` é `>= 0,90`, `silver` é `>= 0,60` e `< 0,90`, e `quarantine` é `<
  0,60`.
- **Elegível:** entrada GOLD ou SILVER. `eligible_entries` e as operações
  padrão de `write_manifest`/`read_manifest` excluem `quarantine`.
- **Quarentena:** dado duvidoso que fica fora do treino até ser revisado. Pode
  aparecer em um dump de auditoria com `include_quarantine=True`.
- **Manifesto JSONL:** arquivo de registros, um objeto por linha. O módulo
  `manual_handwrite.data` fornece `write_manifest` e `read_manifest`.
- **Cobertura:** conjunto de caracteres, tokens e operadores já observados.
  “Falta” significa que um item ainda não apareceu no que foi analisado; não é
  uma correção automática.
- **Captura adaptativa:** escolha de novos trechos para cobrir lacunas. O
  `optimize_coverage` seleciona gananciosamente candidatos com mais cobertura
  nova por caractere, respeitando `max_snippets` e, opcionalmente, `max_cost`.

## 3. Coleta física das amostras

### 3.1 Preparar a folha

A folha-modelo planejada para a Fase 2 é um PDF A4 com marcadores ArUco e uma
grade contendo `a-z`, `A-Z`, `0-9`, vogais acentuadas, `ç`, maiúsculas,
pontuação comum, `R$`, `%`, três variantes por caractere e 40 palavras
frequentes em português. O comando planejado é:

```bash
uv run handwrite template --out folha-modelo.pdf
```

Esse comando ainda é futuro. Não trate a existência do contrato como prova de
que a implementação está disponível.

Imprima em A4 a 100%, sem “ajustar à página”, e escreva com sua caneta habitual
na velocidade normal. O objetivo é capturar a letra natural, não uma versão
caligrafada. Preencha as três variantes pedidas quando a folha estiver
implementada. Não escreva sobre os quatro marcadores dos cantos e não coloque
assinatura em nenhuma parte.

### 3.2 Digitalizar

Prefira scanner. Se usar celular, use um aplicativo de digitalização e evite
sombras, reflexos, desfoque e perspectiva extrema.

- Use **300 dpi ou mais**.
- Prefira PNG ou JPEG de alta qualidade.
- Mantenha a folha inteira visível e os quatro marcadores.
- Guarde o original em `samples/`, que é dado pessoal e deve estar ignorado
  pelo Git.
- Não coloque amostras reais, dataset derivado, pesos ou saídas em commits nem
  em logs de CI.

Para a v1, a documentação de coleta estima duas folhas, cerca de seis
variantes por caractere. Para a v2 neural, a expectativa é de cinco a dez
folhas e algumas páginas de texto livre. Esses números orientam a coleta; não
substituem a verificação de cobertura.

## 4. Ingestão da página

### 4.1 Normalizar

Use `normalize_page(image)` de `manual_handwrite.ingest`:

```python
from PIL import Image
from manual_handwrite.ingest import normalize_page

with Image.open("samples/folha-01.jpg") as image:
    page = normalize_page(image)
```

A função aceita uma imagem Pillow ou um `numpy.ndarray`. Faz uma cópia, aplica
`ImageOps.exif_transpose`, converte para `L` (tons de cinza) e normaliza o
contraste entre os percentis 1 e 99. O retorno é um array NumPy `uint8` 2-D.
Uma página uniforme é devolvida sem divisão por zero.

Isso é **normalização**, não reconhecimento de texto. O módulo não faz OCR,
não chama VLM e não grava uma cópia da imagem por conta própria.

### 4.2 Segmentar linhas

Passe o array normalizado a `segment_lines(page)`:

```python
from manual_handwrite.ingest import segment_lines

regions = segment_lines(page, threshold=200, min_ink_pixels=1, gap_tolerance=2)
```

O padrão é `threshold=200`, `min_ink_pixels=1` e `gap_tolerance=0`. Uma linha
de imagem é considerada ativa quando tem pelo menos `min_ink_pixels` pixels
abaixo do limiar. Linhas ativas consecutivas viram um retângulo de largura
inteira. `gap_tolerance` junta pequenos intervalos brancos dentro de uma mesma
linha.

O retorno é uma lista ordenada de `LineRegion`; cada item recebe
`line_index` começando em zero. A função exige uma matriz 2-D numérica. Se a
página estiver vazia ou sem linhas ativas, retorna `[]` — não inventa regiões.

A segmentação atual é deliberadamente simples e determinística. A ingestão
completa da Fase 2, ainda futura, deverá detectar marcadores, corrigir
perspectiva, binarizar com Sauvola, recortar células e rotular pela posição da
grade. Portanto, hoje não há um comando funcional que transforme
automaticamente a folha-modelo em todas as células rotuladas.

## 5. Associar imagem e texto com `source-pair`

Quando o texto já existe em um arquivo-fonte, não use OCR para redescobri-lo.
O caminho implementado é `source-pair`: ele recebe a imagem, um `source.py`,
as regiões e os textos correspondentes.

A API confirmada é:

```python
from manual_handwrite.data.source_pair import ingest_source_pair

entries = ingest_source_pair(
    "samples/pagina-01.png",
    "exemplos/source.py",
    [(120, 640, 900, 80)],
    ["for item in lista:"],
    owner_consent=True,
)
```

Uma região pode ser fornecida como `LineRegion`, como objeto com as chaves
`x`, `y`, `width`, `height`, `line_index`, ou como sequência de quatro inteiros
`(x, y, width, height)` — nesse último caso o índice é atribuído pela posição
na lista. Uma sequência de cinco inteiros também é aceita, já contendo o
`line_index`. Deve haver exatamente a mesma quantidade de regiões e textos;
`text` pode ser uma string ou `None`.

A função abre a imagem apenas para obter `width` e `height`; não copia a
imagem. Lê os bytes do `source.py`, exige sintaxe Python válida e calcula seu
SHA-256. Cada resultado recebe confiança `1.0`, portanto tier `gold`, e um
`sample_id` no formato `{page_id}-line-{line_index}`. Por padrão, `page_id` é o
`stem` do nome da imagem.

O consentimento não é implícito: `owner_consent` precisa ser exatamente
`True`. Metadados marcados como assinatura também são recusados. Erros dessa
operação levantam `SourcePairError`.

### CLI funcional

A CLI expõe o mesmo caminho com um JSON de regiões. O objeto pode usar
`regions` ou `line_regions`, mas precisa também conter a lista `texts`:

```json
{
  "regions": [[120, 640, 900, 80]],
  "texts": ["for item in lista:"]
}
```

Execute:

```bash
uv run handwrite source-pair \
  samples/pagina-01.png \
  exemplos/source.py \
  regioes.json \
  --owner-consent \
  --out dataset/manifest.jsonl
```

Também é aceita uma lista de objetos com `region` e, opcionalmente, `text`.
O arquivo de saída é escrito por `write_manifest`; como as entradas do
`source-pair` são GOLD, elas entram no manifesto normalmente.

O `source.py` usado no exemplo precisa conter Python válido. A linha escrita na
imagem e a string em `texts` devem ser a mesma coisa, incluindo espaços
relevantes, acentos e operadores. O código acima é um exemplo de contrato,
não uma promessa de que a região foi detectada automaticamente.

## 6. Formato do dataset e confiança

Uma linha produzida por `ManifestEntry.to_dict()` contém, conceitualmente:

```json
{
  "sample_id": "pagina-01-line-0",
  "page": {
    "page_id": "pagina-01",
    "source_path": "samples/pagina-01.png",
    "width": 1200,
    "height": 900,
    "dpi": null,
    "provenance": {
      "method": "source-pair-gold",
      "source_path": "exemplos/source.py",
      "source_sha256": "...",
      "owner_consent": "true"
    }
  },
  "region": {"x": 120, "y": 640, "width": 900, "height": 80, "line_index": 0},
  "text": "for item in lista:",
  "confidence": 1.0,
  "tier": "gold",
  "provenance": {
    "method": "source-pair-gold",
    "source_path": "exemplos/source.py",
    "source_sha256": "...",
    "owner_consent": "true"
  }
}
```

O valor real do hash é calculado pelo programa; `...` acima é apenas uma
abreviação explicativa e não deve ser copiada. `write_manifest(path, entries)`
cria a pasta-pai, grava UTF-8 com uma entrada por linha e retorna a quantidade
gravada. `read_manifest(path)` reconstitui os registros e filtra quarentena
por padrão. Para auditoria explícita, use `include_quarantine=True` nas duas
funções.

O manifesto é o dataset de anotações; ele referencia a imagem por caminho e
não incorpora os pixels. Mantenha os caminhos válidos e relativos ao arranjo
local do projeto. O dataset real continua sendo pessoal e fora do Git.

### GOLD, SILVER e QUARANTINE

- **GOLD:** texto e correspondência têm alta garantia. O `source-pair` atual
  produz apenas GOLD porque o `source.py` é validado e o texto/região são
  fornecidos explicitamente.
- **SILVER:** dado plausível, mas com garantia menor. Pode ser elegível, porém
  deve ser distinguido de GOLD em avaliação e auditoria.
- **QUARANTINE:** incerteza abaixo de `0,60`. Não entra no dataset elegível.

O contrato não permite `confidence` fora de `[0, 1]`, nem um `tier` declarado
que contradiga a confiança.

## 7. Texto desconhecido e VLM: o que existe e o que falta

Se não existe fonte original, o plano prevê um adaptador de VLM para sugerir a
transcrição. A resposta deverá ser JSON válido, comparada entre passes e
verificada por sinais de sintaxe/indentação quando for Python. A classificação
prevista é GOLD, SILVER ou QUARANTINE, e dúvida não pode virar treino.

Isso não deve ser confundido com o caminho implementado de `source-pair`: o
módulo atual não faz OCR, não chama VLM, não faz rede e não fornece uma CLI de
transcrição automática. A ingestão automática da folha com ArUco/Sauvola e a
rotulagem das células também pertencem à Fase 2 futura.

## 8. Medir cobertura e escolher a próxima captura

A API `analyze_text(text)` de `manual_handwrite.coverage` conta:

- `characters`: cada caractere do texto, incluindo espaços e acentos;
- `tokens`: nomes, números e strings reconhecidos pelo tokenizer Python;
- `operators`: operadores Python reconhecidos, como `:`, `=`, `==`, `>=` e
  parênteses;
- `missing_tokens`: itens ausentes do conjunto `CORE_TOKENS`;
- `missing_operators`: itens ausentes do conjunto `CORE_OPERATORS`.

Exemplo executável:

```python
from manual_handwrite.coverage import analyze_text

report = analyze_text("for item in lista:\n    print(item >= 1)\n")
print(report.as_dict())
```

A CLI funcional escreve exatamente esse relatório em JSON:

```bash
uv run handwrite coverage exemplos/source.py --out dataset/coverage.json
```

Se o Python estiver incompleto ou em edição, a contagem de caracteres continua
útil; falhas de `IndentationError` ou `tokenize.TokenError` não fabricam tokens.
A análise não altera o texto.

Para selecionar trechos candidatos, use `optimize_coverage(candidates,
max_snippets, existing_text="", max_cost=None)` em
`manual_handwrite.coverage.optimizer`:

```python
from manual_handwrite.coverage.optimizer import optimize_coverage

selection = optimize_coverage(
    ["if valor >= 1:", "for item in lista:", "print(item)"],
    max_snippets=2,
    existing_text="",
)
print(selection.as_dict())
```

O algoritmo é determinístico, preserva a ordem de entrada em empates e ignora
candidatos que não acrescentam cobertura. O custo padrão é o comprimento do
texto; `max_cost` limita o custo total. A seleção mede somente o vocabulário
que `analyze_text` realmente observou — não presume que um símbolo está
coberto só porque apareceu em outro contexto.

Na prática, leia `missing_tokens` e `missing_operators`, escolha ou gere
candidatos que contenham essas lacunas, capture-os com a sua letra e depois
analise novamente. Cobertura alta não prova qualidade visual: ainda é preciso
inspecionar legibilidade e manter amostras para avaliação fora do treino.

## 9. O que já existe versus o futuro

### Já existe

- `normalize_page` e `segment_lines`, com processamento local e determinístico;
- `PageMetadata`, `LineRegion`, `ManifestEntry` e `ConfidenceTier`;
- leitura e escrita do manifesto JSONL;
- `ingest_source_pair` e a CLI `handwrite source-pair` para pares
  imagem/`source.py` GOLD;
- `analyze_text`, `CoverageReport` e a CLI `handwrite coverage`;
- seleção gananciosa em `optimize_coverage`/`greedy_select`;
- testes de ingestão, dataset, cobertura, CLI e contratos de segurança.

### Futuro planejado

- `handwrite template` e a folha-modelo A4;
- correção de perspectiva por marcadores ArUco, binarização Sauvola, recorte e
  rotulagem automática das células;
- ingestão de texto desconhecido com adaptador VLM e revisão de confiança;
- construção do `GlyphBank`, `StylePack` treinado e geração personalizada;
- modelo neural opcional apenas na Fase 5, sob comando explícito.

Os comandos `template`, `ingest`, `train` e `write` aparecem no contrato do
produto, mas não devem ser documentados como funcionais sem implementação. No
estado atual, os caminhos funcionais relevantes para esta etapa são
`source-pair` e `coverage` (além dos módulos Python de normalização e
segmentação).

## 10. Critérios de aceite

Considere esta etapa aceita somente quando todos os itens abaixo forem
verdadeiros:

- A amostra pertence ao próprio titular e há consentimento explícito.
- A folha está inteira, com marcadores preservados quando aplicável, e foi
  digitalizada a pelo menos 300 dpi.
- Cada região tem coordenadas não negativas, dimensões positivas e limites
  dentro da imagem.
- Há um texto para cada região; o texto preserva exatamente acentos,
  pontuação, espaços relevantes e operadores.
- O `source.py`, quando usado, passa a validação de sintaxe e seu SHA-256 está
  na proveniência.
- Toda entrada tem `sample_id`, página, região, confiança válida e
  proveniência; `owner_consent` é `true`.
- O manifesto abre com `read_manifest` sem erro e não contém quarentena quando
  foi escrito com as opções padrão.
- O relatório de cobertura foi gerado e suas lacunas foram consideradas na
  próxima captura.
- Amostras reais e derivados continuam fora do Git, CI e logs.
- Os gates do repositório passam:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

Para a implementação futura da Fase 2, o aceite definido no plano é recuperar
pelo menos 95% das células com o rótulo correto em uma folha sintética gerada
nos testes. Isso ainda não é um critério satisfeito pela segmentação simples
atual.

## 11. Como depurar

### A imagem não abre

Confirme o caminho, o formato e se o arquivo não está corrompido. Pillow lança
`SourcePairError("could not read page image")` no `source-pair`. Teste primeiro
abrindo a imagem com `Image.open` e verifique suas dimensões.

### A normalização produz resultado estranho

Verifique se a entrada é uma imagem Pillow ou array NumPy numérico. Para array,
confirme forma `(altura, largura)` ou `(altura, largura, canais)` com 1, 3 ou 4
canais. Veja se a orientação EXIF do original está correta e se a página não é
uniforme ou excessivamente estourada.

### Nenhuma linha foi encontrada, ou linhas foram unidas

Inspecione `page` após `normalize_page`. Ajuste, em chamada de teste,
`threshold`, `min_ink_pixels` e `gap_tolerance`. Um limiar alto demais pode
considerar ruído como tinta; um limiar baixo demais pode perder traços claros.
`gap_tolerance` alto demais une linhas distintas. `segment_lines` retorna
regiões de largura total, não recortes apertados ao redor de cada palavra.

### `source-pair` recusa o consentimento

Passe `--owner-consent` na CLI ou `owner_consent=True` na API. Não contorne a
checagem: ela é parte do contrato de segurança.

### Regiões e textos não combinam

Conte os dois arrays. A função exige o mesmo número de itens e rejeita regiões
fora dos limites da imagem. Para uma tupla de quatro números, confirme a ordem
`x, y, width, height`; não confunda `width`/`height` com `right`/`bottom`.

### O `source.py` falha

Execute a operação com um arquivo Python válido. `ingest_source_pair` verifica
encoding e `ast.parse`; erro de sintaxe, encoding inválido ou arquivo ilegível
vira `SourcePairError`. O texto em `texts` é a anotação da região e não é
extraído automaticamente do arquivo.

### O manifesto tem menos linhas do que as entradas

`write_manifest` exclui `quarantine` por padrão. Use
`write_manifest(path, entries, include_quarantine=True)` apenas para um dump de
auditoria. Ao ler, `read_manifest(path, include_quarantine=True)` permite
inspecionar esses registros. Para erro de formato, a exceção informa a linha
inválida do JSONL.

### A cobertura parece errada

Lembre que `analyze_text` conta o texto recebido, não as imagens e não infere o
que está faltando visualmente. Em Python incompleto, tokens podem não ser
contados, embora os caracteres sejam. Compare `report.as_dict()` com o arquivo
original e não edite o texto só para reduzir a lista de ausências.

### A cobertura está alta, mas o resultado visual não está bom

Cobertura mede presença de símbolos, não semelhança de estilo, legibilidade ou
qualidade da digitalização. Separe o diagnóstico: primeiro valide conteúdo e
manifesto; depois qualidade da amostra e, em etapa posterior, StylePack e
renderização. Reserve páginas reais fora do treino para comparação e avaliação
do titular.

### Comando não encontrado

Instale o projeto no ambiente previsto e execute com `uv run`. Confirme que o
comando existente é `source-pair` ou `coverage`; `template`, `ingest`, `train` e
`write` são contratos futuros no estado documentado.

## Regra de rastreabilidade

Não aceite um dataset apenas porque o arquivo JSONL foi criado. Deve ser
possível seguir o caminho completo: texto original → anotação → região na
página → proveniência → entrada elegível. Se houver dúvida, mantenha a amostra
em quarentena e registre o motivo; nunca transforme uma suposição em dado de
treinamento.
