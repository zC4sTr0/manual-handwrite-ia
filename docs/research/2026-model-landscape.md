# Panorama de modelos de geração de caligrafia (2026)

**Escopo.** Nota de decisão para um backend neural opcional da v2. O projeto
continua local e condicionado ao consentimento do titular; nenhum upload externo
é assumido. As referências externas abaixo foram consultadas como leads, mas os
claims são **não verificados localmente nesta revisão**. Antes de adotar algo,
reabrir a fonte, fixar commit/hash, licença e comando, e executar o benchmark
local. Saídas não podem ser usadas para assinaturas ou personificação.

## Decisão executiva provisória

Manter a futura `GlyphBank` como baseline reproduzível. DiffusionPen é o primeiro
candidato raster a investigar; CONSTANT é outro candidato de imagem; DiffInk só
é pertinente se o contrato mudar para trajetórias online. One-DM e a descrição
“imitação zero-shot em nível de parágrafo” permanecem leads não identificados.
Nenhum candidato foi instalado, treinado ou benchmarkado neste repositório.

## Comparação (status externo não verificado localmente)

| Sistema | Modalidade / unidade | Claim externo a verificar | Fit neste repo |
|---|---|---|---|
| DiffusionPen | Raster offline; palavra/parágrafo | O repositório afirma código MIT, pesos do dataset IAM Handwriting (IAM) e dependência Stable Diffusion.[1–3] | Candidato raster; exigiria adaptador e prova local. |
| CONSTANT | Raster offline; imagem estilizada one-shot | O artigo e README afirmam implementação e checkpoints para vários datasets.[4–6] | Candidato promissor, mais novo/pesado; verificar. |
| DiffInk | Trajetória online; linha completa | Artigo/repositório afirmam InkVAE (variational autoencoder, ou autoencoder variacional, de tinta), InkDiT (Diffusion Transformer de tinta), código e pesos.[7–8] | Não é drop-in; exigiria rasterizador e contrato novo. |
| One-DM | Geração de imagem one-shot | Lead encontrado como repositório; paper, README estável, licença e pesos não estabelecidos.[9] | Apenas pesquisa; sem decisão. |
| Claim de parágrafo zero-shot | Descrição ambígua | Nenhuma fonte primária única foi identificada para esse nome exato. | Desconhecido; não prometer fidelidade. |

## Notas por modelo

### DiffusionPen

A fonte [1–3] descreve uma abordagem de difusão few-shot e comandos de amostra
para imagens e parágrafos. Esses detalhes, o licenciamento e a disponibilidade
de pesos são claims externos não verificados localmente. Mesmo se reproduzidos,
não provam acentos portugueses, parágrafos longos ou o estilo do titular.

### CONSTANT

As fontes [4–6] descrevem quantização sensível a estilo e geração one-shot em
mais de um idioma. A existência de checkpoints anunciados não prova hash,
licença, reprodução das métricas ou transferência para `á`, `ã`, `ç` e
pontuação. Comparar 1, 5 e 24 referências só depois de um protocolo local.

### DiffInk

As fontes [7–8] descrevem geração de trajetórias de caneta. Isso conflita com o
contrato raster atual: seria necessário renderizador determinístico,
metadados de avanço/baseline e salvaguardas de quebra de linha. Métricas de
trajetória não devem ser comparadas diretamente com FID (Fréchet Inception
Distance), HWD (Handwriting Distance) ou preferência visual raster.

A alegação de que código é MIT e pesos CASIA seguem termos do dataset deve ser
confirmada diretamente na licença e nos avisos distribuídos; repositório MIT não
relicencia pesos ou dados derivados automaticamente.

### One-DM e claim de parágrafo

One-DM permanece sem identificação bibliográfica suficiente nesta nota. O
repositório [9], isoladamente, não sustenta arquitetura, desempenho, licença ou
pesos. “Zero-shot”, “one-shot” e “parágrafo” também não são sinônimos: o futuro
registro precisa definir referências, texto-alvo, modalidade e avaliação.

## Modalidade offline versus online

- **Raster offline:** entra imagem escrita e sai imagem; combina com scans,
  `GlyphBank`, composição e efeito de scan.
- **Trajetória online:** representa coordenadas temporais, eventos pen-up e
  possivelmente pressão; exige dados online e renderizador determinístico.

IAM Handwriting (IAM) e CASIA-OLHWDB (base chinesa de escrita manual online)
têm modalidades e condições de acesso diferentes segundo as fontes [10–11]. Não extrair trajetórias silenciosamente de scans; isso criaria
outro dataset e outra hipótese.

## Plano de benchmark local futuro

O protocolo em [`docs/experiments/EXP-001.md`](../experiments/EXP-001.md) é um
plano, não um resultado. Quando houver ambiente e dados consentidos, registrar
versões de Python/PyTorch/CUDA, GPU, driver, commit, hash do checkpoint,
precisão, resolução, seed e batch size. Medir tempo mediano/p95, VRAM, falhas,
dimensões, hash de repetição, CER (Character Error Rate, taxa de erro de
caracteres), WER (Word Error Rate, taxa de erro de palavras) e preferência cega.
Manter imagens, pesos e caminhos privados fora do Git e dos logs.

## Critérios de parada e licenças

Não adotar sem fonte primária identificada, licenças separadas para código,
pesos, modelo-base e dataset, hash, comando executado e resultado local. Stable
Diffusion v1.5, por exemplo, é uma dependência alegada de DiffusionPen, não prova
de licença uniforme para todos os artefatos.[12]

## Referências (numeração contínua)

[1] https://github.com/koninik/DiffusionPen
[2] https://arxiv.org/abs/2409.06065
[3] https://huggingface.co/konnik/DiffusionPen
[4] https://github.com/duylebkHCM/CONSTANT
[5] https://arxiv.org/abs/2603.07543
[6] https://openaccess.thecvf.com/content/WACV2026/html/Le_CONSTANT_Towards_High-Quality_One-Shot_Handwriting_Generation_with_Patch_Contrastive_Enhancement_WACV_2026_paper.html
[7] https://github.com/awei669/DiffInk
[8] https://arxiv.org/abs/2509.23624
[9] https://github.com/gyoon0718-ui/One_DM
[10] https://nlpr.ia.ac.cn/databases/handwriting/home.html
[11] https://fki.tic.heia-fr.ch/databases/iam-on-line-handwriting-database
[12] https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5
