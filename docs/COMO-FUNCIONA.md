# Como o projeto funciona

Este documento explica o `manual-handwrite-ia` para quem pensa em termos de
programas tradicionais: arquivos entram, funções transformam esses arquivos,
testes verificam os resultados e outros arquivos saem no final.

A palavra "IA" aparece no nome porque, no futuro, o projeto poderá usar modelos
para aprender padrões da escrita. Mas o sistema não depende de uma caixa-preta
para tudo. A maior parte do fluxo é um pipeline local, explícito e testável.

## Em uma frase

O programa recebe exemplos da sua letra, separa esses exemplos em partes úteis,
guarda a relação entre cada imagem e o texto escrito, monta um pacote de estilo
e usa esse pacote para produzir novas páginas manuscritas.

A aparência de papel escaneado é uma etapa separada. Ela pode ser ligada ou
desligada sem mudar a letra que foi gerada.

## O problema que estamos resolvendo

Uma fonte de computador escreve todos os `a`, `b` e `c` praticamente iguais.
Uma pessoa não faz isso. A mesma letra muda um pouco conforme a palavra, a
pressão da caneta e o espaço disponível.

O projeto tenta preservar essas pequenas características da letra do dono:

- formato das letras;
- tamanho e inclinação;
- distância entre letras e palavras;
- linha de base;
- variações naturais da mesma letra;
- ligações simples da escrita cursiva;
- aparência da tinta e do papel, quando desejado.

O projeto **não** tenta reconhecer ou copiar a letra de outra pessoa. O dataset
precisa declarar que as amostras são do próprio titular.

## A visão geral do pipeline

```text
folhas preenchidas
        |
        v
normalização e segmentação
        |
        v
imagem + texto correspondente
        |
        v
manifesto do dataset pessoal
        |
        v
StylePack, o pacote que descreve a letra
        |
        v
backend de escrita
        |
        v
candidatos manuscritos
        |
        v
layout da página
        |
        v
efeito opcional de scanner/celular
        |
        v
PNG ou PDF com metadados
```

Há uma distinção importante no meio do caminho:

```text
conteúdo       = o que deve ser escrito
estilo         = como o dono costuma escrever
scan           = como a folha final parece depois de digitalizada
```

Misturar essas três coisas dificulta a depuração. Se o texto saiu errado, o
problema é de conteúdo. Se o texto está correto mas não parece a letra do dono,
o problema é de estilo. Se a letra está boa mas o papel parece artificial, o
problema é do simulador de scan.

## Etapa 1: coletar exemplos

O programa deverá gerar uma folha-modelo em PDF. Essa folha contém letras,
números, acentos, pontuação e palavras de exemplo.

O dono imprime a folha e escreve normalmente, sem tentar fazer uma letra
"bonita". Depois escaneia ou fotografa a folha e coloca o arquivo em `samples/`.

A qualidade da amostra importa mais que a quantidade. Uma página escrita de
forma natural ensina mais que várias páginas copiadas devagar e com cuidado
excessivo.

As amostras são dados pessoais. Elas ficam fora do Git e não são enviadas para
serviços externos pelo caminho padrão.

## Etapa 2: preparar a página

A imagem escaneada não entra diretamente no treinamento. Primeiro o programa
faz tarefas parecidas com um utilitário comum de processamento de imagem:

1. corrige a orientação EXIF;
2. converte a imagem para tons de cinza;
3. normaliza o contraste;
4. identifica as linhas escritas pela projeção horizontal;
5. recorta as regiões encontradas;
6. registra de onde cada região veio.

O resultado não é apenas uma pasta de imagens soltas. Cada região carrega
informações como posição na página, índice da linha e origem do arquivo.

Essa proveniência é necessária para responder depois: "de qual folha veio este
recorte?" e "qual texto deveria estar nesta região?".

## Etapa 3: descobrir o texto de cada imagem

Para aprender uma letra, o programa precisa de duas informações:

```text
imagem da escrita + texto que foi escrito
```

Quando o texto original já é conhecido, usamos o caminho `source-pair`. Por
exemplo, uma imagem de uma página de código acompanhada do `source.py` que foi
escrito. Nesse caso o arquivo-fonte é a referência principal. Não faz sentido
usar OCR ou modelo para redescobrir um texto que já temos.

Quando o texto não é conhecido, um adaptador de VLM poderá sugerir transcrições.
Esse modelo não terá autoridade para alterar os dados silenciosamente. As
respostas serão:

- validadas como JSON;
- comparadas entre passes independentes;
- verificadas com sinais de sintaxe e indentação quando o texto for Python;
- classificadas como `Gold`, `Silver` ou `Quarantine`.

