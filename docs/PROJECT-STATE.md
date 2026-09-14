---
type: project-state
status: phase-0
summary: Repositório criado com documentação completa e esqueleto Python (CLI handwrite --version, 1 teste smoke). Nenhuma funcionalidade de geração ainda.
---

# Estado do projeto

## Objetivo

Aprender a letra do usuário a partir de amostras escaneadas e gerar manuscritos
novos nessa letra, com aspecto opcional de documento escaneado.

## Concluído

- Fase 0: README, AGENTS.md, llms.txt, docs/, plano em `.hermes/plans/`,
  `pyproject.toml` (uv), CLI mínima, teste smoke, CI (Ubuntu + Windows).

## Fase atual

Fase 1 — **efeito de scan**. Vem primeiro porque é independente do modelo de
letra e já dá resultado visível (ver `docs/IMPLEMENTATION-PLAN.md`).

## Próximo teste concreto

`tests/test_scan_effect.py::test_scanify_is_deterministic_for_seed`: dada uma
imagem sintética (texto preto em fundo branco) e `seed=42`, `scanify()` com o
preset `scanner-escritorio` retorna imagem idêntica em duas execuções e
diferente com `seed=43`.

## Bloqueios / decisões pendentes

- Nenhum bloqueio técnico.
- Para a Fase 2 o usuário precisa imprimir, preencher e escanear a folha-modelo
  (ver `docs/DATA-COLLECTION.md`).

## Última verificação

Ver o commit inicial: `uv run pytest -q` e `uv run ruff check .` verdes.
