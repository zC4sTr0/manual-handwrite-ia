# Guia 03 — Scan, exportação, segurança e glossário

Este guia mostra como transformar uma imagem em uma versão com aparência de
folha escaneada ou fotografada e como exportá-la com procedência identificável.
Ele também explica os limites de segurança do projeto para quem está começando.

> **Escopo atual:** na Fase 1, o caminho funcional da CLI é `scanify`. Os
> comandos `template`, `ingest`, `train` e `write` aparecem no plano do produto,
> mas ainda são etapas futuras. Não trate esses exemplos futuros como comandos
> disponíveis hoje.

## 1. O mapa mental: conteúdo, estilo e scan

O pipeline tem três responsabilidades diferentes:

```text
conteúdo = o que será escrito
estilo   = como a letra do titular costuma ser
scan     = como a folha pronta parece depois de escaneada ou fotografada
```

O simulador de scan **não aprende letra**, não transcreve texto e não decide o
layout. Ele recebe uma imagem já pronta e devolve outra imagem. Isso é útil para
depurar: se o texto ou a letra estiverem errados antes do scan, trocar o preset
não corrige a causa.

A função pública usada pelo módulo é `manual_handwrite.scan.scanify`. Ela aceita
uma imagem Pillow (ou um array NumPy quando essas dependências estão disponíveis),
um `seed` inteiro e um preset. A entrada não é alterada; a saída mantém as
dimensões da imagem.

## 2. O que é uma imagem limpa?

**Imagem limpa** é a representação da página antes de simular imperfeições de
scanner, câmera ou xerox. Em geral, ela tem fundo e tinta mais uniformes, pouca
textura, geometria alinhada e não contém os defeitos que o simulador adiciona.
Ela não precisa ser literalmente branca nem perfeita: “limpa” significa que a
aparência de digitalização ainda não foi aplicada.

Exemplo conceitual:

```text
imagem limpa → scanify(preset, seed) → imagem com aparência de scan
```

A separação permite comparar duas coisas:

- **letra/layout:** avalie a imagem limpa;
- **naturalidade da digitalização:** avalie a saída do simulador.

O simulador v1 trabalha em tons de cinza durante o processamento e pode
preservar o canal alfa da imagem original. A saída mantém o modo apropriado para
imagens `L`, `RGB`, `RGBA` e alguns outros modos Pillow, conforme o caso.

## 3. O que é um preset?

Um **preset** é um conjunto nomeado de parâmetros que descreve uma situação de
captura. Em vez de escolher cada imperfeição manualmente, você escolhe um nome.
Os quatro presets disponíveis são:

| Preset | Aparência pretendida | Características principais |
|---|---|---|
| `scanner-escritorio` | Scanner de escritório | Pequena rotação, luz relativamente uniforme, papel levemente cinza e JPEG 85. É o padrão da CLI. |
| `foto-celular` | Foto feita com celular | Perspectiva e rotação mais visíveis, vinheta e ruído maiores, JPEG 75. |
| `xerox-velho` | Cópia xerográfica antiga | Mais contraste, textura/ruído e bordas mais escuras, JPEG 65. |
| `limpo` | Letra com pouca degradação | Só efeitos leves de densidade da tinta e espalhamento; sem rotação, vinheta ou compressão JPEG no simulador. |

Os nomes precisam ser escritos exatamente como acima. Um nome desconhecido gera
`ValueError`; não existe fallback silencioso para outro preset.

Internamente, os estágios previstos no efeito de scan são: densidade da tinta,
espalhamento (`bleed`), textura do papel, geometria, iluminação, ruído do
sensor, curva de tons e compressão JPEG. A implementação v1 realiza uma
simulação local determinística desses efeitos com Pillow; o desenho documentado
do pipeline também usa os conceitos de textura, vinheta e ruído para explicar a
aparência esperada.

## 4. O que é seed?

A **seed** (semente) é um número inteiro usado para inicializar a aleatoriedade
do efeito. Ela torna uma execução reproduzível:

```bash
uv run handwrite scanify pagina.png --preset scanner-escritorio --seed 42 --out pagina-scan.png
uv run handwrite scanify pagina.png --preset scanner-escritorio --seed 42 --out pagina-scan-2.png
```

Com a mesma imagem, preset e `seed`, as saídas devem ser iguais. Com outra seed,
a variação determinística pode ser diferente. A seed não é uma senha, não protege
o arquivo e não substitui controle de acesso.

Use uma seed fixa quando estiver comparando presets ou depurando. Use seeds
diferentes quando quiser produzir variações controladas para avaliação. A CLI
exige `--seed` como inteiro; se omitido, o valor padrão é `0`.

## 5. Comando real: `scanify`

A instalação declara o executável `handwrite` como entrada de
`manual_handwrite.cli:main`. Na raiz do repositório, um exemplo completo é:

