# StylePack, GlyphBank e geração da letra

Este guia explica como o projeto separa **o que deve ser escrito**, **a aparência da escrita** e **a organização da página**. Ele é destinado a quem está começando e também serve como referência dos contratos que já existem no código.

> **Importante:** a geração personalizada completa ainda não está implementada. A arquitetura e os contratos existem para permitir a implementação incremental da Fase 3. O caminho padrão continua local e não envia amostras para a rede.

## 1. A ideia em uma frase

O programa recebe um texto, consulta evidências consentidas da letra do próprio usuário, produz um ou mais candidatos, avalia o conteúdo e, quando houver um renderizador real, posiciona as linhas em uma página A4 antes de exportar.

A aparência de scanner é outra etapa: `scanify` transforma uma imagem pronta, mas não aprende a letra nem decide o texto.

```text
conteúdo solicitado
        +
StylePack (proveniência e consentimento do estilo)
        |
        v
backend de escrita
        |
        v
candidatos
        |
        +--> avaliação de conteúdo/estilo/qualidade
        |
        v
layout A4
        |
        v
PNG/PDF + metadado do gerador
        |
        v
scanify opcional
```

## 2. Vocabulário básico

### Conteúdo

É o texto literal que precisa aparecer na saída. Inclui letras, acentos, espaços, pontuação e, no caso de código, símbolos com significado sintático. Se a entrada é `for item in lista:`, o gerador não pode trocar `:` por outro símbolo, remover um espaço relevante ou “corrigir” o texto porque uma imagem ficaria mais bonita.

No código, o conteúdo é recebido como `text: str` por um backend e é comparado literalmente pelas métricas de avaliação. Não há normalização Unicode, limpeza de espaços ou correção ortográfica escondida.

### Estilo

É a maneira como o titular costuma escrever: formas dos caracteres, escala, inclinação, linha de base, espaçamento, variações entre ocorrências e ligações cursivas simples. Estilo não é o texto e não é o efeito de papel escaneado.

Por regra do projeto, as amostras de estilo devem ser do próprio usuário e declarar `owner_consent = true`. O sistema não é gerador de assinaturas nem ferramenta para copiar a letra de outra pessoa.

### Glyph (glifo)

Um **glyph** é a evidência visual de um caractere ou símbolo: normalmente um recorte de imagem associado a uma posição na transcrição. `a`, `A`, `ç`, `=` e `(` são símbolos diferentes, mesmo quando fazem parte da mesma palavra ou linha.

O módulo `manual_handwrite.style.glyphs` define os registros de extração:

- `GlyphProvenance`: guarda `source_text`, `character_index`, `bbox` e o método de segmentação;
- `GlyphCandidate`: guarda `symbol`, a imagem (`numpy.ndarray`), `bbox` e a proveniência;
- `UnresolvedAlignment`: registra por que uma associação não foi adivinhada;
- `GlyphHarvest`: agrupa `candidates` e `unresolved`.

A função existente `harvest_critical_glyphs(image, transcription, threshold=200)` é deliberadamente conservadora. Ela aceita imagem Pillow ou array NumPy, faz uma projeção vertical e só devolve recortes de símbolos críticos quando o número de componentes coincide exatamente com o número de caracteres não vazios. Se houver imagem em branco ou divergência de componentes, retorna um `UnresolvedAlignment`, em vez de inventar uma associação.

A função também pode ser chamada pelo alias `harvest_glyphs`. O conjunto atual de símbolos críticos inclui, entre outros, `()[]{}:,.=+-*/%_<>!&|^~;#`, aspas, barra invertida e `@`. Essa extração é evidência/diagnóstico; ela ainda não é um renderizador de palavras.

### GlyphBank

O **GlyphBank** será o banco de variantes de glifos usados pela síntese v1. Ele deve selecionar exemplos reais de cada símbolo e recombiná-los com pequenas variações controladas. O plano da Fase 3 especifica:

1. escolher variantes;
2. evitar a mesma variante consecutivamente;
3. aplicar jitter de linha de base, inclinação e escala (aproximadamente 4%);
4. controlar espaçamento de letras e palavras;
5. fazer conexões cursivas simples;
6. sinalizar ou recusar caracteres sem cobertura suficiente.

**Estado atual:** não existe uma classe `GlyphBank` nem um método público de composição implementado em `style/glyphs.py`. O arquivo contém a extração conservadora descrita acima. Portanto, exemplos de API como `GlyphBank.render_word(...)` não devem ser tratados como comandos disponíveis.

### StylePack

