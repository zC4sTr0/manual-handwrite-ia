# Como o projeto funciona

Este é o guia operacional do `manual-handwrite-ia`: o que pode ser executado
agora, quais são os contratos já definidos e o que ainda é plano. A palavra
“IA” descreve uma possibilidade futura; o núcleo atual é local, determinístico
e explícito.

> **Estado atual — Fase 1: base de scan + Data Factory.** Hoje existem três
> comandos funcionais: `scanify`, `coverage` e `source-pair`. Eles exigem
> entradas fornecidas pelo usuário. Não há páginas reais do proprietário no
> repositório, nem geração personalizada completa. `template`, `ingest`,
> `train` e `write` são comandos futuros. O backend de geração disponível é
> `UnavailableBackend`: ele recusa renderizar em vez de produzir uma imagem que
> apenas pareça manuscrita.

## Em uma frase

O sistema separa três problemas: **conteúdo** (o que escrever), **estilo** (como
a pessoa escreve) e **scan** (como a folha digitalizada parece). Hoje os
contratos de dados e o efeito de scan podem ser exercitados; o estilo gerador
ainda não está implementado.

## Comandos atuais

Instale as dependências com:

```bash
uv sync --dev
```

### `scanify`: imagem de entrada → imagem com efeito de scan

```bash
uv run handwrite scanify entrada.png \
  --preset scanner-escritorio --seed 7 --out saida.png
```

A entrada precisa existir e ser uma imagem. Os presets atuais são
`scanner-escritorio`, `foto-celular`, `xerox-velho` e `limpo`. A `seed` controla
a aleatoriedade para permitir repetição. A saída pode ser PNG, JPG/JPEG ou PDF.
O módulo não aprende letra, não chama rede e não altera a imagem de entrada.

### `coverage`: arquivo Python → relatório JSON

```bash
uv run handwrite coverage exemplo.py --out coverage.json
```

O comando lê o arquivo Python indicado e mede caracteres, tokens e operadores
observados. Ele não cria amostras nem treina um modelo.

### `source-pair`: imagem + `source.py` + regiões → manifesto JSONL

```bash
uv run handwrite source-pair pagina.png source.py regions.json \
  --owner-consent --out dataset/index.jsonl
```

A imagem e o `source.py` precisam existir. O `source.py` deve ter sintaxe Python
válida. O JSON de regiões pode ser um objeto com listas `regions` e `texts`:

```json
{
  "regions": [
    {"x": 10, "y": 20, "width": 300, "height": 40, "line_index": 0}
  ],
  "texts": ["print('oi')"]
}
```

As listas precisam ter o mesmo tamanho. O comando não faz OCR, não descobre as
regiões e não copia o conteúdo das imagens para o manifesto. `--owner-consent`
é obrigatório porque os dados devem ser do próprio titular.

## O pipeline, com o estado de cada etapa

### 1. Coleta de amostras — **futura**

A ideia é fornecer uma folha-modelo com letras, números, acentos, pontuação e
palavras. `handwrite template` ainda não está implementado. Por enquanto, a
entrada real precisa ser preparada fora do CLI, ou fornecida pelo usuário para
os comandos atuais.

### 2. Normalização e segmentação — **contrato definido; CLI completa futura**

O projeto define páginas e regiões em coordenadas de pixels e tem componentes
determinísticos de imagem. A ingestão automática da folha (`handwrite ingest`),
com correção de perspectiva, binarização e recorte das células, ainda é futura.
`source-pair` recebe regiões prontas; não substitui essa ingestão.

### 3. Associação entre imagem e texto — **parcialmente implementada**

`source-pair` implementa o caminho confiável para pares imagem + `source.py`:
valida o Python, calcula o hash SHA-256 do arquivo-fonte e cria registros GOLD a
partir das regiões e textos fornecidos. Um adaptador VLM para casos sem texto
conhecido é contrato futuro; suas respostas não podem entrar automaticamente
como dados confiáveis.

