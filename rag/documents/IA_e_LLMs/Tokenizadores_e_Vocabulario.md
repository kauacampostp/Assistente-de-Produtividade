# Tokenizadores e Construção de Vocabulário em LLMs

## O que é Tokenização

Modelos de Linguagem de Grande Escala (LLMs) não processam texto bruto diretamente; eles operam sobre sequências de números inteiros chamados **IDs de tokens**. O tokenizador é o componente responsável por segmentar uma string de entrada em unidades menores (tokens) e mapeá-las para um vocabulário fixo definido antes do treinamento do modelo.

## Granularidade: Caracteres, Palavras e Subpalavras

- **Tokenização por palavra:** Gera vocabulários gigantescos, sofre com palavras fora do vocabulário (_Out-Of-Vocabulary_ — OOV) e não lida bem com flexões morfológicas ou erros de digitação.
- **Tokenização por caractere:** Mantém um vocabulário minúsculo, mas produz sequências extremamente longas, elevando o custo computacional da atenção quadrática e dificultando a captura de semântica.
- **Tokenização por subpalavras (Subword):** É o padrão moderno em LLMs. Palavras frequentes permanecem inteiras, enquanto palavras raras ou compostas são divididas em prefixos, radicais e sufixos conhecidos.

## Principais Algoritmos de Subpalavras

1. **Byte-Pair Encoding (BPE):** Inicia com caracteres individuais (ou bytes UTF-8, no caso do _Byte-level BPE_ usado na família GPT) e funde iterativamente os pares adjacentes mais frequentes no corpus de treinamento até atingir o tamanho de vocabulário desejado.
2. **WordPiece:** Semelhante ao BPE, mas escolhe quais pares fundir com base na maximização da verossimilhança (_likelihood_) dos dados de treinamento, em vez de apenas frequência bruta. É utilizado em modelos como BERT.
3. **Unigram Language Model:** Parte de um vocabulário inicial grande e remove gradualmente os tokens que menos impactam a probabilidade total do corpus, permitindo múltiplas segmentações probabilísticas.

## Impactos Práticos no Uso de LLMs

- **Janela de Contexto:** O limite de contexto de um modelo é medido em tokens, não em palavras. Em português, uma palavra equivale em média a 1,3 a 1,6 tokens, o que reduz o texto útil disponível em comparação ao inglês.
- **Custo e Latência:** APIs comerciais cobram por tokens de entrada e saída, e o tempo de geração cresce proporcionalmente ao número de tokens gerados autoregressivamente.
- **Dificuldades em Tarefas de Caracteres:** Como o modelo enxerga blocos de subpalavras e não letras isoladas, tarefas como contar letras ou inverter palavras exigem raciocínio indireto.
