# 04 — Fundamentos de ML e matérias relacionadas

## Para que serve esta trilha

Esta é uma trilha para quem estuda Ciência de Dados e IA e quer entender o que
seria **aprender** a letra neste projeto. Ela começa do zero, mas não trata o
`manual-handwrite-ia` como um exemplo abstrato: cada conceito é ligado ao
pipeline de imagens, dados, cobertura, avaliação e geração.

A distinção mais importante vem antes de qualquer fórmula:

- **O que já existe:** regras determinísticas, contratos e transformações
  locais. `normalize_page` converte uma página para escala de cinza e ajusta
  contraste; `segment_lines` encontra faixas de tinta; `source_pair` monta
  registros GOLD a partir de regiões e textos fornecidos; `analyze_text` conta
  caracteres, tokens e operadores; `optimize_coverage` seleciona snippets por
  cobertura; `harvest_critical_glyphs` só extrai glifos quando o alinhamento é
  exato; as métricas comparam textos literalmente; `scanify` degrada uma imagem
  com uma `seed` reproduzível. Essas funções seguem regras escritas e não
  ajustam parâmetros a partir de exemplos para fazer previsões.
- **O que ainda seria ML:** escolher ou produzir uma representação visual a
  partir de exemplos, estimar o estilo de uma nova amostra, gerar pixels
  condicionados ao texto e ao estilo, ou aprender parâmetros que minimizem uma
  função de erro em dados de treino. O backend de geração atual é
  `UnavailableBackend`: ele valida a solicitação e recusa gerar pixels. Não há
  modelo neural funcionando, pesos treinados ou comando `train` funcional.

Os experimentos abaixo devem usar fixtures sintéticas. Amostras reais de letra,
datasets pessoais e pesos ficam fora do Git e não são necessários para aprender
os fundamentos.

## Como usar cada parada

Em cada tópico, procure quatro coisas:

1. **Ideia simples:** a noção sem jargão.
2. **Analogia no pipeline:** onde ela aparece neste repositório.
3. **Micro-experimento ou pergunta verificável:** uma pequena prova, não uma
   opinião.
4. **Pré-requisito:** o que estudar antes, caso a ideia ainda não faça sentido.

Não confunda uma função que calcula uma estatística com um modelo que aprendeu.
`analyze_text` mede o que já está no texto; ele não adivinha o token ausente.

---

## 1. Dados, observações e rótulos

**Ideia simples.** Dados são observações; um rótulo é a resposta que queremos
associar a uma observação. Em aprendizagem supervisionada, o algoritmo vê
exemplos de entrada e resposta e tenta aprender a relação entre os dois. Uma
foto de uma linha é uma entrada; o texto escrito nessa linha pode ser o rótulo.

**Analogia no pipeline.** O projeto preserva `imagem + texto + região +
proveniência` no manifesto. No caminho `source-pair`, o chamador fornece as
regiões e os textos, `source.py` é validado como Python e os registros recebem
confiança 1.0, portanto `gold`. `silver` e `quarantine` representam graus de
confiança, não uma licença para transformar hipótese em verdade.

**Micro-experimento/pergunta.** Por que um recorte sem texto correspondente
não é automaticamente um exemplo de treino? Abra o contrato de
`ingest_source_pair`: quais informações ainda faltariam para saber qual
caractere está em cada pixel? Depois verifique nos testes que uma amostra
`quarantine` não entra no manifesto elegível por padrão.

**Pré-requisito.** Ler imagens como matrizes e entender a diferença entre um
arquivo, uma amostra e uma coluna de dados.

## 2. Features e representações

**Ideia simples.** Uma feature é uma medida ou representação usada pelo modelo.
Pode ser uma intensidade de pixel, um contorno, uma sequência de tokens ou um
vetor aprendido. A mesma informação pode ser representada de maneiras mais ou
menos úteis.

**Analogia no pipeline.** A página normalizada é uma representação visual
mais comparável que a foto original. `analyze_text` cria representações
explícitas de caracteres, tokens e operadores; `harvest_critical_glyphs`
retém crop, bounding box, índice do caractere e projeção vertical. Isso é
extração de evidência e engenharia de representação, não treinamento de uma
rede.

