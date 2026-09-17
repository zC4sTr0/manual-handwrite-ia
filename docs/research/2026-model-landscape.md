# Handwriting-generation model landscape (2026)

**Scope.** This is a decision note for the optional v2 neural backend. The
project remains a local, owner-consented handwriting tool; no external upload
is assumed. Facts below are separated from hypotheses, and model outputs must
not be used for signatures or impersonation.

## Executive decision

Keep the v1 `GlyphBank` as the reproducible baseline. The first neural
candidate to benchmark is **DiffusionPen** because its authors publish code,
weights, and a five-reference few-shot path. **CONSTANT** is the strongest
image-generation candidate if its newer code and checkpoints are reproducible.
**DiffInk** is relevant only if the project is willing to change the internal
contract from RGBA word images to online pen trajectories. Do not select
One-DM or the unnamed “paragraph-level zero-shot imitation” result until a
primary paper, runnable code, license, and weights are identified.

## Comparison

| System | Modality / unit | Verified public status | Fit to this repo |
|---|---|---|---|
| DiffusionPen | Offline raster; word and paragraph sampling | ECCV 2024 code repo is MIT; repo links IAM weights on Hugging Face and Stable Diffusion v1.5 dependency.[1][2][3] | Best first raster baseline; needs adapter for `Style.render_word`. |
| CONSTANT | Offline raster; one-shot styled handwriting images | WACV 2026 paper and official implementation are public; README advertises checkpoints for IAM, IMGUR5K, CASIA, IIIT, and ViHTGen.[4][5][6] | Promising quality/style candidate, but newer and heavier; verify locally before commitment. |
| DiffInk | Online trajectory; full text line | arXiv describes InkVAE + InkDiT and full-line pen-trajectory generation; official repo says code and pretrained weights were released.[7][8] | Interesting long-line model, but not a drop-in raster backend; integration would require rasterization and a new style contract. |
| One-DM | Reported one-shot handwriting image generation | A GitHub search found a repository named `gyoon0718-ui/One_DM`, but its default README was unavailable during this review.[13] | Research lead only. No adoption decision. |
| Paragraph-level zero-shot imitation | Presumably raster or trajectory, unclear | No authoritative paper/repository was identified from the exact description in this review. DiffusionPen does expose a `paragraph` sampling mode, but that is not proof of the separately named zero-shot result.[1] | Treat as an unresolved lead, not a model choice. |

## Model notes

### DiffusionPen

The authors describe a few-shot diffusion model that can use as few as five
reference samples, with a style-extraction module using metric learning and
classification.[1][2] The official README provides separate sampling commands
for single images and paragraphs and instructions to train a style encoder and
then the diffusion model on custom data.[1] The repo is MIT-licensed according
to GitHub metadata.[1] The linked Hugging Face page contains preprocessed IAM
data, style-encoder weights, and IAM DiffusionPen weights.[1][3]

**Practical implication:** this is the most realistic first experiment for the
current architecture: generate words/short lines, normalize them, then let
`compose_page` handle layout and `scan_effect` handle paper. It is not evidence
that Portuguese accents, long paragraphs, or the owner's style will work.

**Unknowns to close:** exact VRAM peak at the chosen resolution; inference time
per word/paragraph; whether custom references must contain particular content;
quality on Portuguese diacritics and cursive joins; provenance and
redistribution terms for the IAM-derived weights and the Stable Diffusion
component. The code license being MIT does not automatically relicense model
weights or dataset-derived assets.

### CONSTANT

The paper describes one-shot diffusion with Style-Aware Quantization (SAQ), a
contrastive style objective, and latent patch contrastive enhancement.[5][6]
Its reported evaluation spans English, Chinese, and a Vietnamese dataset, which
makes multilingual coverage more relevant than an IAM-only baseline.[5][6] The
official README supplies a CLI for single-style and multi-style generation and
lists downloadable checkpoints for several datasets.[4]

**Practical implication:** test CONSTANT after a minimal DiffusionPen run if
local quality is the bottleneck. Its one-shot reference interface may reduce
sample collection, but one reference is a risk for owner-style capture and
should be compared against 5-reference and 24-reference conditions.

**Unknowns to close:** exact checkpoint files and hashes; actual license of
checkpoints, ViHTGen, and dataset-derived assets; whether the advertised
numbers reproduce with the released commit; peak VRAM and latency on an RTX
4070; whether its image dimensions and conditioning API can produce isolated
words reliably; and whether its Vietnamese coverage transfers to Portuguese
`á`, `ã`, `ç`, and mixed punctuation. The repository README is evidence of an
implementation and claimed resources, not independent verification of its
reported metrics.[4]

### DiffInk

DiffInk explicitly targets text-to-online-handwriting generation: text and a
style reference condition complete text lines, and the output is a pen
trajectory rather than a bitmap.[7][8] Its InkVAE uses OCR and style
classification losses, while InkDiT is the latent diffusion Transformer.[8]
The official repository describes glyph/style-aware latent diffusion and
provides dataset and pretrained-weight download links.[7]

**Practical implication:** this is the best conceptual match for natural
stroke continuity and line-level structure, but it conflicts with the current
`Style.render_word(...) -> RGBA` protocol. A future adapter would need a
trajectory-to-raster renderer, baseline/advance metadata, and safeguards for
line wrapping. Do not compare its trajectory metrics directly with raster FID,
HWD, or visual preference without a common rendered-output protocol.

**License/weights:** the repo states that code is MIT, while pretrained
weights trained on CASIA-OLHWDB follow that dataset's original license.[7][10]
The dataset site requires an application form, so “code available” must not be
read as permission to redistribute weights or CASIA data.[7][10]

