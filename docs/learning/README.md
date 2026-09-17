# Trilha de aprendizagem ligada ao motor

Esta trilha ensina os contratos que já existem no repositório e separa claramente
prática local de ideias futuras. Nem todo capítulo é um tutorial de ponta a ponta:
quando uma capacidade ainda não existe, o texto aponta para o estado atual em vez
de prometer um comando que não pode ser executado.

## Objetivos

Ao concluir a trilha, você deverá conseguir:

- explicar por que imagem, geometria, conteúdo e estilo são problemas distintos;
- ler a proveniência de uma região e entender os tiers `gold`, `silver` e
  `quarantine`;
- distinguir evidência observada de hipótese de transcrição;
- medir cobertura de caracteres, tokens e operadores Python;
- interpretar o que o projeto já verifica e o que continua sem modelo neural.

## Pré-requisitos

- Python básico: arquivos, funções, listas, dicionários e exceções;
- noções de imagem raster (pixels, largura, altura e escala de cinza);
- terminal com Python 3.11+ e `uv` instalado;
- nenhum dado pessoal: os experimentos usam fixtures sintéticas dos testes.

## Ordem recomendada

1. [01 — Imagens e geometria de documentos](01-imagens-geometria.md): pixels,
   transformação e scan determinístico.
2. [02 — Como uma página vira dataset](02-pagina-dataset.md): regiões,
   manifesto e proveniência.
3. [03 — Supervisão fraca e confiança](03-supervisao-fraca.md): hipótese,
   validação e quarentena.
4. [04 — Cobertura como active learning](04-cobertura-active-learning.md):
   preparação matemática, medição e seleção de lacunas.
5. [Checkpoint 05 — fronteira da personalização](checkpoint-05.md): revisão do
   que está implementado antes de falar em geração.

## Convenções de leitura

Comandos `uv run pytest ...` abaixo são executáveis hoje. Eles verificam
contratos locais; passar não significa que uma VLM (modelo de linguagem e visão)
ou um modelo de geração tenha sido treinado. `train`, `write` e benchmark neural
são trabalho futuro, não comandos disponíveis na CLI atual.

Dados reais do titular, pesos e imagens geradas ficam fora do Git e dos logs.
Consulte [`docs/PROJECT-STATE.md`](../PROJECT-STATE.md) para a fase vigente e o
próximo teste concreto.