**Micro-experimento/pergunta.** Compare uma página com rotação e uma página
normalizada. Que variações são removidas e quais informações podem ser
perdidas? Em seguida, rode a análise de cobertura para `if x >= 2:` e liste
quais operadores foram observados. A lista é medida, não uma feature visual
aprendida.

**Pré-requisito.** Álgebra básica, matrizes e o fluxo imagem → array →
transformação.

## 3. Treino, validação e teste

**Ideia simples.** Treino ajusta parâmetros usando exemplos. Validação ajuda a
escolher configurações sem tocar no teste final. Teste mede o comportamento em
exemplos reservados. Se todos os exemplos forem usados para ajustar e avaliar,
não sabemos se o método funciona fora do que já viu.

**Analogia no pipeline.** Um futuro gerador de estilo deveria treinar com
amostras do titular e avaliar com páginas ou linhas separadas. O projeto hoje
não executa essa divisão para um modelo: há contratos e fixtures sintéticas.
O `PROJECT-STATE` registra que ainda não existe geração personalizada. A
avaliação implementada compara `reference_text` e `candidate_text`; ela não
mede estilo ou qualidade visual.

**Micro-experimento/pergunta.** Desenhe três caixas para uma futura coleção:
`train`, `validation`, `test`. Onde ficariam duas linhas da mesma página? Se
linhas quase idênticas da mesma folha caírem em caixas diferentes, o resultado
pode parecer melhor do que é. Confirme no `EvaluationReport` que `style` e
`quality` aparecem como métricas indisponíveis, e não como zeros inventados.

**Pré-requisito.** Dados e rótulos; leitura de tabelas e conjuntos.

## 4. Generalização

**Ideia simples.** Generalizar é funcionar em uma observação nova, não apenas
memorizar os exemplos vistos. Um modelo de letra deve lidar com uma palavra,
linha, escala ou pequena variação que não apareceu literalmente no treino.

**Analogia no pipeline.** Repetir a mesma amostra de `a` pode produzir uma
saída que memoriza aquela imagem. Cobertura de caracteres e variantes ajuda a
saber que evidência existe, mas cobertura não garante generalização. Um
benchmark honesto separaria páginas naturais mantidas fora do ajuste.

**Micro-experimento/pergunta.** Imagine dois resultados: A reproduz exatamente
as imagens de treino, mas falha em `ç`; B não copia nenhum pixel, mas mantém a
forma de `ç` em uma página não vista. Qual evidencia generalização? Escreva
antes quais páginas seriam reservadas e quais variações quer testar.

**Pré-requisito.** Treino-validação-teste e noção de distribuição de dados.

## 5. Overfitting e underfitting

**Ideia simples.** Overfitting é aprender detalhes acidentais do treino e
falhar em dados novos. Underfitting é usar uma representação ou modelo simples
demais para capturar o padrão. A diferença aparece ao comparar desempenho no
treino com desempenho fora dele.

**Analogia no pipeline.** Um banco que só tem um crop de cada símbolo pode
repetir uma forma específica; um sistema que ignora inclinação e espaçamento
pode ser simples demais. O futuro `GlyphBank` é uma estratégia determinística
planejada, não evidência de que um modelo resolveu esses dois problemas.

**Micro-experimento/pergunta.** Crie mentalmente um dataset com dez imagens da
mesma palavra escrita devagar. Qual seria o sinal de overfitting se a avaliação
usar outra palavra? Qual seria o sinal de underfitting se todas as letras
saíssem com a mesma geometria? Relacione cada resposta a uma divisão de dados.

**Pré-requisito.** Generalização e métricas separadas por partição.

## 6. Leakage (vazamento de informação)

**Ideia simples.** Leakage ocorre quando uma informação que não estaria
disponível no momento real do uso entra no treino ou na avaliação. Ele costuma
produzir resultados artificialmente bons.

**Analogia no pipeline.** Colocar recortes da mesma página em treino e teste,
calcular uma normalização usando o conjunto inteiro antes da divisão, ou usar o
texto de teste para escolher candidatos são formas de vazamento. A
proveniência de página e região existe justamente para permitir rastrear essa
separação. O `source_pair` preserva hash do `source.py`, mas isso não substitui
uma divisão experimental correta.