A regra é simples: dúvida não vira dado de treinamento. Uma região duvidosa vai
para quarentena com o motivo registrado.

## Etapa 4: construir o dataset pessoal

O dataset é um manifesto JSONL. Cada linha descreve uma amostra, em vez de
esconder a relação dentro de nomes de arquivos.

Um registro conceitual se parece com isto:

```json
{
  "tier": "gold",
  "image": "samples/folha-01.png",
  "text": "for item in lista:",
  "region": {"x": 120, "y": 640, "width": 900, "height": 80},
  "source": "exercicios/aula-01.py",
  "owner_consent": true
}
```

O formato real pode ganhar campos, mas a ideia não muda: imagem, texto,
localização e origem viajam juntos.

O programa também mede a cobertura do dataset. Ele conta, por exemplo, quais
letras, acentos e símbolos de Python já apareceram. Assim, a próxima folha pode
ser escolhida para preencher uma lacuna real, em vez de pedir amostras às
cegas.

## Etapa 5: criar o StylePack

O `StylePack` é o pacote que representa uma versão segura do estilo da letra.
Ele não é uma fonte instalada no sistema e não é um arquivo mágico com toda a
personalidade do escritor.

Ele guarda referências relativas ao dataset, sua identificação, um hash, o
resumo de cobertura, o preset de scan e o consentimento do proprietário.

O carregamento recusa, entre outras coisas:

- ausência de `owner_consent = true`;
- caminhos absolutos ou tentativa de sair da pasta permitida;
- estilo marcado como assinatura;
- referências inválidas ao dataset.

## Etapa 6: gerar a escrita

A primeira versão usará uma estratégia direta, chamada `GlyphBank`.

A ideia é próxima de recortar e colar, mas com regras melhores que uma simples
montagem de imagens:

1. buscar variantes reais de cada letra no dataset;
2. evitar repetir a mesma variante consecutivamente;
3. variar levemente escala, inclinação e linha de base;
4. respeitar o espaçamento entre letras e palavras;
5. tratar ligações simples entre caracteres cursivos;
6. rejeitar ou sinalizar símbolos que não tenham cobertura suficiente.

O texto pedido pelo usuário continua sendo a autoridade. O gerador não pode
transformar `=` em `==`, trocar uma letra ou apagar um acento apenas porque a
imagem resultante ficou mais bonita.

Para cada linha, o sistema poderá gerar vários candidatos. Depois cada
candidato será avaliado separadamente em quatro aspectos:

- conteúdo: o texto está exatamente correto?
- estilo: parece a letra do dono?
- qualidade: está legível e sem artefatos graves?
- layout: cabe na página e respeita as margens?

Um candidato com texto errado não deve vencer apenas porque parece natural.
Para código Python, símbolos críticos têm peso maior que uma pequena diferença
visual.

## Etapa 7: montar a página

Depois que as linhas foram geradas, outro módulo cuida da página:

- tamanho A4;
- margens;
- posição das linhas;
- recuo de parágrafos e blocos de código;
- quebra de linha;
- quebra de página;
- pauta opcional;
- prevenção de texto cortado ou fora da margem.

Essa separação permite testar o layout mesmo antes de existir um modelo neural.
Também permite trocar o backend de escrita sem reescrever a paginação.

## Etapa 8: simular um documento escaneado

A imagem manuscrita limpa não precisa parecer uma imagem perfeita de computador.
O simulador aplica efeitos configuráveis, como:

- variação de densidade da tinta;
- leve espalhamento da tinta;
- textura e cor do papel;
- rotação e perspectiva;
- iluminação desigual;
- ruído do sensor;
- pretos e brancos menos puros;
- compressão JPEG.

Existem presets planejados para scanner de escritório, celular, xerox antigo e
modo limpo.

Essa etapa recebe uma imagem pronta e devolve outra imagem. Ela não aprende a
letra e não decide o texto. Isso torna possível testar o efeito de scan sozinho.

## Etapa 9: exportar

O resultado final será exportado como PNG ou PDF em resolução adequada para
impressão.

Todo arquivo exportado leva o metadado:

```text
generator=manual-handwrite-ia
```

Esse metadado não é decorativo. Ele identifica que o arquivo foi produzido pelo
programa e não deve ser removido.

## Onde entra a IA

A IA é uma ferramenta opcional em partes específicas do sistema. Ela não deve
ser tratada como dona do pipeline.

### Pode ser usada para

- sugerir a estrutura de uma página;
- propor transcrições quando o texto não é conhecido;
- ajudar a reconciliar linhas ambíguas;
- no futuro, gerar escrita condicionada ao StylePack.

