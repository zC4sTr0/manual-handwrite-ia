# manual-handwrite-ia

Uma IA local que aprende a **sua** letra a partir de amostras escaneadas e gera
manuscritos novos com ela — incluindo o aspecto de **documento escaneado**
(papel levemente torto, textura, tinta irregular, iluminação desigual,
compressão JPEG), para que o resultado pareça uma folha de verdade que passou
por um scanner, e não um PNG limpo demais.

> Status: **Fase 0 — esqueleto e documentação.** Ainda não gera manuscritos.
> O estado atual e o próximo passo concreto ficam em
> [`docs/PROJECT-STATE.md`](docs/PROJECT-STATE.md).

## O que o projeto vai fazer

1. **Coletar** sua letra com uma folha-modelo imprimível (grade com letras,
   números, acentos do português, pontuação e palavras comuns).
2. **Extrair** cada glifo/palavra da folha escaneada (deskew, binarização,
   segmentação) e montar um dataset pessoal, que **nunca sai da sua máquina**.
3. **Aprender o estilo** em duas etapas:
   - **v1 — síntese por glifos:** várias variantes por caractere, ligaduras,
     variação de baseline, inclinação, espaçamento e pressão. Funciona com
     poucas amostras e é totalmente controlável.
   - **v2 — modelo neural few-shot:** geração de palavras/linhas condicionada ao
     seu estilo (família de modelos de difusão/transformers de handwriting),
     afinado com o seu dataset.
4. **Compor** a página: margens, pautas opcionais, quebras de linha naturais,
   pequenos erros de alinhamento.
5. **Envelhecer como scan:** pipeline de degradação configurável (papel,
   tinta, geometria, luz, ruído de sensor, JPEG) com presets como
   `scanner-escritorio`, `foto-celular`, `xerox-velho`.
6. **Exportar** PNG/PDF em 300 dpi.

## O que ele não faz (por design)

- **Não gera assinaturas** nem imita a letra de terceiros. Veja
  [`docs/ETHICS-AND-PRIVACY.md`](docs/ETHICS-AND-PRIVACY.md).
- Não envia suas amostras para nenhum serviço externo por padrão.
- Não é ferramenta de falsificação de documentos.

## Uso previsto (CLI)

```bash
uv sync --dev
uv run handwrite template --out folha-modelo.pdf        # imprimir e preencher
uv run handwrite ingest scans/folha-01.jpg              # extrair glifos
uv run handwrite train --style minha-letra              # v1: montar o estilo
uv run handwrite write "Querido diário, hoje..." \
    --style minha-letra --scan-preset scanner-escritorio --out carta.pdf
```

Hoje só `handwrite --version` funciona; os demais comandos são o contrato das
próximas fases.

## Documentação

| Documento | Conteúdo |
|---|---|
| [docs/COMO-FUNCIONA.md](docs/COMO-FUNCIONA.md) | Explicação do pipeline para programadores tradicionais |
| [AGENTS.md](AGENTS.md) | Regras para agentes (Hermes, Claude Code, Codex) |
| [docs/PROJECT-STATE.md](docs/PROJECT-STATE.md) | Fase atual, próximo teste, bloqueios |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Módulos, fluxo de dados, contratos |
| [docs/IMPLEMENTATION-PLAN.md](docs/IMPLEMENTATION-PLAN.md) | Fases com critérios de aceite |
| [docs/DATA-COLLECTION.md](docs/DATA-COLLECTION.md) | Como preencher e escanear a folha-modelo |
| [docs/SCAN-EFFECT.md](docs/SCAN-EFFECT.md) | O pipeline de "aspecto escaneado" |
| [docs/RESEARCH.md](docs/RESEARCH.md) | Estado da arte em síntese de caligrafia |
| [docs/ETHICS-AND-PRIVACY.md](docs/ETHICS-AND-PRIVACY.md) | Limites de uso e privacidade |
| [docs/ROADMAP.md](docs/ROADMAP.md) | O que fica para depois |

## Desenvolvimento

- Python 3.11+, [`uv`](https://docs.astral.sh/uv/), `pytest`, `ruff`.
- Gates: `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`.
- Suas amostras reais ficam em `samples/` (ignorado pelo git) — nunca comite.
