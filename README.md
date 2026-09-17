# manual-handwrite-ia

Ferramenta local para estudar e, no futuro, gerar manuscritos na **sua própria
letra** a partir de amostras consentidas. O projeto não gera assinaturas nem
imita a letra de terceiros.

> **Estado atual — Fase 1 (base de scan + Data Factory).** O núcleo offline já
> tem três caminhos de CLI executáveis: `scanify`, `coverage` e `source-pair`.
> Ainda não há geração personalizada de manuscritos: `template`, `ingest`,
> `train` e `write` são comandos planejados. Para testar os caminhos atuais,
> você precisa fornecer seus próprios arquivos de entrada; o repositório não
> contém páginas reais do proprietário.

O estado técnico detalhado está em [`docs/PROJECT-STATE.md`](docs/PROJECT-STATE.md).

## Comece pelo que funciona hoje

Requisitos: Python 3.11+ e [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync --dev
```

### 1. Aplicar aparência de documento escaneado

`scanify` recebe uma imagem existente e grava outra. O arquivo de entrada deve
ser uma imagem legível (`.png`, `.jpg` ou `.jpeg`).

```bash
uv run handwrite scanify entrada.png \
  --preset scanner-escritorio --seed 7 --out saida.png
```

Presets disponíveis no núcleo atual: `scanner-escritorio`, `foto-celular`,
`xerox-velho` e `limpo`. A `seed` torna o resultado reproduzível.

### 2. Medir cobertura de um arquivo Python

`coverage` lê um arquivo `.py` que você fornecer e grava um relatório JSON.

```bash
uv run handwrite coverage exemplo.py --out coverage.json
```

### 3. Criar registros GOLD a partir de imagem + `source.py`

`source-pair` exige uma imagem de página, o `source.py` correspondente e um
JSON com regiões e textos. As regiões são fornecidas pelo chamador; este
comando não faz OCR nem segmenta a imagem automaticamente. Também exige a
confirmação explícita de que a amostra é do proprietário.

```bash
uv run handwrite source-pair pagina.png source.py regions.json \
  --owner-consent --out dataset/index.jsonl
```

O JSON de regiões pode ter o formato `{"regions": [...], "texts": [...]}`.
Cada região usa `x`, `y`, `width`, `height` e `line_index`. Consulte o contrato
em [`docs/COMO-FUNCIONA.md`](docs/COMO-FUNCIONA.md) antes de montar os dados.

Esses comandos são determinísticos/offline e não enviam amostras para a rede.
Para uma verificação local completa:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

## O que está planejado, mas ainda não executa

Os comandos abaixo descrevem a direção do produto, não um tutorial executável
hoje:

```bash
# futuro: criar a folha-modelo
uv run handwrite template --out folha-modelo.pdf
# futuro: ingerir/segmentar a folha preenchida
uv run handwrite ingest samples/folha-01.jpg
# futuro: montar um StylePack
uv run handwrite train --style minha-letra
# futuro: gerar e exportar manuscrito
uv run handwrite write "Uma anotação" --style minha-letra \
  --scan-preset scanner-escritorio --out anotacao.pdf
```

A geração depende de um backend de escrita e de dados reais do proprietário.
O backend atual recusa a operação com `UnavailableBackend`; ele não finge que
uma fonte do sistema é manuscrito personalizado. `GlyphBank` e geração neural
continuam no roadmap.

## O que o projeto fará quando essas fases existirem

1. coletar amostras naturais em uma folha-modelo;
2. normalizar e segmentar as páginas;
3. associar imagem, texto, região e proveniência em um dataset pessoal;
4. montar um pacote de estilo consentido;
5. gerar candidatos manuscritos;
6. compor páginas e aplicar o efeito opcional de scan;
7. exportar PNG/PDF com `generator=manual-handwrite-ia`.

As etapas 1–3 têm contratos e partes determinísticas já implementados; a
criação da folha, a ingestão completa e a geração ainda são trabalho futuro.

## Limites de uso e privacidade

- O caminho padrão é local e não faz chamadas de rede.
- Amostras reais, datasets derivados, estilos, pesos e saídas ficam fora do Git.
- O dataset só aceita amostras declaradas como pertencentes ao próprio usuário.
- Assinaturas são recusadas por design.
- Arquivos exportados mantêm o metadado `generator=manual-handwrite-ia`.

Leia [`docs/ETHICS-AND-PRIVACY.md`](docs/ETHICS-AND-PRIVACY.md) antes de usar
amostras reais.

## Documentação

| Documento | Conteúdo |
|---|---|
| [Como funciona](docs/COMO-FUNCIONA.md) | Pipeline, estado e contratos em linguagem direta |
| [Estado do projeto](docs/PROJECT-STATE.md) | Fase atual, verificações e bloqueios |
| [Arquitetura](docs/ARCHITECTURE.md) | Módulos e fronteiras do sistema |
| [Plano de implementação](docs/IMPLEMENTATION-PLAN.md) | Fases e critérios de aceite |
| [Coleta de dados](docs/DATA-COLLECTION.md) | Como preparar amostras reais |
| [Efeito de scan](docs/SCAN-EFFECT.md) | Degradação de imagem |
| [Pesquisa](docs/RESEARCH.md) | Estado da arte e hipóteses |
| [Ética e privacidade](docs/ETHICS-AND-PRIVACY.md) | Limites de uso |
| [Roadmap](docs/ROADMAP.md) | O que fica para depois |

A trilha didática continua nos quatro guias:

1. [Coleta, ingestão e dataset](docs/guias/01-coleta-ingestao-dataset.md)
2. [StylePack, GlyphBank e geração](docs/guias/02-estilo-geracao-layout.md)
3. [Scan, exportação e segurança](docs/guias/03-scan-exportacao-seguranca.md)
4. [Fundamentos de ML e matérias relacionadas](docs/guias/04-fundamentos-ml-e-materias.md)

## Desenvolvimento

- Python 3.11+, `uv`, `pytest` e `ruff`.
- Gates: `uv run pytest -q`, `uv run ruff check .` e `uv run ruff format --check .`.
- Não comite amostras reais nem dados gerados.
