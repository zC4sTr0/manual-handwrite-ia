# 03 — Supervisão fraca e confiança

## Objetivo

Tratar uma hipótese de um modelo de linguagem e visão (VLM) como evidência
incerta, nunca como ground truth. O pipeline precisa saber quando conservar,
marcar ou descartar informação.

## Problema e limite da solução ingênua

Corrigir uma linha inválida com o parser Python seria alucinação: sintaxe sugere,
mas não prova, o que foi escrito visualmente. Do mesmo modo, confiança numérica
sem proveniência não explica de onde veio a decisão.

## Conceito e implementação atual

A validação local combina evidência fornecida, concordância e verificadores
Python como sinais de confiança. O parser ajuda a detectar ambiguidade, mas não
substitui a imagem. Os resultados alimentam tiers e manifests. O esquema VLM
implementado valida JSON recebido; não chama fornecedor, lê fotografia ou faz
rede.

## Micro-experimento executável

Na raiz:

```bash
uv run pytest -q tests/test_coverage.py tests/test_data_factory.py tests/test_vlm_schema.py
```

Saída esperada: `18 passed` (ou mais, se novos testes forem acrescentados; o
critério é zero falhas). Em particular, o caso `if x = 5:` mantém `if`, `x`,
`5` e o caractere `=` observados, mas não inventa `==`; os testes do esquema
recusam passes incompletos, IDs inconsistentes e confiança inválida.

O teste não usa uma fotografia nem simula que uma VLM tenha transcrito algo: ele
exercita apenas contratos locais com payloads e textos sintéticos.

## O que ainda não existe

Não há adaptador VLM executando transcrição visual nem processo automático de
revisão humana. Também não há métrica de fidelidade de estilo. Portanto, passar
os testes demonstra rejeição e rastreabilidade do contrato, não acurácia de um
modelo.
