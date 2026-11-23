# Agentes de IA e Orquestração com Grafos (LangGraph)

## Do Chatbot ao Agente

Um chatbot comum responde a cada mensagem de forma isolada. Um **agente** combina um modelo de linguagem com ferramentas, memória e um fluxo de decisão, repetindo um ciclo de perceber, decidir, agir e observar o resultado. Existem duas abordagens principais para construí-lo:

- **Agente genérico (loop ReAct):** o modelo recebe a lista de ferramentas e escolhe livremente qual chamar a cada passo. É rápido de montar, porém o desenvolvedor controla pouco a ordem das etapas e é mais difícil prever o comportamento.
- **Fluxo explícito em grafo:** o desenvolvedor define as etapas, as ligações entre elas e os pontos de decisão. O modelo decide apenas onde o grafo permite (por exemplo, classificar uma intenção ou avaliar se um contexto é suficiente), o que torna o sistema mais previsível e fácil de testar.

## Conceitos Fundamentais do LangGraph

1. **Estado (State):** estrutura compartilhada (geralmente um `TypedDict`) que trafega entre os nós. Cada nó recebe o estado atual e devolve apenas as atualizações dos campos que modificou.
2. **Nós (Nodes):** funções que executam uma etapa do fluxo, como chamar o LLM, consultar uma ferramenta ou validar uma mensagem.
3. **Arestas (Edges):** ligações que definem qual nó roda depois de qual. As **arestas condicionais** usam uma função de roteamento que lê o estado e devolve o nome do próximo nó.
4. **START e END:** pontos especiais que marcam o início e o fim de um turno de execução.
5. **Reducers:** por padrão, o valor devolvido por um nó substitui o valor anterior do campo. Reducers permitem combinar valores, como acumular mensagens em uma lista.
6. **Compilação:** o método `compile()` transforma a definição em um grafo executável e aceita um checkpointer opcional.

## Checkpointer e Threads

O **checkpointer** salva uma fotografia do estado a cada passo do grafo, associada a um identificador de conversa chamado `thread_id`. Isso permite manter memória de curto prazo entre turnos, retomar conversas antigas e pausar o fluxo para aguardar uma decisão humana. Há implementações em memória, em SQLite e em PostgreSQL.

Um cuidado importante: como o estado é persistido, um campo que nenhum nó sobrescreve **mantém o valor do turno anterior**. Campos de observabilidade, como a lista de ferramentas usadas ou a skill carregada, devem ser reiniciados no início de cada turno para não aparecerem "grudados" em respostas seguintes.

## Subgrafos

Um grafo compilado pode ser invocado dentro de um nó de outro grafo. Isso isola um fluxo complexo em um módulo reutilizável. Um exemplo comum é o RAG agêntico (decidir se busca, recuperar, avaliar, reformular), que roda como subgrafo chamado pelo fluxo principal de conhecimento.

## Boas Práticas

- Usar regras determinísticas no roteamento sempre que possível e reservar o LLM para os casos ambíguos, reduzindo custo e variação.
- Limitar o número de repetições em ciclos, como o máximo de reformulações de consulta, para evitar laços infinitos.
- Colocar validações de entrada e de saída em nós dedicados, de modo que toda resposta, inclusive as bloqueadas, passe pela mesma verificação final.
- Exigir confirmação explícita do usuário antes de qualquer operação que altere dados externos.
