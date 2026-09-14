# Arquitetura

## Visão geral

```
folha-modelo (PDF) -> imprimir / preencher / escanear -> scans/*.jpg
        |
        v
ingest: deskew -> binarize -> segment -> label -> dataset/<style>/glyphs/*.png + index.jsonl
        |
        v
style (v1: GlyphBank | v2: NeuralStyle) -> styles/<style>/style.toml (+ pesos v2)
        |
        v
compose: layout de linhas, jitter de baseline/inclinação/espaço -> página limpa (RGBA, 300 dpi)
        |
        v
scan_effect: papel -> tinta -> geometria -> luz -> sensor -> JPEG -> página "escaneada"
        |
        v
export -> PNG / PDF (metadado generator=manual-handwrite-ia)
```

## Módulos (`src/manual_handwrite/`)

| Módulo | Responsabilidade | Fase |
|---|---|---|
| `cli.py` | Entrada `handwrite`: `template`, `ingest`, `train`, `write`, `scanify` | 0+ |
| `scan_effect/` | Pipeline de degradação puro (numpy in, numpy out), determinístico por `seed` | 1 |
| `template.py` | Gera a folha-modelo PDF com grade e marcadores fiduciais (ArUco) | 2 |
| `ingest/` | Detecta marcadores, corrige perspectiva, binariza (Sauvola), recorta células, rotula pela posição | 2 |
| `dataset.py` | Contrato do dataset: `index.jsonl` com `{char, variant, path, baseline, advance}` | 2 |
| `safety.py` | Recusa de assinatura, checagem de `owner_consent` | 2 |
| `style/glyphs.py` | v1: `GlyphBank` escolhe variantes, aplica ligaduras e jitter | 3 |
| `compose.py` | Layout: quebra de linha, margens, pauta, parágrafo | 3 |
| `export.py` | PNG/PDF 300 dpi com metadados obrigatórios | 3 |
| `style/neural.py` | v2: adaptador para modelo few-shot (extra `[neural]`) | 5 |

## Contratos principais

```python
# scan_effect
def scanify(page: np.ndarray, preset: str | ScanParams, seed: int) -> np.ndarray: ...


# style
class Style(Protocol):
    def render_word(self, text: str, rng: np.random.Generator) -> np.ndarray: ...  # RGBA


# compose
def compose_page(text: str, style: Style, page: PageSpec, seed: int) -> np.ndarray: ...
```

## Fronteiras de confiança

- `samples/`, `dataset/`, `styles/`, `models/`, `output/` são **dados pessoais**:
  ignorados pelo git e nunca lidos em CI.
- Nenhum módulo do núcleo faz rede. O extra `[neural]` só baixa pesos base
  públicos via comando explícito (`handwrite model download`).
