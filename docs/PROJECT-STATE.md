---
type: project-state
status: phase-1-ready-for-data
summary: Núcleo offline da Fase 1 está funcional e verificado. O sistema já normaliza/segmenta páginas, cria manifests confiáveis, mede cobertura, seleciona captura adaptativa, aceita pares GOLD image+source.py, protege StylePack, valida o protocolo VLM, mede fidelidade textual, compõe A4, exporta PNG/PDF e simula scan. A documentação ganhou quatro guias didáticos, incluindo fundamentos de ML e matérias relacionadas. Não há páginas reais do proprietário no repositório; portanto VLM, StylePack real, benchmark neural e geração personalizada ainda não podem ser executados honestamente.
---

# Estado do projeto

## Objetivo

Aprender a letra do usuário a partir de amostras escaneadas e gerar manuscritos
novos nessa letra, com aspecto opcional de documento escaneado.

## Concluído

- Fase 0: README, AGENTS.md, llms.txt, docs/, plano em `.hermes/plans/`,
  `pyproject.toml` (uv), CLI mínima, teste smoke, CI (Ubuntu + Windows).
- Scan simulator em `src/manual_handwrite/scan/scanify`, com presets locais,
  seed determinística e preservação da entrada.
- Contratos da Data Factory em `src/manual_handwrite/data/`: página, região,
  proveniência, tiers Gold/Silver/Quarantine e manifesto JSONL.
- Analisador de cobertura de caracteres, tokens e operadores Python em
  `src/manual_handwrite/coverage/`.
- Relatório de landscape em `docs/research/2026-model-landscape.md` e protocolo
  `docs/experiments/EXP-001.md`; fatos, hipóteses e unknowns estão separados.
- Trilha prática em `docs/learning/`, conectada aos módulos implementados.
- Guias de onboarding em `docs/guias/`: coleta/dataset, estilo/geração/layout,
  scan/segurança e fundamentos de ML/matérias relacionadas.

## Fase atual

Fase 1 — **base de scan + Data Factory**. O simulator já está implementado;
  ingestão/segmentação e adaptador VLM continuam pendentes.

## Próximo teste concreto

`uv run pytest -q && uv run ruff check . && uv run ruff format --check .`:
  88 testes passaram; Ruff check e format check passaram.

## Bloqueios / decisões pendentes

- Nenhum bloqueio técnico no núcleo offline.
- Para validar a primeira ingestão real, o usuário precisa fornecer páginas
  naturais de código Python do próprio titular (ver `docs/DATA-COLLECTION.md`).
- Os backends VLM e neurais permanecem explicitamente sem rede no caminho padrão;
  nenhum benchmark de modelo foi executado ainda.

## Última verificação

Verificação atual: `uv run pytest -q` → 88 passed; `uv run ruff check .` →
All checks passed; `uv run ruff format --check .` → 60 files already formatted;
`git diff --check` → sem erros. Smoke E2E sintético → `E2E_PASS`, gerou PNG limpo,
PNG simulado e PDF em diretório temporário, com `generator=manual-handwrite-ia`
confirmado nos PNGs. Smoke CLI → `CLI_E2E_PASS`, executou `scanify` e `coverage`.
Smoke GOLD CLI → `GOLD_CLI_E2E_PASS`, executou `source-pair` e produziu manifesto
JSONL com dois registros Gold em diretório aninhado temporário.
