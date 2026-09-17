# 02 — Como uma página vira dataset

## Objetivo

Aprender a preservar página, região, texto e proveniência sem transformar uma
transcrição incerta em verdade. A fonte primária são folhas naturais, sem rótulo
por letra; um OCR único da página não preserva regiões, ordem e incerteza.

## Problema e limite da solução ingênua

Aceitar toda transcrição automática ensina erros ao personalizador. Em código,
um `=` confundido com `==` muda o programa. O módulo local não chama rede nem faz
OCR: ele valida dados que já foram fornecidos por um chamador explícito.

## Conceito e implementação atual

A Data Factory em `src/manual_handwrite/data/` representa páginas e regiões,
calcula tiers `gold`, `silver` e `quarantine`, preserva proveniência e, por
padrão, não publica `quarantine` no manifesto. O caminho de par imagem/`source.py`
é `ingest_source_pair`; ele exige consentimento, valida Python e calcula o hash
do arquivo-fonte.

## Micro-experimentos executáveis

Use fixtures sintéticas, sem escanear ou adicionar amostras pessoais:

```bash
uv run pytest -q tests/test_data_factory.py tests/test_source_pair.py tests/test_cli.py -q
```

Saída esperada: `16 passed` (se a suíte tiver sido ampliada, o número pode
crescer; o critério é nenhum `failed`). Os testes verificam que o manifesto
JSONL preserva página/região/proveniência, exclui `quarantine` por padrão,
exige `owner_consent` e produz um registro `gold` para um par sintético.

Para exercitar o contrato de cobertura de uma fonte Python já existente:

```bash
uv run pytest -q tests/test_coverage.py
```

Saída esperada: `2 passed`. O resultado registra o que foi observado; não
preenche um símbolo ausente só porque ele seria comum.

## O que ainda não existe

A etapa não implementa template de coleta, OCR/VLM, correção de perspectiva ou
rotulagem automática de uma página real. Esses são próximos passos condicionados
a dados consentidos e aos contratos de ingestão; não são resultados deste
experimento.