### 4. Manifesto do dataset — **implementada**

O manifesto é JSONL: uma linha por região. O registro real é um `ManifestEntry`
com `sample_id`, `page`, `region`, `text`, `confidence` e `provenance`; `tier` é
derivado da confiança e também aparece na serialização. Um exemplo compatível
com o schema atual:

```json
{
  "sample_id": "pagina-01-line-0",
  "page": {
    "page_id": "pagina-01",
    "source_path": "samples/pagina-01.png",
    "width": 1600,
    "height": 1200,
    "dpi": null,
    "provenance": {
      "method": "source-pair-gold",
      "source_path": "exercicios/aula-01.py",
      "source_sha256": "<hash calculado do arquivo>",
      "owner_consent": "true"
    }
  },
  "region": {
    "x": 10,
    "y": 20,
    "width": 300,
    "height": 40,
    "line_index": 0
  },
  "text": "print('oi')",
  "confidence": 1.0,
  "tier": "gold",
  "provenance": {
    "method": "source-pair-gold",
    "source_path": "exercicios/aula-01.py",
    "source_sha256": "<hash calculado do arquivo>",
    "owner_consent": "true"
  }
}
```

`<hash calculado do arquivo>` é um marcador explicativo, não um valor para
copiar literalmente. O programa calcula o valor real. `confidence` entre 0,90 e
1,0 é `gold`; entre 0,60 e 0,89 é `silver`; abaixo disso é `quarantine`.
Registros em quarentena são excluídos da leitura normal do manifesto.

### 5. Cobertura e captura — **parcialmente implementada**

`coverage` mede o texto que já foi observado. A seleção de novos trechos para
preencher lacunas existe como lógica de cobertura, mas ainda não há um fluxo
completo que imprima uma nova folha e a envie para ingestão. Essa captura
adaptativa é uma ação futura de produto.

### 6. StylePack — **contrato implementado; criação utilizável futura**

O contrato do `StylePack` exige dataset identificado, hash, cobertura, preset de
scan e consentimento do proprietário. Ele protege contra caminhos inválidos,
amostras sem consentimento e dados marcados como assinatura. O comando `train`
que montaria um StylePack a partir de dados reais ainda não existe.

### 7. Geração — **futura**

`GlyphBank` é o plano para a primeira geração por variantes de glifos. Ele ainda
não deve ser descrito como funcional. A geração neural é uma etapa posterior e
opcional, fora do caminho offline padrão.

O contrato de backend recebe texto, `StylePack`, `seed` e quantidade de
candidatos. Hoje `UnavailableBackend` declara `available=false` e
`renders_handwriting=false`. Ao receber uma solicitação válida, lança
`BackendUnavailableError` com a mensagem de que nenhum texto foi renderizado.
Isso é deliberado: uma fonte do sistema não é tratada como manuscrito
personalizado.

### 8. Layout — **contrato futuro para a saída gerada**

O layout deverá cuidar de A4, margens, quebras, recuos e pauta, separado do
backend de estilo. Os módulos e critérios estão descritos no plano, mas o
comando `write` que conecta geração, layout e exportação ainda não está pronto.

### 9. Efeito de scan — **implementada como módulo independente**

`scanify` aplica densidade/espalhamento de tinta, papel, geometria, iluminação,
ruído, curva de tons e JPEG conforme o preset. É uma transformação de uma
imagem já existente; não cria letra nem decide texto. Pode ser testada antes da
geração personalizada.

### 10. Exportação — **parcialmente implementada**

O exportador escreve PNG/PDF e preserva `generator=manual-handwrite-ia` nos
formatos suportados. A exportação de uma página manuscrita completa aguarda o
backend real e o comando `write`; `scanify` já pode produzir arquivos de saída.

## O que é IA e o que não é