O **StylePack** é o pacote versionado que identifica uma seleção segura de referências de estilo. Ele contém metadados e caminhos relativos; não contém bytes de imagens nem lê automaticamente os arquivos referenciados.

A classe real `manual_handwrite.style.StylePack` exige:

- `references`: tupla não vazia de `StyleReference`;
- `dataset_id`: identificador não vazio;
- `dataset_hash`: hash não vazio;
- `coverage`: objeto/dicionário;
- `scan_preset`: nome não vazio;
- `owner_consent=True`;
- `version`: versão não vazia.

Cada `StyleReference` contém `path` e `provenance`. O caminho deve ser relativo: caminhos absolutos, drives Windows e componentes `..` são recusados. O carregamento também recusa marcadores de assinatura nos metadados (`signature`, `is_signature`, `signature_marked` ou `is_signature_marked` com valor `true`).

O formato JSON produzido por `pack.to_dict()` tem esta forma contratual:

```json
{
  "version": "1",
  "owner_consent": true,
  "references": [
    {
      "path": "dataset/index.jsonl",
      "provenance": {"source": "folha-01"}
    }
  ],
  "dataset": {"id": "minha-letra", "hash": "..."},
  "coverage": {"characters": ["a", "b"]},
  "scan_preset": "scanner-escritorio"
}
```

Os nomes dos valores de exemplo são ilustrativos; o formato e as validações são os contratos reais. Para ler e escrever, existem `load_stylepack(path)` e `write_stylepack(path, pack)`, além dos aliases `load_stylepack_manifest`, `write_stylepack_manifest`, `load_manifest` e `write_manifest`. Um erro de formato ou segurança levanta `StylePackError`.

Um StylePack não é uma fonte instalada, não é uma assinatura e não transforma sozinho as imagens em texto. Ele identifica quais dados consentidos um backend pode consultar e registra cobertura, hash, versão e preset associado.

### Backend

Um **backend** é a implementação concreta que recebe conteúdo e estilo e tenta gerar candidatos. A fronteira real está em `manual_handwrite.generation`:

```python
class HandwritingBackend(Protocol):
    @property
    def capabilities(self) -> BackendCapabilities: ...

    def generate(
        self,
        text: str,
        stylepack: StylePack,
        *,
        seed: int,
        count: int,
    ) -> tuple[Candidate, ...]: ...
```

`BackendCapabilities` declara `name`, `version`, disponibilidade, suporte a `seed`, `count` e `StylePack`, se renderiza manuscrito, se exige rede e se exige o extra neural. Isso impede que um componente se apresente como gerador manuscrito sem realmente renderizar manuscrito.

O backend atualmente disponível é `UnavailableBackend`. Ele valida a requisição e então levanta `BackendUnavailableError` com a mensagem de que não há backend real e nenhum texto foi renderizado. Ele não substitui a letra por uma fonte de sistema.

### Candidato

Um **candidato** é uma possibilidade numerada de saída para o mesmo texto e estilo. O contrato atual `Candidate` contém somente:

- `text: str`;
- `seed: int`;
- `index: int` não negativo;
- `backend: str` não vazio.

Os pixels não fazem parte desse contrato v1. Um futuro backend deverá documentar como ligar o artefato raster ao candidato. Não se deve interpretar a existência de um `Candidate` como prova de que uma página manuscrita foi renderizada.

### Avaliação

A **avaliação** verifica se o candidato respeitou o texto e, futuramente, se a aparência e o layout são adequados.

Hoje `evaluation.metrics` implementa métricas determinísticas de conteúdo:

- `edit_distance(reference, candidate)`: distância de Levenshtein literal;
- `normalized_character_error_rate(...)`: distância dividida pelo tamanho da referência; retorna `None` para referência vazia;
- `critical_token_accuracy(...)`: compara tokens críticos de Python em ordem, contando inserções e omissões;
- `character_error_rate`: alias do nome normalizado.

`evaluate_content(reference_text, candidate_text, provenance=...)` devolve `EvaluationReport`. O relatório preserva as duas strings, as métricas e a proveniência. `style` e `quality` aparecem explicitamente em `unavailable_metrics`, porque ainda precisam de imagem renderizada e/ou avaliação humana. Não são preenchidas com valores inventados.

### Layout

**Layout** é a geometria da página, não o estilo do traço. Ele decide onde as linhas ficam, quando quebrar uma linha e quando começar uma nova página.

`manual_handwrite.layout` fornece:

