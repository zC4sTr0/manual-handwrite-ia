# Pesquisa: síntese de caligrafia

Resumo das abordagens para decidir a v2. **Validar versões, licenças e
disponibilidade de pesos antes de adotar qualquer uma.**

## Famílias de abordagem

| Abordagem | Ideia | Prós | Contras |
|---|---|---|---|
| Síntese por glifos (v1) | Recortar e recombinar amostras reais com variação | Poucos dados, controle total, roda na CPU | Conexões cursivas artificiais |
| Traço online (RNN/MDN) | Gerar a sequência de pontos da caneta (Graves, 2013, "Generating Sequences With Recurrent Neural Networks") | Traços contínuos e naturais | Precisa de dados de caneta digital, não de scans |
| GAN / Transformer few-shot | Imagem de palavra condicionada ao estilo (ex.: Handwriting Transformers, 2021; VATr, 2023) | Poucas amostras de estilo | Artefatos em palavras longas |
| Difusão few-shot | Difusão condicionada a amostras de estilo (ex.: WordStylist, 2023; One-DM e DiffusionPen, 2024) | Melhor fidelidade | GPU, inferência lenta, pesos grandes |

## Questões específicas do português

- Acentos e cedilha são raros nos datasets públicos (o IAM é em inglês). A v1
  cobre isso com glifos próprios; na v2 é preciso incluir palavras acentuadas
  no fine-tuning ou compor o acento sobre a letra base.
- Datasets de referência: IAM Handwriting (inglês), CVL, RIMES (francês).

## Decisão atual

v1 = glifos (Fase 3). Reavaliar difusão few-shot na Fase 5, com o dataset pessoal pronto.
