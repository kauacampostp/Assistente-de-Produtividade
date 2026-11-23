# Skills e Memória em Agentes de IA

## Skills: Procedimentos Carregados sob Demanda

Uma **skill** é uma pasta com um arquivo `SKILL.md` que ensina ao agente como executar uma tarefa de várias etapas. O arquivo começa com um cabeçalho (frontmatter) contendo `name` e `description`, seguido das instruções em texto: objetivo, quando usar, procedimento passo a passo, regras e formato da resposta.

### Divulgação Progressiva

Colocar todas as instruções de todas as skills no prompt desperdiçaria tokens e confundiria o modelo. Por isso se usa a **divulgação progressiva**:

1. O prompt recebe apenas o **catálogo**, isto é, o nome e a descrição curta de cada skill.
2. O modelo (ou uma etapa de roteamento) escolhe a skill adequada para a mensagem do usuário, ou nenhuma.
3. Somente então o conteúdo completo do `SKILL.md` escolhido é carregado e usado.

### Skill vs. Ferramenta

Uma **ferramenta** executa uma ação concreta, como listar tarefas ou ler um arquivo. Uma **skill** ensina um método: em que ordem consultar as fontes, como cruzar informações, quais regras respeitar e como estruturar o resultado. Uma boa skill não repete o que a ferramenta já faz sozinha e sim orienta como usar várias ferramentas e fontes para chegar a uma análise.

### Boas Práticas ao Escrever Skills

- Escrever a descrição dizendo claramente **quando** a skill deve ser usada, pois ela é o critério de escolha.
- Incluir regras de honestidade, como não inventar dados, diferenciar fatos de inferências e informar o que não pôde ser verificado.
- Definir um formato de resposta previsível.

## Memória em Agentes

- **Memória de curto prazo:** o histórico da conversa atual. Em frameworks de grafos é mantida por um checkpointer, que salva o estado por `thread_id`, permitindo retomar a conversa depois.
- **Memória de longo prazo:** informações guardadas para uso entre conversas diferentes, em arquivos, bancos relacionais ou bancos vetoriais.

### O Limite da Janela de Contexto

O histórico enviado ao modelo consome tokens e a janela de contexto é finita. Provedores também impõem limites de taxa, como tokens por minuto e por dia nos planos gratuitos. Estratégias comuns para controlar o custo:

- **Janela deslizante:** enviar apenas os últimos turnos da conversa.
- **Truncamento:** cortar respostas antigas muito longas.
- **Resumo:** substituir turnos antigos por um resumo curto.

Cada etapa do grafo que chama o LLM reenvia o histórico, então um fluxo com várias chamadas por turno multiplica o gasto, e vale reduzir tanto a quantidade de turnos quanto o tamanho de cada um.
