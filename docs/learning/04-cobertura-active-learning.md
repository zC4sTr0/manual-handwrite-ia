# 04 — Cobertura como active learning

## Problema encontrado
Mais páginas não garantem informação nova. Precisamos medir símbolos e tokens
vistos e pedir apenas uma pequena folha que cubra lacunas.

## Solução ingênua e limite
Escolher snippets aleatórios pode repetir `print` e nunca observar operadores
críticos como `!=` ou `>=`.

## Conceito e implementação
`manual_handwrite.coverage.analyze_text` extrai caracteres, tokens Python e
operadores, expondo ausências do vocabulário inicial. A próxima etapa adicionará
um otimizador de maximum coverage que seleciona snippets Python naturais.

## Experimente
```bash
uv run python -c "from manual_handwrite.coverage import analyze_text; print(analyze_text('for i in range(3):').as_dict())"
```

Sucesso é cobertura observável e auditável; nenhum caractere é inferido apenas
porque seria comum no vocabulário.
