# Efeito "escaneado"

O objetivo é o aspecto pouco real de papel escaneado: nada de branco perfeito,
tinta uniforme ou alinhamento exato.

## Estágios (ordem padrão)

| # | Estágio | O que simula | Parâmetros principais |
|---|---|---|---|
| 1 | `ink_density` | pressão da caneta, falhas de tinta | opacidade variável por traço, dropout |
| 2 | `ink_bleed` | tinta espalhando na fibra | blur gaussiano leve + limiar aleatório nas bordas |
| 3 | `paper_texture` | fibra e grão do papel, amarelado | ruído Perlin multiescala, cor base (ex. `#f4f1e8`) |
| 4 | `geometry` | folha torta no vidro, celular inclinado | rotação, perspectiva, curvatura, ondulação |
| 5 | `lighting` | luz irregular, sombra na borda | vinheta, gradiente linear, sombra de lombada |
| 6 | `sensor_noise` | ruído do sensor | gaussiano + poisson, poeira e pontos |
| 7 | `tone_curve` | pretos cinzentos, brancos sujos | gamma, compressão de faixa dinâmica |
| 8 | `jpeg` | compressão | qualidade 60 a 90, subsampling 4:2:0 |

## Presets

- `scanner-escritorio`: rotação pequena, luz uniforme, papel levemente cinza, JPEG 85.
- `foto-celular`: perspectiva visível, vinheta forte, sombra de borda, JPEG 75.
- `xerox-velho`: alto contraste, pontos de toner, bordas escuras, meio-tom.
- `limpo`: só `ink_density` e `ink_bleed` (para quem quer apenas a letra).

## Implementação

- Numpy e OpenCV puros, determinísticos por `seed` (`np.random.default_rng(seed)`).
- Referência útil: a biblioteca [Augraphy](https://github.com/sparkfish/augraphy)
  (augmentation de documentos). Avaliar na Fase 1 como dependência ou inspiração.
