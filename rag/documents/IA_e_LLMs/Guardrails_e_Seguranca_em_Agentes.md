# Guardrails e Segurança em Agentes de IA

## Principais Riscos

1. **Prompt injection direta:** o usuário escreve instruções para o modelo ignorar as regras originais ou revelar o prompt de sistema.
2. **Prompt injection indireta:** instruções maliciosas escondidas em documentos, páginas web ou resultados de ferramentas que o agente lê durante a tarefa. A lista de riscos de aplicações com LLMs mantida pela OWASP coloca a prompt injection entre os principais problemas.
3. **Vazamento de dados e credenciais:** respostas que expõem chaves de API, tokens, senhas ou conteúdo de arquivos sensíveis como `.env` e `token.json`.
4. **Ações destrutivas ou excessivas:** o agente executa operações irreversíveis, como apagar tarefas em massa, sem o usuário ter autorizado.
5. **Alucinação:** o modelo afirma como fato algo que não está nas fontes.

## Guardrails de Entrada

Verificam a mensagem do usuário antes de qualquer processamento pelo modelo principal:

- limite de tamanho da mensagem e rejeição de entradas vazias;
- detecção de padrões de manipulação de instruções, em português e inglês;
- detecção de pedidos de acesso a arquivos de segredo ou de exclusões em massa sem confirmação.

Padrões baseados em expressões regulares são rápidos e previsíveis, mas têm limite: paráfrases, outros idiomas e textos ofuscados podem escapar. Por isso devem ser uma camada entre várias, junto com as demais defesas abaixo.

## Guardrails de Saída

Verificam a resposta antes de entregá-la ao usuário:

- **Redação de segredos:** substituir por um marcador padrões típicos de chaves de API, tokens Bearer, pares como `api_key=...` e chaves privadas.
- **Limite de tamanho:** truncar respostas excessivamente longas.
- **Resposta vazia:** devolver uma mensagem de fallback clara em vez de um texto em branco.

## Defesa em Camadas

- **Menor privilégio:** ferramentas de leitura podem executar direto, enquanto ferramentas de escrita só rodam depois de confirmação explícita do usuário (human-in-the-loop).
- **Segredos fora do código:** chaves ficam em variáveis de ambiente, o arquivo `.env` é ignorado pelo Git e o repositório traz apenas um `.env.example` sem valores reais.
- **Instruções de grounding:** o prompt manda o modelo responder somente com base nas fontes e admitir quando não souber.
- **Validação de argumentos:** antes de chamar uma ferramenta, conferir tipos, campos obrigatórios e valores permitidos.

## Guardrails como Nós do Grafo

Implementar a validação como nós dedicados de um grafo permite que uma mensagem bloqueada pule todo o processamento e siga direto para a etapa final de saída, sem consumir chamadas ao LLM. Como todos os caminhos terminam no mesmo nó de validação de saída, nenhuma resposta, bloqueada ou não, sai sem sanitização.

## Como Testar

Montar casos de teste adversariais (red teaming), como pedidos para ignorar instruções, exibir o prompt de sistema, revelar chaves e apagar dados sem confirmação. Registrar quais foram bloqueados, quais passaram e se mensagens legítimas foram bloqueadas por engano (falsos positivos).