**Micro-experimento/pergunta.** Faça um quadro com `page_id` nas linhas e
`train/validation/test` nas colunas; existe algum `page_id` repetido? Se sim,
explique por que uma taxa de erro baixa pode ser enganosa. Pergunte também:
qual informação estava disponível antes da avaliação e qual só apareceu depois?

**Pré-requisito.** Partições e proveniência.

## 7. Baseline

**Ideia simples.** Baseline é um método simples e explícito que serve de
referência. Sem ele, não sabemos se um modelo sofisticado melhorou algo.

**Analogia no pipeline.** A primeira referência futura pode ser a composição
por glifos planejada no `GlyphBank`, enquanto o caminho atual ainda não renderiza
caligrafia. Para conteúdo, uma comparação literal fornece um baseline óbvio:
texto idêntico tem erro de edição zero e tokens críticos preservados. Para scan,
`scanify` com uma seed fixa é uma transformação determinística comparável.
Nenhum desses baselines é um modelo neural.

**Micro-experimento/pergunta.** Defina por escrito o baseline de cada objetivo:
conteúdo, estilo, qualidade e layout. Depois marque quais já têm medição no
código. A resposta correta hoje é que conteúdo tem métricas; estilo e qualidade
estão indisponíveis no `EvaluationReport`, e geração personalizada ainda não
está disponível.

**Pré-requisito.** Métricas e definição do objetivo.

## 8. Loss e objetivo

**Ideia simples.** Uma função de loss transforma uma diferença em um número que
o treinamento tenta reduzir. O objetivo precisa dizer o que importa: fidelidade
ao texto, aparência do estilo, legibilidade e limites da página podem entrar
em objetivos diferentes, com trade-offs.

**Analogia no pipeline.** `normalized_character_error_rate` é uma medida de
erro de conteúdo, não uma loss usada para treinar. `critical_token_accuracy`
mede tokens em sequência e trata inserções e omissões como discordâncias. Um
futuro gerador não deveria melhorar aparência sacrificando `=` por `==` ou
apagando acentos; o contrato do projeto dá prioridade ao texto solicitado.

**Micro-experimento/pergunta.** Compare dois candidatos: um tem texto perfeito
mas leve artefato visual; outro parece manuscrito, mas troca `=` por `==`.
Qual objetivo vence em uma ferramenta para escrever código? Especifique uma
regra antes de olhar o resultado e explique por que uma única métrica seria
insuficiente.

**Pré-requisito.** Erro absoluto, proporções e métricas.

## 9. Otimização e gradiente

**Ideia simples.** Otimização procura parâmetros que melhoram o objetivo. Em
modelos diferenciáveis, o gradiente indica uma direção local de aumento; para
reduzir a loss, o ajuste costuma andar na direção oposta, em passos controlados
pela taxa de aprendizado.

**Analogia no pipeline.** Nada em `analyze_text`, `optimize_coverage` ou
`scanify` executa backpropagation. O otimizador de cobertura é uma seleção
**gulosa**: calcula ganho de símbolos novos por custo de caracteres, escolhe o
melhor candidato de forma determinística e repete. Isso é otimização
combinatória simples, não descida de gradiente nem aprendizado de pesos.

**Micro-experimento/pergunta.** Leia `optimize_coverage` e identifique: qual é
o custo, qual é o ganho, como empates são resolvidos e por que candidatos sem
cobertura nova são omitidos? Depois descreva uma situação em que uma escolha
localmente melhor não produz a cobertura globalmente mínima.

**Pré-requisito.** Funções, gráficos simples e aritmética de proporções; cálculo
é o próximo passo para redes neurais.

## 10. Métricas e leitura crítica

**Ideia simples.** Métrica é uma regra de medição; não é sinônimo de qualidade
nem substitui a pergunta científica. Escolher a métrica muda o que o sistema
parece otimizar.

**Analogia no pipeline.** O projeto mede erro de edição literal e acurácia de
tokens críticos. O relatório preserva os dois textos e a proveniência; não
normaliza Unicode, corrige espaços ou faz correção ortográfica escondida. Os
campos `unavailable_metrics` deixam claro que estilo e qualidade ainda não
foram medidos.