- `PageSpec`: A4 por padrão, 300 DPI, dimensões e margens calculadas em pixels;
- `LayoutLine`: texto, posição `x`/`y` e largura medida;
- `PageLayout`: lista de páginas e o `PageSpec` usado;
- `wrap_text(text, max_width, font)`: quebra por avanço medido e divide uma palavra que excede a largura;
- `layout_text(text, spec, font)`: aplica recuo no primeiro trecho do parágrafo, mede linhas e quebra por capacidade da página.

As constantes são `A4_WIDTH_MM = 210.0` e `A4_HEIGHT_MM = 297.0`. A geometria padrão usa margens de 20 mm e altura de linha de 48 pixels. O alias `compose_layout` aponta para `layout_text`; `A4PageSpec` aponta para `PageSpec`.

## 3. Fluxo completo, sem misturar responsabilidades

### 3.1 Coleta e ingestão

A folha preenchida pelo titular é normalizada, segmentada e associada ao texto. O manifesto JSONL preserva imagem, texto, regiões e proveniência. O caminho `source-pair` é especialmente importante quando já existe um `source.py`: o código-fonte é a referência do conteúdo, em vez de tentar redescobri-lo por OCR.

A ingestão precisa manter `owner_consent=true`. Amostras reais, datasets, estilos, modelos e saídas ficam fora do Git e não entram em logs de CI.

### 3.2 Cobertura

A cobertura responde quais caracteres, acentos e operadores já têm evidência. Ela deve orientar a captura adaptativa e evitar que a geração descubra tarde demais que não há `ç`, `ã`, `=` ou outro símbolo necessário.

Cobertura insuficiente não deve ser escondida por uma fonte de sistema ou por uma substituição silenciosa. O resultado correto é pedir mais amostras, sinalizar a lacuna ou recusar a geração.

### 3.3 Construção do StylePack

O StylePack reúne referências relativas, identificador e hash do dataset, cobertura, preset de scan, versão e consentimento. O hash identifica a versão dos dados; a cobertura ajuda a decidir se o texto pode ser gerado; o preset descreve a aparência de scan desejada, que continua sendo uma etapa posterior.

O carregador lê apenas o manifesto. Cabe ao consumidor acessar as referências locais e construir o banco de glifos sem quebrar as regras de proveniência.

### 3.4 Seleção pelo GlyphBank

Na v1 planejada, o GlyphBank recebe o texto já aprovado e busca variantes de cada símbolo no dataset do StylePack. A seleção deve ser determinística quando recebe uma semente e deve evitar repetições consecutivas. Jitter e espaçamento precisam ser pequenos o bastante para conservar legibilidade e a identidade da letra.

A seleção não pode alterar o conteúdo. Uma ligação cursiva é uma transformação visual entre caracteres, não uma licença para remover ou inserir caracteres.

### 3.5 Geração de candidatos

O backend recebe `text`, `stylepack`, `seed` e `count`. `count` deve ser inteiro positivo; `seed` deve ser inteiro, sem coerção silenciosa de booleanos. Cada candidato recebe `index` e o nome do backend para permitir rastreabilidade.

A ideia futura é gerar várias versões da mesma linha ou página. O avaliador pode então escolher a melhor que ainda esteja correta. Um candidato visualmente natural não pode vencer um candidato literal se perdeu um operador ou um acento importante.

### 3.6 Avaliação e escolha

A primeira barreira é conteúdo: comparar o texto original com o texto do candidato. Para código, `critical_token_accuracy` dá visibilidade a operadores e tokens importantes. A avaliação de estilo e qualidade só é válida quando há um artefato manuscrito real; hoje o relatório registra essas dimensões como indisponíveis.

Depois, com renderização implementada, a avaliação deve considerar:

1. **conteúdo:** caracteres, espaços e tokens corretos;
2. **estilo:** semelhança com amostras do próprio titular;
3. **qualidade:** legibilidade e ausência de artefatos graves;
4. **layout:** linhas e margens respeitadas.

A proveniência do candidato e do StylePack deve acompanhar o relatório.

### 3.7 Layout e exportação

O texto renderizado é colocado em `PageSpec`. O layout mede avanços, quebra palavras longas, aplica recuo e inicia novas páginas conforme a capacidade vertical. O backend não deve resolver paginação internamente.

A exportação deve preservar `generator=manual-handwrite-ia` no PNG (tEXt) ou no PDF (Producer). Esse metadado é obrigatório e não deve ser removido.

### 3.8 Scan opcional

Só depois de existir uma imagem limpa faz sentido aplicar `scanify`. Os presets previstos incluem `scanner-escritorio`, `foto-celular`, `xerox-velho` e `limpo`. O efeito pode aplicar variação de tinta, textura, geometria, iluminação, ruído, curva de tom e JPEG.

