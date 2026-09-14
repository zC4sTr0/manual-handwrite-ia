# AGENTS.md

Guia para agentes de IA (Hermes, Claude Code, Codex) neste repositório. Leia primeiro.

## O que é este projeto

manual-handwrite-ia é uma ferramenta local em Python que aprende a letra do
dono do repositório a partir de amostras escaneadas e gera manuscritos novos
nessa letra, com um pipeline opcional de degradação que imita papel
escaneado/fotografado. Não é gerador de assinaturas nem ferramenta para imitar
a letra de outras pessoas.

## Por onde começar

1. `docs/PROJECT-STATE.md` — fase atual, próximo teste, bloqueios.
2. `docs/IMPLEMENTATION-PLAN.md` — fases, contratos, CLI e layout de arquivos.
3. `docs/ETHICS-AND-PRIVACY.md` — antes de mexer em ingestão, dataset, modelo ou exportação.
4. `docs/ARCHITECTURE.md` — módulos e fluxo de dados.
5. `docs/SCAN-EFFECT.md` e `docs/RESEARCH.md` — quando o assunto for degradação ou modelo neural.

Cópia operacional do plano: `.hermes/plans/manual-handwrite-ia-v1.md`.

## Inegociáveis

- Amostras reais de letra, datasets derivados, pesos treinados e saídas geradas
  **nunca** entram no git nem em logs de CI. Testes usam fixtures sintéticas.
- Nenhuma chamada de rede na execução padrão. Upload para APIs externas só com
  flag explícita e documentada.
- Nada de geração de assinatura: o renderizador recusa entradas marcadas como
  assinatura e o dataset não coleta assinaturas.
- Estilos só podem ser treinados a partir de amostras declaradas como do
  próprio usuário (`style.toml` com `owner_consent = true`).
- Todo arquivo exportado leva metadado `generator=manual-handwrite-ia`
  (PNG tEXt / PDF Producer). Não remover.

## Fluxo de desenvolvimento

- Python 3.11+, `uv`, `pytest`, `ruff`. Pacote em `src/manual_handwrite/`.
- TDD: um teste que falha, confirmar a falha, menor mudança, rodar teste focado
  e os gates completos, depois atualizar `docs/PROJECT-STATE.md` com o comando
  exato e o resultado.
- Gates: `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`.
- Dependências pesadas (torch, diffusers) só entram na fase v2, num extra
  opcional `[neural]`. O v1 roda com numpy, opencv-python-headless e Pillow.

## Regras para agentes

- Não invente APIs/contratos fora do plano. Se o plano for ambíguo, registre a
  decisão em `docs/PROJECT-STATE.md` e atualize o plano.
- Mantenha `docs/PROJECT-STATE.md` curto e factual; substitua o que ficou velho.
- Ao terminar, deixe o repo de forma que um agente novo recupere o contexto e o
  próximo teste só pelos documentos, sem o histórico do chat.