**Micro-experimento/pergunta.** Calcule, à mão, a diferença entre uma troca de
um caractere em uma string curta e em uma longa. Depois compare um caso em que
o texto tem CER baixo, mas um operador Python crítico está errado. Por que
`critical_token_accuracy` existe ao lado do CER?

**Pré-requisito.** Frações, distância de edição e sequências de tokens.

## 11. Distribuição, mudança de domínio e viés/variância

**Ideia simples.** A distribuição descreve quais exemplos e variações aparecem
e com que frequência. Mudança de distribuição ocorre quando o uso real difere
do treino. Viés é erro sistemático por uma hipótese restritiva; variância é a
sensibilidade a pequenas mudanças nos dados. O equilíbrio entre ambos afeta a
generalização.

**Analogia no pipeline.** Folhas escaneadas em boa luz não representam
necessariamente fotos de celular, e código sem acentos não representa português.
Os presets `scanner-escritorio`, `foto-celular`, `xerox-velho` e `limpo` simulam
condições diferentes, mas `scanify` não aprende a distribuição nem prova que o
modelo de letra seria robusto a elas. `coverage` revela lacunas do vocabulário;
não revela sozinho viés visual.

**Micro-experimento/pergunta.** Liste as dimensões que podem mudar: inclinação,
pressão, papel, iluminação, acentos, símbolos e comprimento da linha. Qual
conjunto está sub-representado? Uma saída sempre com o mesmo formato sugere
viés alto ou variância alta? Justifique com dados que você mediria.

**Pré-requisito.** Generalização, estatística descritiva e partições.

## 12. Embeddings — apenas a intuição

**Ideia simples.** Um embedding representa um item como um vetor em que itens
com relações úteis podem ficar próximos. A proximidade não é uma verdade
mágica: depende dos dados, da tarefa e do modo como o vetor foi aprendido.

**Analogia no pipeline.** Um futuro modelo poderia representar trechos de
imagem, caracteres ou estilos em vetores para comparar exemplos. Hoje o
projeto usa estruturas explícitas: `Counter` para cobertura, crops para
candidatos e metadados de proveniência. Não há embedding nem busca vetorial no
código lido, e não se deve inventar uma API para ele.

**Micro-experimento/pergunta.** Imagine vetores de três variantes de `a` e de
três variantes de `+`. Que propriedade você desejaria que a distância refletisse:
forma, papel, posição ou texto? Como verificaria se a proximidade escolhida é
útil para uma nova página? Se não consegue definir o teste, o embedding ainda
não é uma solução.

**Pré-requisito.** Vetores, distância e normalização; redes neurais são o
próximo aprofundamento, não um requisito para entender o pipeline atual.

## 13. Redes neurais e fine-tuning como próximos passos

**Ideia simples.** Uma rede neural é uma composição de funções parametrizadas.
Durante o treino, os parâmetros são ajustados para reduzir um objetivo. Fine-
tuning começa com um modelo pré-treinado e adapta seus parâmetros, ou parte
deles, a uma tarefa/dataset específico.

**Analogia no pipeline.** A Fase 5 prevê um adaptador neural opcional para um
modelo few-shot, sob comando explícito, com pesos e amostras fora do Git. Esse
backend teria de consumir um `StylePack` consentido, produzir pixels e registrar
proveniência. O plano também prevê fallback do `GlyphBank` para caracteres com
pouca cobertura. Isso é trabalho futuro; `generation/__init__.py` hoje só define
contratos e uma indisponibilidade explícita.

**Micro-experimento/pergunta.** Antes de usar uma rede, escreva o contrato de
entrada, saída, seed, consentimento, divisão de dados e métricas. Depois rode o
teste de geração e confirme que `UnavailableBackend` lança
`BackendUnavailableError` e não devolve uma imagem de fonte do sistema. Esse
resultado é uma proteção correta, não uma falha de modelo.

**Pré-requisito.** Todos os tópicos anteriores, Python/NumPy, álgebra linear,
probabilidade, loss e avaliação experimental.

## 14. Álgebra linear

**Ideia simples.** Vetores armazenam listas ordenadas de números; matrizes
organizam vetores. Produto, transposição, norma e projeção descrevem
transformações e comparações em dados tabulares e imagens.