### Não deve fazer sozinha

- inventar texto ausente;
- corrigir silenciosamente o que aparece na imagem;
- aceitar uma resposta malformada;
- decidir que uma assinatura pode ser coletada;
- enviar amostras para a internet sem comando explícito;
- substituir testes por uma afirmação de confiança.

No caminho padrão, o núcleo não faz chamadas de rede. Um backend neural só será
considerado depois que a versão determinística estiver medida e funcionando.

## O que existe hoje

O estado atual é de fundação da Fase 1. Já existem e foram testados:

- normalização e segmentação de páginas;
- contratos de página, região e proveniência;
- manifesto JSONL e níveis de confiança;
- ingestão `source-pair` para dados GOLD;
- análise de cobertura de texto e Python;
- protocolo de respostas VLM;
- contratos de StylePack e segurança;
- contratos de backend de geração;
- layout e exportação;
- simulador de scan;
- testes automatizados e smoke tests da CLI.

A verificação atual passa com:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

O resultado verificado no estado atual é de 88 testes passando.

Ainda não existe uma geração personalizada completa. O backend de geração atual
recusa explicitamente a operação quando não há um renderizador real, em vez de
fingir que uma fonte de sistema é manuscrito.

## O que falta para usar de verdade

A ordem prática é:

1. implementar o comando `handwrite template`;
2. implementar a ingestão completa da folha preenchida;
3. gerar e preencher as primeiras folhas reais;
4. validar o dataset com amostras do próprio titular;
5. implementar o `GlyphBank` e o comando `handwrite write`;
6. comparar páginas geradas com páginas reais fora do dataset de treino;
7. só depois avaliar um modelo neural.

Os comandos abaixo já aparecem como contrato do produto, mas alguns ainda são
etapas futuras:

```bash
uv run handwrite template --out folha-modelo.pdf
uv run handwrite ingest samples/folha-01.jpg
uv run handwrite train --style minha-letra
uv run handwrite write "Uma anotação" \
  --style minha-letra \
  --scan-preset scanner-escritorio \
  --out anotacao.pdf
```

Hoje os caminhos funcionais da CLI são `scanify`, `coverage` e `source-pair`.

## Como depurar um problema

A pergunta certa depende de onde o resultado ficou errado:

### O texto está errado

Verifique a fonte original, o manifesto e a transcrição. Não comece ajustando
o modelo visual.

### A letra não parece a do dono

Verifique se o StylePack aponta para amostras reais, se as amostras ficaram
fora do treinamento de avaliação e se há cobertura suficiente para os símbolos
usados.

### A página ficou cortada

Verifique o módulo de layout, as margens e a medição das linhas. O backend de
estilo não deveria resolver um problema de paginação.

### O manuscrito parece uma imagem digital perfeita

Verifique o preset e o simulador de scan. Não confunda esse problema com falha
do modelo de escrita.

### O teste passou, mas a letra ficou ruim

Isso é possível e esperado. Testes automatizados verificam contratos, formatos,
limites e determinismo. A qualidade visual exige comparação com páginas reais,
amostras mantidas fora do treino e avaliação do titular.

## Glossário curto

**Dataset**
Conjunto de amostras usadas pelo programa. Aqui, cada amostra tem imagem,
texto e proveniência.

**GOLD**
Dado cujo texto e relação com a imagem são conhecidos com segurança, como um
par imagem + `source.py` validado.

**SILVER**
Dado plausível, mas com menos garantia que GOLD.

**Quarantine**
Dado que não será usado no treinamento até ser resolvido.

**Glyph**
Um recorte de uma letra ou símbolo.

**GlyphBank**
Banco de variantes de glifos usados pela primeira versão do gerador.

**StylePack**
Pacote versionado que aponta para um dataset consentido e descreve o estilo
aprendido.

**Backend**
Implementação concreta capaz de gerar uma saída. O projeto pode ter mais de
um backend, mas um backend indisponível deve avisar claramente.

**VLM**
Modelo que combina imagem e linguagem. Neste projeto ele serve primeiro como
ajudante de transcrição e estrutura, não como fonte incontestável.

**Scan simulator**
Módulo que transforma uma imagem limpa em uma imagem com aparência de folha
escaneada ou fotografada.

## Regra principal do projeto

A saída precisa ser rastreável: deve ser possível explicar qual texto entrou,
quais amostras de estilo foram usadas, qual backend gerou a imagem, quais
transformações de scan foram aplicadas e quais metadados foram exportados.

Se não for possível explicar o caminho, o programa não aprendeu a letra; ele
apenas produziu uma imagem que parece plausível.