```bash
uv run handwrite scanify entrada.png \
  --preset scanner-escritorio \
  --seed 42 \
  --out output/entrada-scan.png
```

O diretório-pai da saída é criado pela CLI quando necessário. A extensão da
saída precisa ser `.png`, `.pdf`, `.jpg` ou `.jpeg`:

```bash
uv run handwrite scanify entrada.png \
  --preset foto-celular \
  --seed 7 \
  --out output/entrada-celular.jpg

uv run handwrite scanify entrada.png \
  --preset xerox-velho \
  --seed 13 \
  --out output/entrada-xerox.pdf
```

Para o fluxo de PNG e PDF, a CLI chama `manual_handwrite.export.export_image`.
JPEG é salvo diretamente pela CLI, com um comentário de procedência. A API de
exportação `export_image` aceita apenas os formatos `png` e `pdf`; quando o
formato não é informado, ele é obtido pela extensão do destino.

### Uso direto em Python

Quando já existe uma imagem Pillow, a API pode ser usada sem a CLI:

```python
from PIL import Image

from manual_handwrite.export import export_image
from manual_handwrite.scan import scanify

with Image.open("entrada.png") as imagem:
    simulada = scanify(imagem, seed=42, preset="scanner-escritorio")

export_image(simulada, "output/entrada-scan.png")
export_image(simulada, "output/entrada-scan.pdf")
```

Não passe um preset inventado e não presuma que a API aceite parâmetros que não
estão neste guia. O contrato atual é `scanify(image, seed, preset=...)`.

## 6. Exportação PNG e PDF

### PNG

`export_png` salva a imagem como PNG e escreve os metadados textuais fornecidos.
Mesmo que o chamador tente substituir esse valor, o módulo sempre grava:

```text
generator=manual-handwrite-ia
```

Esse campo fica no bloco tEXt do PNG. Metadados adicionais, como `author`,
podem ser enviados pela API:

```python
from PIL import Image
from manual_handwrite.export import export_png

export_png(
    Image.new("RGB", (200, 100), "white"),
    "output/exemplo.png",
    metadata={"author": "titular", "subject": "estudo"},
)
```

### PDF

`export_pdf` grava um PDF de uma página, com resolução configurada em 300 dpi.
A imagem é convertida para RGB quando necessário. O campo PDF `Producer` recebe
`manual-handwrite-ia`; campos opcionais reconhecidos pelo exportador incluem
`title`, `author`, `subject`, `keywords` e `creator`.

```python
from PIL import Image
from manual_handwrite.export import export_pdf

export_pdf(
    Image.open("output/entrada-scan.png"),
    "output/entrada-scan.pdf",
    metadata={"title": "Página de estudo", "author": "titular"},
)
```

Feche a imagem aberta com `with Image.open(...)` em código de produção. O
metadado `generator` é obrigatório e não deve ser removido, mesmo ao editar o
arquivo em outro programa. Exportações não são prova de autenticidade do
conteúdo: o campo apenas registra a origem do gerador.

## 7. Consentimento e segurança

A letra manuscrita é dado pessoal sensível para este caso porque pode ser usada
para fraude. O projeto foi desenhado para uso na letra do próprio titular.

### Consentimento do proprietário

`owner_consent` significa uma confirmação explícita de que as amostras pertencem
ao proprietário que autorizou o uso. No comando funcional `source-pair`, a
confirmação é obrigatória:

```bash
uv run handwrite source-pair pagina.png source.py regions.json \
  --out dataset/gold.jsonl \
  --owner-consent
```

Sem `--owner-consent`, o parser recusa a operação e não deve produzir o
manifesto. No código de ingestão, o valor precisa ser exatamente `True`; valores
como `1` ou texto não substituem a confirmação booleana.

O `source-pair` usa uma imagem, um arquivo-fonte correspondente e um JSON de
regiões. O JSON pode conter `regions` ou `line_regions`, além de `texts`, ou uma
lista de objetos com `region` e `text`. O resultado é um manifesto JSONL GOLD.
Esse comando é uma etapa de ingestão, não uma exportação PNG/PDF.

### Assinatura não faz parte do produto

**Assinatura** ou **rubrica** é uma marca pessoal usada para assinar, autenticar
ou aparentar autoria. Este projeto não gera, não coleta e não treina estilos de
assinatura. Entradas marcadas com chaves como `signature`, `is_signature`,
`signature_marked` ou `is_signature_marked` são recusadas pelo caminho de dados e
pelo carregamento do StylePack.

Não contorne essa proteção renomeando o campo, omitindo a marca ou usando uma
amostra de assinatura sem rótulo. Também não use a ferramenta para criar
contratos, cheques, receitas, atestados, provas ou outros documentos destinados a
enganar terceiros.

### Privacidade operacional

A privacidade operacional depende de manter os dados sob controle local.

