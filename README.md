# Projeto — Assistente Pessoal de Conhecimento e Produtividade

## 1. Visão geral

Desenvolver um assistente inteligente capaz de centralizar informações, tarefas, compromissos e conhecimentos pessoais, ajudando o usuário a organizar sua rotina, administrar sua agenda e tomar decisões sobre a utilização do seu tempo.

O sistema será construído em Python, utilizando LangGraph para orquestrar o agente, RAG para recuperação de conhecimento, MCP para integração com ferramentas externas, Skills para execução de processos especializados e Streamlit como interface.

## 2. Público-alvo

Pessoas que precisam administrar diferentes responsabilidades pessoais, acadêmicas e profissionais e desejam centralizar suas informações em um único assistente.

## 3. Problema identificado

Informações, tarefas e compromissos frequentemente ficam distribuídos entre diferentes ferramentas e documentos.

Isso dificulta:

- Encontrar informações armazenadas anteriormente.
- Ter uma visão completa da rotina.
- Identificar conflitos de horários e excesso de atividades.
- Distribuir tarefas de acordo com prioridades e prazos.
- Planejar a semana considerando compromissos existentes.

## 4. Solução proposta

Um assistente pessoal que conecta diferentes fontes de informação e utiliza um agente de IA para interpretar solicitações, consultar dados, executar tarefas autorizadas e produzir recomendações contextualizadas.

### Principais funcionalidades

**Conhecimento**

- Consultar documentos e anotações locais.
- Recuperar informações utilizando RAG.
- Responder perguntas sobre conteúdos armazenados.
- Criar e organizar anotações.

**Tarefas**

- Consultar tarefas pendentes.
- Identificar tarefas atrasadas.
- Consultar prioridades e prazos.
- Criar e atualizar tarefas no Todoist.

**Agenda**

- Consultar compromissos no Google Calendar.
- Identificar horários disponíveis.
- Identificar conflitos.
- Consultar a programação de determinado período.

**Planejamento**

- Criar propostas de planejamento diário e semanal.
- Distribuir tarefas considerando prazos e prioridades.
- Considerar compromissos existentes.
- Identificar sobrecarga.
- Solicitar aprovação antes de modificar a agenda.

**Revisão de rotina**

- Analisar a distribuição das atividades.
- Identificar tarefas acumuladas.
- Identificar conflitos e problemas de organização.
- Recomendar melhorias.

## 5. Fontes de dados

| Fonte           | Utilização                        |
| --------------- | --------------------------------- |
| Todoist         | Gerenciamento de tarefas          |
| Google Calendar | Gerenciamento de compromissos     |
| Arquivos locais | Documentos, notas e conhecimentos |

Formatos iniciais de documentos: PDF, TXT e Markdown.

## 6. Arquitetura e tecnologias

- **Python:** linguagem principal.
- **LangGraph:** construção e execução do grafo do agente.
- **LLM:** interpretação de solicitações e tomada de decisões.
- **RAG:** recuperação de informações dos documentos.
- **MCP próprio:** acesso e organização de notas locais.
- **MCP da comunidade:** integração com Todoist e Google Calendar.
- **Skills:** procedimentos especializados para planejamento e revisão.
- **Checkpointer:** memória conversacional entre turnos.
- **Guardrails:** proteção de entradas, operações e respostas.
- **Streamlit:** interface de usuário.

## 7. Skills

### Skill 1 — Revisor de rotina

Arquivo: `skills/revisor_rotina/SKILL.md`

Deverá ensinar o agente a:

1. Consultar tarefas e compromissos.
2. Identificar atrasos e conflitos.
3. Avaliar a distribuição das atividades.
4. Identificar possíveis sobrecargas.
5. Elaborar um diagnóstico.
6. Apresentar recomendações.

### Skill 2 — Planejador de rotina

Arquivo: `skills/planejador_rotina/SKILL.md`

Deverá ensinar o agente a:

1. Identificar objetivos e prioridades.
2. Consultar tarefas e compromissos.
3. Avaliar disponibilidade.
4. Distribuir atividades ao longo da semana.
5. Considerar prazos e duração das tarefas.
6. Elaborar uma proposta de planejamento.
7. Solicitar aprovação antes de executar alterações.

## 8. Guardrails

Serão implementadas proteções em dois momentos.

**Entrada:**

- Identificação de solicitações fora do domínio do assistente.
- Proteção contra prompt injection em mensagens e documentos.
- Bloqueio de solicitações que tentem obter informações de outros usuários.

**Saída e execução:**

- Verificação de informações sensíveis.
- Proteção contra exposição de credenciais e dados privados.
- Confirmação antes de operações que alterem ou excluam informações.

## 9. Memória

O agente utilizará Checkpointer do LangGraph para manter o histórico de cada conversa, permitindo recuperar informações de turnos anteriores.

O histórico conversacional será separado do conhecimento persistente armazenado nos documentos.

## 10. Escopo do MVP

A primeira versão deverá permitir:

1. Conversar com o assistente por meio de uma interface Streamlit.
2. Consultar informações armazenadas em documentos.
3. Consultar tarefas do Todoist.
4. Consultar compromissos do Google Calendar.
5. Solicitar revisão da rotina.
6. Solicitar planejamento semanal.
7. Criar tarefas mediante autorização.
8. Manter memória entre mensagens.
9. Identificar e bloquear solicitações inseguras.
10. Exibir ferramentas utilizadas e Skills carregadas em cada resposta.

## 11. Fora do escopo inicial

- Aplicativo mobile nativo.
- Sincronização com múltiplos provedores de agenda.
- Notificações automáticas.
- Automação autônoma sem aprovação.
- Análises avançadas de produtividade histórica.

Esses recursos poderão ser considerados em versões futuras.

## 12. Critérios de sucesso

O projeto será considerado funcional quando:

- O grafo LangGraph executar os diferentes fluxos de atendimento.
- O RAG recuperar informações relevantes e conseguir reformular pesquisas insuficientes.
- Existir pelo menos um servidor MCP desenvolvido pela dupla e um servidor da comunidade.
- As duas Skills forem carregadas sob demanda.
- O agente conseguir consultar e utilizar dados do Todoist e Google Calendar.
- A memória funcionar entre turnos da mesma conversa.
- Os guardrails protegerem contra pelo menos dois riscos concretos.
- A interface Streamlit permitir conversar e iniciar novas conversas.
- As ferramentas utilizadas e Skills carregadas forem exibidas.
- Os dez casos de teste exigidos forem documentados e avaliados.

## 13. Entrega

- Repositório público no GitHub.
- Código completo e organizado.
- README com arquitetura, participantes, decisões técnicas e instruções de execução.
- Dez casos de teste documentados.
- Vídeo demonstrativo de até cinco minutos.
# Assistente-de-Produtividade
