## STATE

- Estrutura padrão do LangChain para representar texto extraido EXP
  from langchain_core.documents import Document

- Classe principal (molde) que vai guarda as variáveis do agente como memória (quando acontece o fluxo, isso serve como memoria para o agente saber o que já fez ou pode fazer)
  class AgentState(TypedDict):

- RAG = Leitura dos documentos

- RAG agêntico = Processo de novas buscas do documento para melhores resposta caso necessário

- MCP = tools em servidores locais ou externos para uso "plug and play"

- Skills = arquivos de texto para fazer o agente ter uma função e seguir regras

## WORKFLOW

- Cria o construtor do grafo. Vê o AgentState (molde) e percebe o que deve guardar e o que gerenciar.
  builder = StateGraph(AgentState)

- Registra os nós. Colocando o nome do nó e qual função ele chama quando acionado
  builder.add_node("classify_intent", classify_intent)

- Define o início do fluxo.
  builder.add_edge(START, "classify_intent")

- Define o roteamento condicional. Define o nó que deve esperar terminar, recebe o retorna da função "route_intent" e compara com o dicionário.
  builder.add_conditional_edges(
  "classify_intent",
  route_intent,
  {
  "knowledge": "knowledge",
  "productivity": "productivity",
  "review": "review",
  "planning": "planning",
  },

  )

- Todos os caminhos terminam após executar seu respectivo nó.
  builder.add_edge("knowledge", END)

- Compila o grafo com memória persistente. Checkpointer é a memória entre as execuções. A cada ação ele tira uma foto do agentState e salva em um banco com um id
  def build_graph(checkpointer):
  return builder.compile(checkpointer=checkpointer)