- Mantenha `samples/`, `dataset/`, `styles/`, `models/` e `output/` fora do Git.
- Não coloque imagens reais, datasets derivados, pesos ou saídas em logs de CI.
- Testes devem usar fixtures sintéticas.
- O caminho padrão não faz chamadas de rede.
- Qualquer upload externo exige uma opção explícita e documentada; não é uma
  consequência de `scanify` ou de `export_image`.
- Evite incluir nomes, textos pessoais ou caminhos absolutos em relatórios
  compartilhados.

O metadado `generator=manual-handwrite-ia` é uma medida de rastreabilidade, não
um mecanismo de anonimização. Remover EXIF ou outros metadados de origem também
não torna legítimo o uso de uma letra sem consentimento.

## 8. O que já funciona e o que ainda não funciona

### Funciona hoje

- `handwrite --version` e o parser da CLI.
- `handwrite scanify` com os quatro presets listados.
- Seed inteira e resultado determinístico para a mesma entrada, preset e seed.
- Proteção contra mutação da imagem de entrada.
- Exportação PNG e PDF pelo módulo `export.py`.
- Metadado obrigatório em PNG (tEXt) e PDF (Producer).
- `handwrite coverage` para relatório JSON de cobertura de um arquivo Python.
- `handwrite source-pair` com consentimento explícito e manifesto GOLD.
- Recusa de marcadores de assinatura na ingestão e no StylePack.

### Ainda é futuro

Os comandos abaixo são contratos planejados, não caminhos que a CLI atual
implementa:

```bash
uv run handwrite template --out folha-modelo.pdf
uv run handwrite ingest samples/folha-01.jpg
uv run handwrite train --style minha-letra
uv run handwrite write "Uma anotação" \
  --style minha-letra \
  --scan-preset scanner-escritorio \
  --out anotacao.pdf
```

A geração personalizada completa, a coleta automatizada da folha-modelo e o
backend `GlyphBank` ainda não devem ser apresentados como disponíveis apenas
porque aparecem no plano ou na arquitetura.

## 9. Erros comuns e como resolver

### `unknown preset`

Causa: nome digitado diferente do contrato. Use exatamente
`scanner-escritorio`, `foto-celular`, `xerox-velho` ou `limpo`.

### `seed must be an integer`

Causa: a API recebeu um valor que não é inteiro. Na CLI, passe, por exemplo,
`--seed 7`, sem texto adicional. A seed `True` também não deve ser usada como
substituta de um número.

### `output format must be .png, .jpg, .jpeg, or .pdf`

Causa: a CLI não reconhece a extensão do destino. Escolha uma dessas quatro
extensões. Para a API `export_image`, use apenas `png` ou `pdf`.

### `format must be png or pdf`

Causa: `export_image` recebeu outro formato. JPEG é tratado diretamente pelo
caminho específico da CLI, não pelo exportador genérico.

### O PNG não mostra `generator`

Confirme que o arquivo foi produzido por `export_png`/`export_image` e reabra-o
com Pillow:

```bash
uv run python -c "from PIL import Image; im=Image.open('output/entrada-scan.png'); print(im.info.get('generator'))"
```

O resultado esperado é `manual-handwrite-ia`. Não confunda o valor do campo com
o nome do arquivo.

### O PDF parece sem metadado

O PDF usa `Producer`, não tEXt de PNG. Faça uma verificação simples de bytes:

```bash
uv run python -c "from pathlib import Path; b=Path('output/entrada-scan.pdf').read_bytes(); print(b'/Producer' in b, b'manual-handwrite-ia' in b)"
```

Ferramentas PDF podem codificar strings de formas diferentes ao exibir
metadados; a verificação oficial do projeto confirma a presença de `/Producer` e
do identificador do gerador.

### A saída mudou sem mudança aparente no arquivo

Verifique o preset e a seed. A aleatoriedade é determinística por seed, mas
alterar qualquer entrada muda o resultado. Compare também tamanho e modo da
imagem.

### O resultado parece digital demais

Teste `scanner-escritorio` ou `foto-celular` em vez de `limpo`. Se a letra já
estava errada na imagem limpa, o problema está antes de `scanify`; o simulador
não corrige estilo.

### `source-pair` recusa a operação

Confira três pontos: `--owner-consent` está presente; o JSON contém listas
válidas de regiões e textos; e nenhum metadado marca a entrada como assinatura.
Não remova a validação para fazer o comando passar.

## 10. Depuração passo a passo

1. **Isole a entrada:** abra a imagem original e confirme que ela existe e pode
   ser lida pelo Pillow.
2. **Teste o preset mais simples:** execute `limpo` com seed fixa.
3. **Compare determinismo:** rode duas vezes com a mesma seed e depois com uma
   seed diferente.
