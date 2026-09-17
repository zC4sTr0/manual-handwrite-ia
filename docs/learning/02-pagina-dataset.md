# 02 — Como uma página vira dataset

## Problema encontrado
A fonte primária são folhas naturais, sem rótulo por letra. Um OCR único da
página não preserva regiões, ordem e incerteza de cada linha.

## Solução ingênua e limite
Aceitar toda transcrição automática ensina erros ao personalizador. Em código,
um `=` confundido com `==` muda o programa.

## Conceito e implementação
A Data Factory representa regiões e proveniência, separa `gold`, `silver` e
`quarantine`, e só publica pares acima do limiar. O módulo em
`src/manual_handwrite/data/` deliberadamente não chama rede: adaptadores VLM
serão portas explícitas e testáveis.

## Experimente
Crie uma manifestação JSONL sintética nos testes e verifique que uma amostra
quarantined não aparece no conjunto de treino. Sucesso é filtragem determinística
com página/região preservadas.
