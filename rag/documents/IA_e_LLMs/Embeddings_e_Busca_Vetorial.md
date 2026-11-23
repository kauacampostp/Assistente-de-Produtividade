# Embeddings Densos e Busca Vetorial

## Representação Semântica em Espaços Latentes

**Embeddings** são vetores numéricos densos de dimensão fixa (como 384, 768 ou 1536 dimensões) que representam o significado semântico de palavras, frases ou documentos inteiros. Diferente de representações esparsas baseadas em contagem exata de palavras (como TF-IDF ou BM25), embeddings mapeiam textos com significados semelhantes para regiões próximas no espaço vetorial, mesmo quando não compartilham vocabulário idêntico.

## Métricas de Similaridade

Para recuperar os documentos mais relevantes diante de uma consulta convertida em vetor, bancos vetoriais utilizam métricas geométricas:

- **Similaridade de Cosseno:** Mede o cosseno do ângulo entre dois vetores, focando na orientação semântica independentemente da magnitude (comprimento) dos vetores. Varia entre $-1$ e $1$.
- **Produto Interno (Dot Product):** Combina direção e magnitude; equivale à similaridade de cosseno quando os vetores estão normalizados ($L_2 = 1$).
- **Distância Euclidiana ($L_2$):** Mede a distância em linha reta entre dois pontos no espaço vetorial; quanto menor o valor, maior a proximidade.

## Estratégias de Chunking (Fragmentação)

Modelos de embedding possuem limite máximo de tokens e perdem precisão semântica quando comprimem documentos muito longos em um único vetor. Por isso, bases de conhecimento dividem os textos em **chunks**:

- **Chunking Recursivo por Caracteres:** Quebra o texto respeitando hierarquias naturais (parágrafos, quebras de linha, sentenças) até atingir um tamanho alvo (ex.: 800 a 1000 caracteres).
- **Sobreposição (Overlap):** Mantém uma janela de repetição (ex.: 150 a 200 caracteres) entre chunks consecutivos para evitar que ideias importantes sejam cortadas ao meio na fronteira entre blocos.
