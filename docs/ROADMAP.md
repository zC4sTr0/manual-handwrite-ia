# Roadmap futuro

Este documento descreve trabalho **não implementado**. A ordem abaixo é a
ordem de dependências proposta e não substitui o estado canônico de
[`docs/PROJECT-STATE.md`](PROJECT-STATE.md). O histórico das fases do plano de
implementação permanece em [`docs/IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md).

## Ordem e dependências

1. **Fase 1 — base de scan + Data Factory (estado atual).** O núcleo offline de
   scan, manifests, cobertura, ingestão de pares GOLD e contratos de segurança
   está implementado; ingestão/segmentação de páginas reais e adaptador VLM ainda
   dependem de amostras naturais consentidas.
2. **Fase 2 — coleta e ingestão real (futuro).** Depende de dados do titular,
   template de coleta e contrato de ingestão; inclui correção de perspectiva,
   binarização, recorte e rotulagem.
3. **Fase 3 — síntese v1 por glifos (futuro).** Depende de dataset aprovado,
   `GlyphBank`, composição de página e critérios de qualidade; a CLI `write`
   ainda não existe.
4. **Fase 4 — qualidade percebida (futuro).** Depende de páginas geradas e de
   teste cego local.
5. **Fase 5 — modelo neural v2 (futuro).** Depende de backend opcional,
   dataset pessoal, ambiente GPU, licenças verificadas e benchmark reproduzível;
   consulte [`docs/RESEARCH.md`](RESEARCH.md) e o
   [`landscape de modelos`](research/2026-model-landscape.md).

Os nomes preservam a história do `IMPLEMENTATION-PLAN`; a Fase 1 atual combina
na prática a base de scan e os contratos iniciais da Data Factory, conforme o
`PROJECT-STATE` vigente.

## Ideias posteriores, sem compromisso de implementação

- Captura por tablet ou caneta digital para traços (depende de dados online e de
  um novo contrato, não de scans convertidos silenciosamente).
- Editor web local com pré-visualização dos presets de scan.
- Várias canetas e cores, rasuras realistas, folhas pautadas/quadriculadas e
  cadernos com espiral.
- Exportação de traços em SVG/G-code para plotter (depende de trajetória e
  validação de segurança).

Nenhum item acima autoriza upload, coleta de assinatura ou entrada de dados de
terceiros. Dados pessoais, pesos e saídas continuam fora do Git.
