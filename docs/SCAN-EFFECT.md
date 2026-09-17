# Efeito “escaneado”

O objetivo é dar a uma imagem o aspecto imperfeito de papel processado: fundo
fora do branco puro, variação de tinta, ruído, iluminação e compressão. O
simulador atual é local e determinístico; ele não pretende reproduzir uma
câmera física com fidelidade calibrada.

## Implementação atual

A função é `manual_handwrite.scan.scanify(image, seed, preset)`, em
[`src/manual_handwrite/scan/__init__.py`](../src/manual_handwrite/scan/__init__.py).
Ela trabalha principalmente em tons de cinza com Pillow, usa
`random.Random(seed)`, preserva a entrada e pode receber/retornar uma imagem
Pillow ou um array NumPy na fronteira. Os parâmetros internos combinam:

- blur leve para bleed e variação determinística de densidade da tinta;
- papel com base acinzentada, textura aleatória e vinheta;
- multiplicação de papel e tinta, contraste adicional no preset de xerox;
- ruído gaussiano;
- rotação determinística limitada pelo preset;
- reentrada JPEG nos presets que têm qualidade configurada.

Não há implementação independente de oito estágios nomeados. A função atual
não usa OpenCV nem `np.random.default_rng`.

## Presets atuais

| Preset | Parâmetros observáveis no código | Situação |
|---|---|---|
| `scanner-escritorio` | papel 246, textura 3, ruído 1,5, bleed 0,35, rotação até 0,45°, vinheta 0,025, JPEG 85 | implementado |
| `foto-celular` | papel 242, textura 5, ruído 3,0, bleed 0,65, rotação até 1,5°, vinheta 0,12, JPEG 75 | implementado |
| `xerox-velho` | papel 235, textura 7, ruído 4,0, bleed 0,8, rotação até 0,8°, vinheta 0,16, JPEG 65 e contraste extra | implementado |
| `limpo` | papel 250, textura 1, ruído 0,7, bleed 0,2, sem rotação e sem JPEG | implementado |

A CLI expõe o mesmo conjunto por meio de:

```text
handwrite scanify in.png --preset foto-celular --seed 7 --out out.jpg
```

PNG e PDF passam por `export.py`; JPEG é salvo diretamente pelo caminho da
CLI. O metadado obrigatório é preservado na exportação PNG/PDF e a CLI inclui
uma anotação equivalente no JPEG.

## Estágios desejados, ainda futuros

A decomposição abaixo é uma meta de arquitetura, não uma descrição do código
atual:

1. `ink_density` — pressão e falhas de tinta;
2. `ink_bleed` — espalhamento controlado nas bordas;
3. `paper_texture` — fibra, grão e cor do papel;
4. `geometry` — rotação, perspectiva, curvatura e ondulação;
5. `lighting` — gradientes e sombras de borda;
6. `sensor_noise` — ruído de sensor, poeira e pontos;
7. `tone_curve` — gamma e compressão de faixa dinâmica;
8. `jpeg` — compressão configurável.

Hoje há aproximações de densidade/bleed, textura, geometria limitada a
rotação, iluminação/vinheta, ruído e JPEG. **Perspectiva, curvatura,
ondulação, poeira/pontos, tone curve explícita, Poisson e um pipeline de
estágios independentes ainda não estão implementados.**

A biblioteca [Augraphy](https://github.com/sparkfish/augraphy) pode ser
avaliada como inspiração ou dependência futura, mas não é dependência atual.

## Critérios ainda não verificados

- Não foi estabelecido nem medido um limiar de SSIM.
- A afirmação de que nenhum preset deixa mais de 98% dos pixels em branco puro
  ainda é critério futuro/não verificado.
- Não há teste de OCR, legibilidade humana calibrada ou fidelidade fotográfica.
- Não há evidência de que `foto-celular` reproduza perspectiva de câmera:
  atualmente ele só aplica rotação, vinheta, ruído, bleed, textura e JPEG.

Os testes atuais verificam principalmente determinismo, não mutação da entrada,
presets válidos e erro para preset desconhecido; veja
[`tests/test_scan_effect.py`](../tests/test_scan_effect.py).