**Analogia no pipeline.** Uma imagem em tons de cinza pode ser vista como uma
matriz de pixels. `normalize_page` usa arrays NumPy e percentis; `scanify`
transforma matrizes e preserva forma e tipo quando recebe um array. Bounding
boxes são coordenadas, e uma projeção vertical resume tinta por coluna para
localizar componentes.

**Micro-experimento/pergunta.** Desenhe uma matriz 3×4 e marque quais índices
formam uma região `(x0, y0, x1, y1)`. Por que trocar linha e coluna pode deslocar
um recorte? Em seguida explique por que uma projeção vertical pode unir duas
letras que se tocam.

**Pré-requisito.** Operações básicas com números e índices; depois estude
produto matricial, norma e autovetores.

## 15. Probabilidade e estatística

**Ideia simples.** Probabilidade representa incerteza; estatística descreve dados
e ajuda a inferir além da amostra. Média, mediana, variância, quantis e
intervalos de incerteza respondem perguntas diferentes.

**Analogia no pipeline.** A confiança de uma hipótese de transcrição precisa
ser tratada como evidência, não como verdade. O protocolo separa `gold`,
`silver` e `quarantine`; o parser Python é um sinal de consistência, não prova
visual. `normalize_page` usa percentis 1 e 99 para contraste, e
`scanify` usa uma seed para tornar o ruído reproduzível.

**Micro-experimento/pergunta.** Para uma lista de intensidades com um outlier,
compare média e mediana. Qual representa melhor o fundo? Para cinco hipóteses
com confiança 0.9, a soma das confianças prova que uma está correta? Não: a
calibração e a independência das evidências ainda precisariam ser estudadas.

**Pré-requisito.** Frações, funções e leitura de gráficos.

## 16. Processamento digital de imagens

**Ideia simples.** Uma imagem digital é uma grade de amostras. Pré-processar
pode corrigir orientação, converter cores, ajustar contraste, separar regiões e
reduzir variações irrelevantes; cada operação também pode remover informação.

**Analogia no pipeline.** `normalize_page` aplica orientação EXIF, tons de
cinza e contraste. `segment_lines` marca linhas por limiar e tolerância de
lacunas. `harvest_critical_glyphs` usa projeção vertical e recusa quando o
número de componentes não bate com a transcrição. `scanify` transforma uma
imagem limpa com textura, ruído, geometria e compressão, sem alterar o texto.

**Micro-experimento/pergunta.** Rode os testes de scan com a mesma imagem e
seed repetida; depois troque a seed. Os pixels devem repetir no primeiro caso,
mas a degradação pode mudar no segundo. Pergunte: a transformação mudou o
conteúdo ou apenas a aparência? Teste também uma imagem vazia na colheita de
glifos e observe `blank_image`, não um palpite.

**Pré-requisito.** Matrizes, intensidade, coordenadas e Python/NumPy.

## 17. Python, NumPy e leitura de código científico

**Ideia simples.** Python expressa o experimento; NumPy representa arrays e
operações vetorizadas; Pillow faz a ponte com imagens. A habilidade central é
saber quais tipos entram, quais saem e quais invariantes são preservados.

**Analogia no pipeline.** Leia as assinaturas e docstrings reais antes de
chamar algo: `scanify(image, seed, preset)` aceita Pillow e arrays; `analyze_text`
retorna `CoverageReport`; `evaluate_content` retorna `EvaluationReport`;
`optimize_coverage` escolhe snippets segundo custo e ganho. O uso de `seed`,
objetos imutáveis e resultados serializáveis torna os experimentos auditáveis.

**Micro-experimento/pergunta.** Execute:

```bash
uv run python -c "from manual_handwrite.coverage import analyze_text; print(analyze_text('for i in range(3):').as_dict())"
```

Explique cada parte do dicionário e a diferença entre `tokens` e
`missing_operators`. Depois leia um teste correspondente e diga qual
comportamento é contrato e qual ainda é hipótese.

**Pré-requisito.** Python básico: funções, exceções, listas, dicionários e
módulos.

## 18. Reprodutibilidade, proveniência e ética dos dados

