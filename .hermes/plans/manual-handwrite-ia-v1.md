# Plano de implementação

Cada fase termina com gates verdes (`pytest`, `ruff check`, `ruff format --check`)
e `docs/PROJECT-STATE.md` atualizado.

## Fase 0 — Esqueleto (concluída)

- pyproject (uv), CLI `handwrite --version`, teste smoke, CI, documentação.

## Fase 1 — Efeito de scan (independente do modelo)

- `scan_effect/` com estágios `ink_density`, `ink_bleed`, `paper_texture`,
  `geometry` (rotação até 1.5 graus, leve perspectiva, curvatura opcional),
  `lighting` (vinheta, gradiente, sombra de borda), `sensor_noise`,
  `tone_curve` (preto e branco não puros) e `jpeg`.
- Presets: `scanner-escritorio`, `foto-celular`, `xerox-velho`, `limpo`.
- CLI: `handwrite scanify in.png --preset foto-celular --seed 7 --out out.jpg`.
- Aceite: determinístico por seed; legibilidade preservada (SSIM mínimo contra
  a entrada binarizada, OCR opcional); nenhum preset deixa mais de 98% dos
  pixels em branco puro.

## Fase 2 — Coleta e ingestão

- `handwrite template` gera PDF A4 com marcadores ArUco e grade: a-z, A-Z, 0-9,
  vogais acentuadas e ç (minúsculas e maiúsculas), pontuação comum, R$ e %,
  3 variantes por caractere e 40 palavras frequentes do português (ligaduras).
- `handwrite ingest` corrige perspectiva, binariza, recorta e rotula.
- `safety.py`: `style.toml` exige `owner_consent = true`.
- Aceite: com uma folha sintética gerada nos testes, a ingestão recupera pelo
  menos 95% das células com o rótulo correto.

## Fase 3 — v1 síntese por glifos

- `GlyphBank`: variante aleatória sem repetição consecutiva, jitter de baseline,
  inclinação, escala (cerca de 4%), espaçamento de letras e palavras, conexão
  simples entre letras cursivas.
- `compose_page` + `export` (PNG/PDF com metadado).
- CLI `handwrite write`.
- Aceite: página A4 com 1.000 caracteres em menos de 5 s na CPU; nenhuma palavra
  cruza a margem; metadados presentes.

## Fase 4 — Qualidade percebida

- Teste cego do usuário: páginas reais vs. geradas (com scan).
- Ajuste de parâmetros por estilo em `style.toml`.

## Fase 5 — v2 modelo neural (extra `[neural]`)

- Escolher base few-shot (ver `docs/RESEARCH.md`) e afinar com o dataset pessoal
  em GPU local ou nuvem, sempre sob comando explícito.
- Fallback para `GlyphBank` em caracteres com pouca cobertura.
- Aceite: preferência do usuário igual ou maior que a v1 em teste cego.