**Unknowns to close:** whether all released weights are downloadable without
manual approval; exact training-data subset and license notices; trajectory
coordinate conventions; rasterization settings; Portuguese text support; and
RTX 4070 memory/time after the full-line model is loaded.

### One-DM and the paragraph-level claim

The existing project notes name One-DM as a one-shot candidate, but this review
could not establish a stable primary paper or official reproducible release
for it. The repository search result is insufficient evidence for architecture,
performance, license, or weights.[13] Record any future URL, paper identifier,
commit, checkpoint hash, and test command before citing it as a dependency.

Likewise, “paragraph-level zero-shot imitation” is an ambiguous descriptor,
not a sufficiently unique citation. A paragraph sampler, a one-shot style
encoder, and zero-shot imitation are different claims. Required evidence is a
paper title/identifier plus an official implementation and a defined protocol
(number/content of references, target text, output modality, and evaluation).
Until then, mark the item **unknown** and do not promise paragraph fidelity.

## Offline versus online modality

- **Offline/raster:** input is an image of written text; output is an image.
  This matches scans, `GlyphBank`, `compose_page`, and `scan_effect`. It can
  preserve visual artifacts but does not expose pen order or pressure.
- **Online/trajectory:** input/output represent time-ordered pen coordinates,
  pen-up events, and possibly pressure. It can model joins and stroke dynamics,
  but requires trajectory data and a deterministic renderer before export.
- IAM and CASIA-OLHWDB expose different data modalities and access conditions;
  DiffInk's README specifically names CASIA-OLHWDB and IAM-OnDB as resources.[7][11]
  Do not train an online model from the project's scans without an explicit
  trajectory-extraction decision; inferred trajectories are a different
  dataset and should be validated separately.

The current architecture is intentionally raster-first. An online backend
should be a separate experimental adapter, not a silent change to the v1
contract.

## Licensing and artifact policy

1. Record code license, checkpoint license, base-model license, and dataset
   terms independently. “MIT repository” is not enough for weights.[1][7]
2. Keep raw owner samples, derived datasets, checkpoints, and generated pages
   outside git and CI logs, as required by `AGENTS.md`.
3. Download only with an explicit command; normal generation remains offline.
4. Store a manifest locally with source URL, commit/tag, file hash, license
   notice, model config, and benchmark command. Never commit the manifest if it
   contains private paths or data.
5. Stable Diffusion v1.5 is a dependency of DiffusionPen's VAE/DDIM setup, not
   proof that every DiffusionPen asset has the same license.[1][12]

## RTX 4070 local benchmark plan

Treat “RTX 4070, 12 GB VRAM” as the machine assumption to verify at run time,
not a hard-coded capability. Use one isolated environment per candidate and
record OS, Python, PyTorch, CUDA, GPU name, driver, git commit, checkpoint
hash, precision, resolution, seed, and batch size.

### Phases

1. **Smoke:** load weights, generate one fixed short word from five owner-
   consented reference images, then unload. Capture peak allocated/reserved
   VRAM and failure mode. No real samples in logs.
2. **Raster baseline:** for each model that runs, generate 30 words and 10
   short lines at 512px and the model's native recommended setting, with seeds
   `0..9`. Include Portuguese stress cases: `ação`, `órgão`, `pão`, `coração`,
   `pingüim`, `ç`, currency, punctuation, and a long compound word.
3. **Page path:** assemble the same 300-dpi A4 page through the project adapter,
   apply each of the `scanner-escritorio` and `foto-celular` presets, and export
   PNG with required generator metadata.
4. **Ablations:** 1/5/24 reference images; native versus 512px; fp16 versus
   bf16 if supported; 10 versus 25 diffusion steps if the implementation
   exposes steps. Hold all seeds and text fixed.
5. **Online branch (DiffInk only):** add a temporary trajectory rasterizer and
   compare rendered lines, not raw trajectory metrics, against raster models.

### Metrics and report

Record median and p95 seconds per word/line/page, peak VRAM, crash/OOM rate,
output dimensions, deterministic-repeat pixel hash, character error rate (CER)
and word error rate (WER) from a fixed local HTR evaluator, and a blinded
owner/style preference score. Add a legibility failure count for accents,
cedilla, punctuation, clipping, broken joins, and margin overflow. Keep
per-image outputs in ignored local storage; logs contain IDs and metrics only.

This benchmark is a protocol, not a claimed result. No model wins until its
actual run produces a complete report and passes the decision gates in
`EXP-001.md`.

## Open questions / stop conditions

- Which exact “One-DM” paper and release is intended?
- Which exact paragraph-level zero-shot paper is intended?
- Are the selected checkpoints legally usable for this owner-only local tool?
- Can a candidate render accented Portuguese faithfully without per-character
  fallback?
- Does a candidate beat v1 in blinded owner preference at acceptable latency?
- Can it run within the verified VRAM budget without hidden network calls?

## Sources

[1] https://github.com/koninik/DiffusionPen
[2] https://arxiv.org/abs/2409.06065
[3] https://huggingface.co/konnik/DiffusionPen
[4] https://github.com/duylebkHCM/CONSTANT
[5] https://arxiv.org/abs/2603.07543
[6] https://openaccess.thecvf.com/content/WACV2026/html/Le_CONSTANT_Towards_High-Quality_One-Shot_Handwriting_Generation_with_Patch_Contrastive_Enhancement_WACV_2026_paper.html
[7] https://github.com/awei669/DiffInk
[8] https://arxiv.org/abs/2509.23624
[13] https://github.com/gyoon0718-ui/One_DM
[10] https://nlpr.ia.ac.cn/databases/handwriting/home.html
[11] https://fki.tic.heia-fr.ch/databases/iam-on-line-handwriting-database
[12] https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5