As operações atuais — validação de Python, hash, manifesto, cobertura e
`scanify` — seguem regras reproduzíveis. Um VLM poderá sugerir transcrições no
futuro, mas terá de produzir JSON válido, passar por verificações independentes
e enviar dúvidas para `quarantine`. Um modelo neural de estilo só será avaliado
após uma baseline determinística medida.

Nenhum módulo do caminho padrão faz chamadas de rede. Qualquer download de
pesos ou integração externa deverá ser uma ação explícita e documentada.

## Ações atuais e ações futuras

| Ação | Estado | Entrada principal | Saída/efeito |
|---|---|---|---|
| `handwrite scanify` | atual | imagem | imagem com preset de scan |
| `handwrite coverage` | atual | `.py` | relatório JSON |
| `handwrite source-pair` | atual | imagem, `.py`, regiões/textos | manifesto GOLD JSONL |
| `handwrite template` | futura | opções da folha | PDF-modelo |
| `handwrite ingest` | futura | folha preenchida | regiões rotuladas |
| `handwrite train` | futura | dataset consentido | `StylePack` |
| `handwrite write` | futura | texto + `StylePack` | PNG/PDF manuscrito |
| backend `GlyphBank` | futuro | dataset de glifos | candidatos manuscritos |
| backend neural | futuro | dataset + extra `[neural]` | candidatos condicionados |

## Trilha de aprendizado

Os quatro guias didáticos permanecem como portas de entrada, nesta ordem:

1. [Coleta, ingestão e dataset](guias/01-coleta-ingestao-dataset.md): dados,
   rótulos, proveniência e cobertura;
2. [StylePack, GlyphBank e geração](guias/02-estilo-geracao-layout.md):
   representação, candidatos, avaliação e layout;
3. [Scan, exportação e segurança](guias/03-scan-exportacao-seguranca.md):
   imagens, transformações, ruído e reprodutibilidade;
4. [Fundamentos de ML e matérias relacionadas](guias/04-fundamentos-ml-e-materias.md):
   ML, álgebra linear, probabilidade, estatística e redes neurais.

## Segurança e privacidade

- Só amostras do próprio usuário, com `owner_consent=true`, podem formar estilo.
- Assinaturas são recusadas.
- `samples/`, `dataset/`, `styles/`, `models/` e `output/` são dados locais e
  não devem ser commitados.
- Arquivos exportados mantêm o metadado do gerador.
- O resultado deve permitir rastrear texto, amostras, backend e transformações.

## Glossário

**Proveniência** — informações que registram de onde veio uma amostra: página,
arquivo-fonte, método, hash e consentimento. Permite auditar um recorte.

**Seed** — número usado para inicializar a aleatoriedade. A mesma entrada,
preset e seed permitem repetir uma transformação como `scanify`.

**Tier** — faixa de confiança do registro: `gold`, `silver` ou `quarantine`.
`gold` é a faixa mais confiável; `quarantine` não entra no dataset elegível.

**Baseline** — referência simples e mensurável usada para comparação. Neste
projeto, regras determinísticas como `scanify` e fidelidade textual servem de
baseline antes de comparar um modelo neural.

**Dataset** — conjunto de registros e arquivos relacionados usados para análise
ou treino. Cada registro deve manter imagem, texto, região e proveniência.

**StylePack** — pacote versionado que aponta para um dataset consentido e
resume o estilo; não é uma fonte instalada nem um gerador por si só.

**Backend** — implementação que atende ao contrato de geração. Um backend pode
estar indisponível; nesse caso deve falhar explicitamente.

**GlyphBank** — backend planejado que escolheria variantes reais de glifos e
aplicaria pequenas variações. Ainda é futuro.

## Verificação local

Os gates do repositório são:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

Eles verificam contratos e determinismo, não provam que uma futura geração
parece com a letra do titular. Essa qualidade exigirá páginas reais mantidas fora
do treino e avaliação humana.
