# 01 — Imagens e geometria de documentos

## Problema encontrado
Uma foto de uma folha não é ainda uma matriz comparável: há rotação, perspectiva,
fundo e ruído de captura.

## Solução ingênua e limite
Aplicar um filtro global diretamente mistura tinta com iluminação. O resultado
pode ficar visualmente diferente mesmo quando o conteúdo é igual.

## Conceito e implementação
A primeira fatia separa a simulação de scan do gerador de letra. O contrato é
`manual_handwrite.scan.scanify`: recebe uma imagem e uma semente, devolve uma
imagem reproduzível. O pipeline pode evoluir sem contaminar o modelo de estilo.

## Experimente
Rode `uv run pytest -q tests/test_scan_effect.py` e compare os artefatos
produzidos pelo preset com duas seeds. Sucesso significa mesma entrada + mesma
seed = mesmos pixels; seed diferente altera a degradação, não o conteúdo.

## Evidência
O teste e o código desta etapa ficam em `tests/test_scan_effect.py` e
`src/manual_handwrite/scan/`. A saída visual será adicionada ao relatório quando
houver fixture de imagem versionada (sintética, nunca caligrafia real).
