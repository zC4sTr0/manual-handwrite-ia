# Pesquisa: síntese de caligrafia

Resumo das abordagens para decidir uma v2. Esta é uma nota de pesquisa, não uma
lista de dependências adotadas. Claims externos (afirmações sobre artigos,
repositórios, pesos, licenças ou datasets) são **não verificados localmente**:
as URLs abaixo são pontos de partida e precisam de conferência de versão,
licença, hash e execução antes de qualquer decisão.

## Famílias de abordagem

| Abordagem | Ideia | Prós | Contras |
|---|---|---|---|
| Síntese por glifos (v1 futuro) | Recortar e recombinar amostras reais com variação | Poucos dados, controle total, CPU | Conexões cursivas artificiais |
| Traço online com RNN/MDN (rede neural recorrente / mistura de densidades) | Gerar sequência de pontos da caneta | Traços contínuos | Exige dados de caneta, não scans |
| GAN (rede generativa adversarial) / Transformer few-shot | Imagem condicionada ao estilo | Poucas amostras de estilo | Artefatos em palavras longas |
| Difusão few-shot | Difusão condicionada a referências | Fidelidade potencialmente maior | GPU, inferência lenta, pesos grandes |

## Questões específicas do português

A hipótese de que acentos e cedilha são raros nos datasets públicos precisa ser
verificada no dataset escolhido; IAM, CVL e RIMES têm idiomas e condições
próprios. Para o projeto, a pergunta prática é cobertura de `á`, `ã`, `ç`,
pontuação e combinações reais. Não tratar essa hipótese como medição local.

## Estado e decisão provisória

O estado local continua raster-first e sem backend neural executado. A decisão
provisória é manter a base de glifos como baseline futuro e reavaliar um modelo
de difusão somente na Fase 5, depois de dataset pessoal consentido e benchmark.
Isso não significa que a Fase 3 esteja implementada.

## Critérios de pesquisa antes de adotar

Para cada candidato, registrar artigo primário, código oficial, commit/tag,
checkpoint e hash, licença do código, licença dos pesos e termos do dataset,
requisitos de hardware, comando de reprodução e resultado local. Se qualquer
item faltar, manter como hipótese/lead, não como dependência.

Veja a nota detalhada em [`research/2026-model-landscape.md`](research/2026-model-landscape.md)
e o protocolo de experimento em [`experiments/EXP-001.md`](experiments/EXP-001.md).