O scan simulator não altera o texto, não escolhe glifos e não aprende estilo. Para depurar, primeiro compare a imagem manuscrita limpa; só depois investigue o preset de scan.

## 4. Comandos reais e comandos planejados

### Comandos funcionais conferidos na CLI atual

A entrada é `handwrite` (`manual_handwrite.cli`). Os comandos que já estão registrados e executáveis são:

```bash
uv run handwrite scanify in.png \
  --preset foto-celular \
  --seed 7 \
  --out out.jpg

uv run handwrite coverage arquivo.py --out coverage.json

uv run handwrite source-pair pagina.png arquivo.py regions.json \
  --owner-consent \
  --out manifesto.jsonl
```

`source-pair` exige `--owner-consent`; o JSON de regiões pode ser um objeto com listas `regions`/`line_regions` e `texts`, ou uma lista de entradas com `region` e, opcionalmente, `text`.

### Comandos previstos no plano, ainda não disponíveis na CLI atual

O plano de implementação prevê, mas a função `build_parser()` atual ainda não registra:

```bash
uv run handwrite template --out folha-modelo.pdf
uv run handwrite ingest samples/folha-01.jpg
uv run handwrite train --style minha-letra
uv run handwrite write "Uma anotação" \
  --style minha-letra \
  --scan-preset scanner-escritorio \
  --out anotacao.pdf
```

Esses comandos são contratos de produto/fases futuras, não instruções para fingir que a geração já funciona. Em particular, `handwrite write` não deve ser anunciado como funcional enquanto não houver backend real e GlyphBank implementado.

## 5. Exemplo conceitual de uma geração futura

Considere o pedido literal:

```text
A soma é 2 + 2 = 4.
```

O fluxo esperado é:

1. o conteúdo entra sem correção;
2. o StylePack é carregado e validado;
3. a cobertura é consultada para letras acentuadas, números, `+`, `=` e pontuação;
4. o GlyphBank seleciona variantes para cada símbolo coberto;
5. o backend gera candidatos com uma semente e uma contagem;
6. o avaliador rejeita qualquer candidato que perca `é`, `+` ou `=`;
7. o layout mede a linha dentro da caixa de conteúdo A4;
8. a exportação escreve PNG/PDF com `generator=manual-handwrite-ia`;
9. `scanify` pode ser aplicado depois, se desejado.

Se `é` não estiver coberto, a saída correta é pedir uma amostra ou sinalizar a limitação. Usar uma fonte de computador para completar o caractere violaria a intenção do pipeline.

## 6. Limitações atuais e direção futura

### Limitações atuais

- `GlyphBank` como gerador ainda não existe; `style/glyphs.py` faz apenas colheita conservadora de glifos críticos.
- Não há renderizador de manuscrito completo no pacote.
- `UnavailableBackend` recusa a geração e não produz pixels.
- `Candidate` não carrega raster; sua forma atual representa identidade e proveniência mínimas.
- O relatório de avaliação cobre conteúdo, mas marca estilo e qualidade como indisponíveis.
- Os comandos de `template`, `ingest`, `train` e `write` ainda são etapas do plano, não comandos registrados hoje.
- Conexões cursivas, acentos compostos e cobertura de palavras longas precisam de implementação e testes visuais.
- Testes de contrato não substituem comparação cega com páginas reais do titular.

### Futuro planejado

A Fase 3 implementa síntese por glifos, composição, `handwrite write` e exportação. A Fase 4 mede a qualidade percebida e ajusta parâmetros por estilo em `style.toml`. A Fase 5 pode adicionar um backend neural opcional (`[neural]`), com fallback para `GlyphBank` em caracteres pouco cobertos.

Dependências pesadas como Torch e Diffusers não pertencem ao caminho v1. Um backend neural futuro deve continuar explícito, local por padrão e rastreável; download de pesos públicos só ocorre por comando explícito.

## 7. Erros comuns e diagnóstico

### “O texto ficou diferente”

Verifique primeiro a entrada, o manifesto e a transcrição. Compare as strings literalmente e consulte `character_error_rate` e `critical_token_accuracy`. Não comece ajustando escala ou inclinação.

### “A letra não parece a do titular”

Confira `owner_consent`, `dataset_id`, `dataset_hash`, referências relativas, cobertura e separação entre treino e avaliação. Um StylePack válido identifica dados seguros, mas não garante que o renderizador já exista nem que a cobertura seja suficiente.

### “O sistema aceitou uma imagem ambígua”

