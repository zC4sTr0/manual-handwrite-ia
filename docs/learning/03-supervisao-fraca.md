# 03 — Supervisão fraca e confiança

## Problema encontrado
Uma VLM pode produzir uma hipótese boa, mas não é ground truth. O pipeline
precisa saber quando descartar informação.

## Solução ingênua e limite
Corrigir uma linha inválida com o parser Python seria alucinação: sintaxe sugere,
mas não prova, o que foi escrito visualmente.

## Conceito e implementação
A validação combina evidência visual, concordância entre passes e verificadores
Python. O parser é um sinal de confiança e um detector de ambiguidade, nunca um
substituto da imagem. O resultado alimenta tiers e manifests versionáveis.

## Experimente
Compare uma linha sintética válida com uma linha contendo `if x = 5:`. Observe
que a análise registra os tokens observados e não inventa `==`.
