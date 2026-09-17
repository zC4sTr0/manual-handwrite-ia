# Plano de implementação v1

Cada fase deve terminar com os gates definidos no repositório:
`uv run pytest -q`, `uv run ruff check .` e `uv run ruff format --check .`,
além da atualização factual de [`docs/PROJECT-STATE.md`](../../docs/PROJECT-STATE.md).
O plano distingue o núcleo já existente das entregas futuras; presença de um
contrato não significa que exista um backend ou uma CLI para executá-lo.

## Fase 0 — Esqueleto (concluída)

- `pyproject.toml`/uv, pacote em `src/manual_handwrite/`, CLI/versionamento,
  testes, CI e documentação inicial.

## Fase 1 — Núcleo offline existente (implementado e verificado)

Esta fase não é uma lista de arquivos a criar. O núcleo atual já inclui:

- `src/manual_handwrite/scan/scanify`, com Pillow, `random.Random`, seed
  determinística, preservação da entrada e os presets
  `scanner-escritorio`, `foto-celular`, `xerox-velho` e `limpo`;
- `src/manual_handwrite/ingest/`, com `normalize_page` e `segment_lines`;
- `src/manual_handwrite/data/`, com metadados de página, regiões, proveniência,
  tiers Gold/Silver/Quarantine, manifesto JSONL e `source_pair` com
  `owner_consent`;
- `src/manual_handwrite/coverage/`, com análise de caracteres/tokens/
  operadores e seleção gulosa de snippets;
- `src/manual_handwrite/style/`, com contrato de `StylePack`, hash, referências
  relativas, cobertura e consentimento, além de extração conservadora de
  glifos críticos;
- `src/manual_handwrite/layout/`, com `PageSpec`, wrapping medido e layout de
  linhas A4;
- `src/manual_handwrite/export.py`, com PNG/PDF e metadado obrigatório;
- contratos locais de avaliação, relatórios e validação do protocolo VLM;
- `src/manual_handwrite/generation/`, que expõe a fronteira de backend e falha
  explicitamente com `UnavailableBackend` em vez de fingir manuscrito.

A CLI efetivamente disponível é:

```text
handwrite scanify IN --preset PRESET --seed N --out OUT
handwrite coverage IN.py --out REPORT.json
handwrite source-pair IMAGE SOURCE.py REGIONS.json --out MANIFEST.jsonl --owner-consent
```

O núcleo foi exercitado com fixtures sintéticas e os gates registrados em
`docs/PROJECT-STATE.md`. Ainda falta a primeira ingestão real do proprietário;
isso não deve ser transformado em dado de teste ou commit.

### Lacunas da Fase 1 (não confundir com implementação)

- O simulador não tem oito estágios independentes; perspectiva, curvatura,
  ondulação e outras propriedades fotográficas permanecem futuras.
- SSIM mínimo, OCR/legibilidade calibrada e o limite de 98% de branco puro são
  critérios ainda não verificados. Eles não são resultados atuais.
- Não há integração de captura ativa com páginas reais, nem adaptador VLM ou
  treinamento. O schema VLM existente só valida respostas locais.

## Fase 2 — Coleta e ingestão orientada por template (futura)

- Criar `template.py` para gerar folha A4 com marcadores/grade e conteúdo
  definido pelo contrato de coleta; hoje esse arquivo não existe.
- Evoluir a ingestão para detectar marcadores, corrigir perspectiva, binarizar
  células, recortar e rotular automaticamente. A segmentação atual só detecta
  faixas horizontais e o `source-pair` recebe regiões/textos do chamador.
- Se for necessário um contrato dedicado de glifos, criar `dataset.py` com
  schema explícito; `data/` atual é um manifesto de páginas/linhas, não esse
  dataset.
- Se a política crescer além das validações atuais, extrair `safety.py`; hoje
  consentimento e recusa de assinatura vivem em `data/source_pair.py` e
  `style/stylepack.py`.
- Aceite futuro: fixture sintética com taxa de rótulo correta definida e
  medida. A meta de 95% ainda não foi implementada nem verificada.

## Fase 3 — Síntese v1 por glifos e composição (futura)

- Implementar um backend real de glifos, com variantes, jitter, escala,
  espaçamento e conexões; `style/glyphs.py` atual não é um `GlyphBank` e só
  extrai glifos críticos de linhas alinhadas.
- Criar a composição de página (possivelmente `compose.py`) sobre as primitivas
  de `layout/`; `compose_page` não existe hoje.
- Implementar exportação integrada e uma CLI `handwrite write`; a CLI atual não
  tem o comando `write`.
- Aceites futuros: página A4 com 1.000 caracteres em menos de 5 s na CPU,
  nenhuma palavra fora da margem e metadados presentes. O último item já é
  coberto pela exportação existente; desempenho e renderização ainda não.

## Fase 4 — Qualidade percebida (futura)

- Comparação cega entre páginas reais e geradas, incluindo a degradação de
  scan, com protocolo definido antes da coleta.
- Ajuste de parâmetros por estilo em manifesto/arquivo de configuração.
- Medir estilo e qualidade visual com evidência; os relatórios atuais marcam
  essas métricas como indisponíveis.

## Fase 5 — Modelo neural opcional (futura)

- Escolher e implementar um adaptador few-shot conforme
  [`docs/RESEARCH.md`](../../docs/RESEARCH.md), em extra opcional `[neural]`,
  sempre sob comando explícito e sem rede no caminho padrão.
- Criar `src/manual_handwrite/style/neural.py` somente quando houver um
  contrato e backend reais; esse caminho ainda não existe.
- Prever fallback para glifos apenas depois que o backend de glifos existir.
- Aceite futuro: preferência do usuário igual ou maior que a v1 em teste cego.
  Esse resultado não foi medido.

## Referências de execução e segurança

- Estado atual: [`docs/PROJECT-STATE.md`](../../docs/PROJECT-STATE.md).
- Coleta de amostras: [`docs/DATA-COLLECTION.md`](../../docs/DATA-COLLECTION.md).
- Privacidade e consentimento: [`docs/ETHICS-AND-PRIVACY.md`](../../docs/ETHICS-AND-PRIVACY.md).
- Arquitetura reconciliada: [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
- Scan e critérios ainda não verificados: [`docs/SCAN-EFFECT.md`](../../docs/SCAN-EFFECT.md).