Isso é sinal de implementação incorreta. `harvest_critical_glyphs` deve devolver `component_count_mismatch`, `blank_image` ou outro `UnresolvedAlignment` quando não consegue alinhar com segurança. Não se deve adivinhar o glifo.

### “O candidato existe, mas não há imagem”

Isso é compatível com o contrato atual: `Candidate` só contém identidade e proveniência. Verifique `BackendCapabilities.renders_handwriting` antes de tratar o resultado como manuscrito.

### “A linha saiu cortada”

Investigue `PageSpec`, margens, `content_width_px`, `wrap_text` e capacidade vertical de `layout_text`. Não coloque regras de quebra de página dentro do GlyphBank.

### “A página parece um computador perfeito”

Primeiro confirme que houve um renderizador de manuscrito real. Só então ajuste `scanify`. Scan não converte texto de fonte em letra do usuário.

### “O teste passou, mas a escrita ficou ruim”

Testes automatizados verificam contratos, formatos, limites e determinismo. A qualidade visual exige amostras reais fora do treino, inspeção do titular e, quando aplicável, avaliação cega. Não invente uma métrica de estilo para encobrir a ausência de renderização.

### “O StylePack carregou um caminho perigoso”

O carregador deve recusar caminhos absolutos, drives Windows e `..`. Não remova essa validação para “facilitar” uma referência local.

### “Quero usar a letra de outra pessoa ou gerar assinatura”

Isso está fora do escopo e das regras do projeto. O carregador recusa estilos marcados como assinatura, e estilos só podem ser treinados a partir de amostras declaradas como pertencentes ao próprio usuário.

## 8. Critérios de aceite

Uma implementação de estilo e geração só deve ser considerada pronta quando atender aos critérios abaixo.

### Contratos e segurança

- [ ] `StylePack` carrega e escreve o JSON contratual sem perder versão, hash, cobertura, preset, referências ou consentimento.
- [ ] `owner_consent` precisa ser exatamente `true`.
- [ ] Referências são relativas e não escapam da pasta permitida.
- [ ] Marcadores de assinatura são rejeitados.
- [ ] Amostras reais, datasets, pesos e saídas permanecem fora do Git e dos logs de CI.
- [ ] O caminho padrão não faz chamadas de rede.

### Conteúdo e glyphs

- [ ] O texto de entrada é preservado literalmente.
- [ ] A extração não cria associações quando a segmentação é ambígua.
- [ ] O GlyphBank não repete a mesma variante consecutivamente quando há alternativas.
- [ ] Falta de cobertura é sinalizada ou recusada; não há fallback silencioso para fonte de sistema.
- [ ] Acentos, cedilha e símbolos críticos têm cobertura testada.

### Backend e candidatos

- [ ] O backend declara suas capacidades.
- [ ] `seed` e `count` obedecem às validações reais; `count` é positivo.
- [ ] Cada candidato preserva texto, seed, índice e backend.
- [ ] Um backend indisponível falha explicitamente e não afirma ter renderizado.
- [ ] A proveniência permite explicar qual StylePack e backend foram usados.

### Avaliação

- [ ] Conteúdo é medido com comparação literal e métricas reproduzíveis.
- [ ] Tokens críticos de Python recebem verificação própria.
- [ ] Estilo e qualidade só são reportados como avaliados quando há pixels e procedimento correspondente.
- [ ] Candidato com conteúdo errado nunca vence por parecer visualmente natural.

### Layout e exportação

- [ ] A página usa geometria A4 e margens configuradas.
- [ ] O wrapping é baseado em medida, não em contagem fixa de caracteres.
- [ ] Nenhuma palavra cruza a margem; linhas longas são divididas conforme o contrato.
- [ ] Quebras de página, recuos e altura de linha são determinísticos.
- [ ] PNG/PDF preserva `generator=manual-handwrite-ia`.

### Desempenho e qualidade percebida

- [ ] O aceite da Fase 3 é uma página A4 com 1.000 caracteres em menos de 5 s na CPU.
- [ ] A saída é legível e não depende de uma fonte de sistema disfarçada.
- [ ] Há comparação com páginas reais do titular e amostras de avaliação fora do treino.
- [ ] A aplicação opcional de scan mantém o conteúdo e a proveniência rastreáveis.

## 9. Regra de ouro

Sempre deve ser possível responder, para qualquer página produzida: **qual texto entrou, quais amostras consentidas forneceram o estilo, qual backend gerou os candidatos, qual avaliação escolheu o resultado, como o layout o posicionou e quais efeitos de scan foram aplicados**. Se essa cadeia não puder ser explicada, a imagem não é uma geração confiável do pipeline.