4. **Separe visual de exportação:** inspecione a imagem retornada por
   `scanify` antes de exportá-la; depois valide o arquivo salvo.
5. **Valide o formato:** use `.png` ou `.pdf` e confira o metadado correspondente.
6. **Reduza o caso:** use uma fixture pequena e sintética para um erro de
   processamento. Não copie uma amostra real para testes ou CI.
7. **Localize a fronteira:** texto errado aponta para conteúdo/transcrição;
   letra errada aponta para estilo; página cortada aponta para layout; aparência
   de scan errada aponta para `scanify`; metadado ausente aponta para exportação.
8. **Execute os gates do repositório:**

   ```bash
   uv run pytest -q
   uv run ruff check .
   uv run ruff format --check .
   ```

Os testes verificam contratos, determinismo, formatos e metadados. Eles não
substituem a avaliação visual de uma página real; essa avaliação deve usar
amostras do titular, separadas do treino, sem colocar os dados no repositório.

## 11. Critérios de aceite

Considere o fluxo de scan e exportação aceito somente quando todos os itens
forem verdadeiros:

- [ ] A entrada é uma imagem válida e a original permanece inalterada.
- [ ] O preset é um dos quatro nomes oficiais.
- [ ] A seed é inteira e foi registrada para reproduzir a execução.
- [ ] A saída conserva as dimensões esperadas da entrada.
- [ ] O PNG abre e contém `generator=manual-handwrite-ia` em seus metadados.
- [ ] O PDF abre, é de uma página no fluxo atual e identifica o gerador como
      `Producer`.
- [ ] O conteúdo da página foi verificado separadamente do efeito de scan.
- [ ] Nenhuma amostra de terceiros ou assinatura foi usada.
- [ ] O consentimento do titular está explícito quando houver ingestão de dados.
- [ ] Dados pessoais, saídas reais e pesos não entram no Git nem em logs.
- [ ] O caminho executado não fez rede inesperada.
- [ ] Os três gates (`pytest`, `ruff check` e `ruff format --check`) passam.

## 12. Glossário

**Imagem limpa** — Imagem da página antes da degradação de scanner/câmera; serve
como referência para julgar letra e layout.

**Scan / digitalização** — Captura de uma folha por scanner, câmera ou xerox.
Neste projeto, o termo também descreve a aparência simulada dessa captura.

**Simulador de scan (`scanify`)** — Função local que transforma uma imagem em uma
cópia com textura, ruído, alterações de tom e, conforme o preset, geometria e
compressão.

**Preset** — Nome de uma configuração pronta do simulador: `scanner-escritorio`,
`foto-celular`, `xerox-velho` ou `limpo`.

**Seed** — Inteiro que controla a aleatoriedade reproduzível de uma execução.

**Exportação** — Gravação do resultado em um arquivo de saída, como PNG ou PDF.

**PNG** — Formato de imagem que, neste projeto, recebe metadados textuais tEXt.

**PDF** — Formato de documento; o exportador atual grava uma página em 300 dpi
e usa o campo `Producer` para a procedência.

**Metadado `generator`** — Campo obrigatório com o valor
`manual-handwrite-ia`. Identifica o programa que gerou o arquivo; não é
assinatura criptográfica nem garantia de autenticidade.

**Producer** — Campo de procedência do PDF usado pelo exportador para registrar o
gerador.

**Consentimento (`owner_consent`)** — Confirmação explícita de que as amostras
são do próprio titular e podem ser usadas no estilo.

**Assinatura / rubrica** — Marca pessoal de autenticação. É proibida no dataset e
recusada pelos validadores do projeto.

**Privacidade** — Práticas para manter letra, imagens, datasets, modelos e
saídas sob controle local, sem Git, CI ou rede não autorizada.

**Dataset** — Conjunto de amostras relacionadas a imagens, texto e proveniência.

**GOLD** — Registro cuja imagem e texto correspondente têm relação conhecida com
alta confiança, como um par `image + source.py` validado.

**SILVER** — Registro plausível, mas com garantia menor que GOLD.

**Quarantine (quarentena)** — Registro duvidoso retirado do treinamento até que
seja revisado ou descartado.

**Glyph (glifo)** — Recorte visual de uma letra ou símbolo.

**GlyphBank** — Backend planejado para escolher variantes de glifos do dataset e
montar escrita; ainda não é a geração personalizada disponível na CLI atual.

**StylePack** — Pacote que referencia um dataset consentido e descreve uma
versão do estilo; não é uma fonte de sistema.

**Proveniência** — Registro de origem e transformações: qual entrada foi usada,
qual preset/seed e qual gerador produziu a saída.

**Backend** — Implementação concreta de uma etapa, como um gerador de estilo.

**VLM** — Modelo que combina visão e linguagem; no projeto, é um auxiliar
opcional para transcrição, nunca autoridade para inventar dados.
