# 04 — Cobertura como active learning

## Objetivo

Medir o vocabulário realmente observado e escolher uma pequena captura que cubra
lacunas, em vez de coletar páginas aleatórias. *Active learning* (aprendizado
ativo) aqui é uma estratégia de seleção; não é um modelo neural.

## Etapa 0 — preparação

Antes de otimizar, pratique Python básico, matrizes e proporções: uma imagem é
uma matriz de pixels; uma contagem de cobertura é uma tabela; e a pontuação de
um candidato é ganho novo dividido pelo custo (número de caracteres). Você deve
conseguir ler `set`, `dict`, `for`, `len` e divisão antes de interpretar o
algoritmo. Um candidato vazio custa uma unidade para evitar divisão por zero.

## Problema e solução atual

Mais páginas não garantem informação nova. Escolher snippets aleatórios pode
repetir `print` e nunca observar `!=` ou `>=`. `analyze_text` extrai caracteres,
tokens Python e operadores, expondo ausências do vocabulário inicial.

O otimizador guloso de *maximum coverage* (cobertura máxima) **já está
implementado** em `manual_handwrite.coverage.optimizer.optimize_coverage` e é
exportado pelo pacote. Ele seleciona, de forma determinística, o ganho novo por
caractere, respeita `max_snippets`/`max_cost`, preserva a ordem em empates e
omite candidatos sem ganho. Não é uma etapa a adicionar.

## Micro-experimento executável

```bash
uv run pytest -q tests/test_coverage.py tests/test_coverage_optimizer.py
```

Saída esperada: `6 passed` (ou mais com novos testes; zero falhas). Para ver um
relatório real da CLI, ainda sem dado pessoal:

```bash
uv run python -c "from manual_handwrite.coverage import analyze_text; print(analyze_text('for i in range(3):').as_dict())"
```

A saída deve conter evidência para `for`, `in`, `range` e `:` e listas
reprodutíveis de ausências; ela não deve preencher lacunas por frequência.

## O que não afirmar

Overfitting (sobreajuste), viés-variância e embeddings aparecem nesta trilha
apenas como exemplos mentais — analogias de decorar snippets, trocar
complexidade por generalização e representar itens num espaço — porque o
repositório ainda não tem um modelo treinável nem embeddings implementados.
Não há loss, treino, validação neural ou benchmark que permita medir esses
conceitos aqui.
