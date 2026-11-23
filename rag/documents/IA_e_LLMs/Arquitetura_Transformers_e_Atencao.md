# Arquitetura Transformer e Mecanismos de Atenção

## Visão Geral da Arquitetura

Introduzida no artigo _Attention Is All You Need_ (2017), a arquitetura **Transformer** eliminou a recorrência sequencial das RNNs e LSTMs, permitindo processar todos os tokens de uma sequência em paralelo durante o treinamento. Seu núcleo baseia-se no mecanismo de **autoatenção** (_Self-Attention_), que pondera a relevância de cada token em relação a todos os outros da mesma entrada.

## Como Funciona o Self-Attention (Q, K, V)

Para cada token de entrada, o modelo projeta seu vetor de embedding em três representações lineares aprendidas:

- **Query ($Q$):** Representa o que o token atual está buscando de contexto.
- **Key ($K$):** Representa o identificador ou atributo que cada token oferece para ser encontrado.
- **Value ($V$):** Contém a informação semântica real que será agregada caso haja correspondência entre $Q$ e $K$.

A atenção escalonada por produto interno calcula a similaridade entre cada par de queries e keys, divide pela raiz quadrada da dimensão $d_k$ para estabilizar os gradientes e aplica uma função _softmax_ para gerar pesos de probabilidade que ponderam os vetores $V$.

## Multi-Head Attention e Positional Encoding

- **Multi-Head Attention:** Em vez de executar uma única função de atenção, o Transformer divide as projeções em múltiplas "cabeças" paralelas. Cada cabeça aprende a capturar relações distintas, como dependências sintáticas, correferência pronominal ou proximidade semântica.
- **Positional Encoding:** Como a autoatenção é invariante à ordem dos tokens, o modelo injeta informações de posição nos embeddings de entrada (via funções senoidais, embeddings posicionais aprendidos ou métodos relativos como **RoPE** — _Rotary Position Embedding_).

## Variantes Estruturais

1. **Encoder-Only (ex.: BERT):** Usa atenção bidirecional. Ideal para classificação, extração de entidades e geração de embeddings.
2. **Decoder-Only (ex.: GPT, Llama, Qwen):** Usa máscara causal (_masked self-attention_) para impedir que um token acesse posições futuras. É o padrão para geração de texto autoregressiva.
3. **Encoder-Decoder (ex.: T5, BART):** Separa a compreensão da entrada (encoder) da geração condicionada (decoder), sendo eficaz em tradução e sumarização.
