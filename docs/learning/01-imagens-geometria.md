# 01 — Imagens e geometria de documentos

## Objetivo

Entender por que uma foto de uma folha não é ainda uma matriz comparável: há
rotação, perspectiva, fundo, iluminação e ruído de captura. Nesta etapa, o
contrato implementado é a simulação de scan; correção geométrica de páginas
reais continua dependente da ingestão futura.

## Problema e limite da solução ingênua

Aplicar um filtro global diretamente mistura tinta com iluminação. O resultado
pode ficar visualmente diferente mesmo quando o conteúdo é igual. A primeira
fatia separa a simulação de scan do gerador de letra, para que o pipeline de
aparência evolua sem contaminar o modelo de estilo.

## Conceito e implementação atual

`manual_handwrite.scan.scanify` recebe uma imagem, uma semente e um preset, e
devolve uma imagem reproduzível. A implementação está em
`src/manual_handwrite/scan/`; a CLI também expõe `scanify`.

## Micro-experimento executável

Na raiz do repositório:

```bash
uv run pytest -q tests/test_scan_effect.py
```

Saída esperada: `2 passed`. O primeiro teste confirma que a mesma entrada e a
mesma seed produzem os mesmos pixels e que outra seed altera a degradação; o
segundo confirma que a entrada não é modificada e que preset desconhecido é
recusado. A página usada pelo teste é sintética e não representa a letra do
proprietário.

Para conferir a CLI sem dados pessoais, use o smoke já coberto por
`tests/test_cli.py` (`test_scanify_command_writes_processed_image_with_metadata`).
Ele espera uma imagem de saída com as mesmas dimensões e o metadado
`generator=manual-handwrite-ia`.

## Próximos limites

Isso não prova correção de perspectiva, qualidade perceptual, OCR nem geração de
caligrafia. Esses assuntos pertencem à ingestão e às fases futuras descritas em
`docs/IMPLEMENTATION-PLAN.md` e no [Roadmap](../ROADMAP.md).
