# RAG (Retrieval-Augmented Generation) e Mitigação de Alucinações

## Por que Utilizar RAG

LLMs armazenam conhecimento paramétrico adquirido durante o pré-treinamento, o que traz três limitações críticas: desatualização temporal, desconhecimento de documentos privados e tendência a gerar afirmações plausíveis porém falsas (**alucinações**) quando faltam evidências. O **RAG** resolve esse problema conectando o gerador a uma base de conhecimento externa recuperável em tempo de execução.

## Pipeline Clássico vs. RAG Agêntico

- **RAG Linear (Ingênuo):** Converte a pergunta do usuário em embedding, recupera os _top-k_ chunks mais próximos no banco vetorial (como ChromaDB ou FAISS) e injeta tudo no prompt do LLM. Falha quando a pergunta é ambígua ou usa termos diferentes dos documentos.
- **RAG Agêntico:** Introduz ciclos de decisão e autoavaliação no fluxo:
  1. O agente decide se a pergunta realmente exige consulta à base documental.
  2. Após a busca inicial, um nó avaliador verifica se os trechos recuperados respondem à pergunta.
  3. Caso o contexto seja insuficiente, o agente **reformula a consulta** (expandindo sinônimos ou decompondo perguntas complexas) e executa uma nova busca antes de sintetizar a resposta.

## Boas Práticas de Grounding e Citação

Para garantir confiabilidade em sistemas corporativos e acadêmicos, o prompt de geração deve instruir o modelo a responder estritamente com base nos trechos recuperados, declarar explicitamente quando não houver evidência suficiente e preservar os **metadados de origem** (nome do arquivo ou seção) em cada resposta.