**Ideia simples.** Um resultado reproduzível pode ser refeito com código,
versão, dados, parâmetros e seed conhecidos. Proveniência responde de onde um
dado veio e quais transformações recebeu. Em dados pessoais, consentimento e
limites de uso fazem parte do experimento.

**Analogia no pipeline.** Registros preservam `page_id`, região, origem e hash
do `source.py`; `StylePack` exige `owner_consent = true`, referências relativas
e hash do dataset; a execução padrão é local, sem rede; saídas levam
`generator=manual-handwrite-ia`. A regra do projeto é não coletar nem gerar
assinaturas e usar somente a letra do próprio titular.

**Micro-experimento/pergunta.** Rode duas vezes um teste de `scanify` com a
mesma seed e compare os arrays; registre preset e seed. Em seguida explique por
que uma imagem sem `page_id`, origem e consentimento não deveria entrar em um
dataset pessoal, mesmo que o código consiga abri-la.

**Pré-requisito.** Python, hashes, arquivos e noções de privacidade/ética em
ciência de dados.

---

## Ordem de estudo recomendada

1. **Orientação no projeto:** leia `docs/COMO-FUNCIONA.md`,
   `docs/ARCHITECTURE.md` e o `checkpoint-05`; desenhe o pipeline e marque o
   que é regra determinística versus o que é futuro ML.
2. **Python e imagens:** pratique arrays, pixels, coordenadas, orientação,
   contraste e segmentação; acompanhe os capítulos `docs/learning/01` e os
   módulos `ingest` e `scan`.
3. **Dados supervisionados:** estude observação, rótulo, GOLD/SILVER/
   quarantine, regiões e proveniência; acompanhe `docs/learning/02` e
   `03`, `data/source_pair.py` e `style`.
4. **Representação e cobertura:** conte caracteres, tokens e operadores; estude
   features e seleção gulosa; acompanhe `docs/learning/04` e `coverage`.
5. **Avaliação científica:** treine divisão por página, generalização,
   overfitting, leakage, baseline, loss e métricas; leia `evaluation` e
   escreva um protocolo que não use amostras do teste para ajustar nada.
6. **Matemática:** revise álgebra linear, probabilidade e estatística junto de
   cada experimento de imagem e de cobertura, em vez de estudá-las só como
   fórmulas isoladas.
7. **Embeddings e redes:** só depois estude representações vetoriais, redes,
   otimização por gradiente e fine-tuning. Primeiro defina contratos,
   consentimento, partições, métricas e fallback; depois considere a Fase 5.
8. **Reprodutibilidade:** repita os testes com seed, registre versão e
   proveniência e confirme os gates locais: `uv run pytest -q`, `uv run ruff
   check .` e `uv run ruff format --check .`.

## Critérios de domínio

Você domina a trilha quando consegue, sem consultar uma definição pronta:

- desenhar o fluxo de uma imagem até um eventual modelo e apontar onde estão
  rótulos, features, partições e métricas;
- explicar por que `source-pair` e `analyze_text` são determinísticos e por que
  nenhum deles é um modelo treinado;
- montar uma divisão treino/validação/teste por página, detectar leakage e
  justificar uma baseline;
- distinguir loss de métrica, e explicar por que CER sozinho não protege
  operadores Python críticos;
- diagnosticar overfitting, underfitting, mudança de distribuição e
  compromissos de viés/variância com um experimento verificável;
- explicar uma imagem como matriz, uma projeção como resumo e uma seed como
  parte da reprodutibilidade;
- interpretar `gold`, `silver` e `quarantine` sem transformar confiança em
  verdade automática;
- dizer exatamente o que o `EvaluationReport` mede e o que marca como
  indisponível;
- descrever embeddings, redes neurais e fine-tuning apenas como próximos
  passos, sem afirmar que há um modelo neural funcionando neste projeto;
- propor um experimento local, sintético, ético e repetível que registre dados,
  código, parâmetros, seed, métrica, resultado e limitações.

O sinal final de domínio não é saber dizer “há IA” no nome do projeto. É saber
explicar, com evidência, qual transformação aconteceu, qual hipótese foi
medida, qual incerteza permaneceu e qual parte ainda não foi implementada.
