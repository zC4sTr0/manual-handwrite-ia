# Ética e privacidade

A letra de uma pessoa é dado pessoal e pode ser usada para fraude. Estas regras
valem para o código e para os agentes que trabalham no repositório.

## Uso permitido

- Gerar textos na **sua própria** letra: cartas, anotações, cadernos, arte,
  mockups e estudos.

## Proibido (reforçado em código quando possível)

- Gerar assinaturas ou rubricas.
- Treinar estilo com a letra de outra pessoa sem consentimento documentado.
- Produzir documentos que se passem por originais para enganar terceiros
  (contratos, receitas, atestados, cheques, provas).

## Salvaguardas técnicas

- `style.toml` exige `owner_consent = true`; `train` recusa sem isso.
- Entradas marcadas como assinatura são recusadas.
- Metadado `generator=manual-handwrite-ia` em toda exportação.
- `samples/`, `dataset/`, `styles/`, `models/` e `output/` fora do git; CI usa só fixtures sintéticas.
- Sem rede por padrão.
