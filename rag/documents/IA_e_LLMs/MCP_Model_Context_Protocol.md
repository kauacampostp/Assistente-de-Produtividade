# MCP: Model Context Protocol

## O que é o MCP

O **Model Context Protocol (MCP)** é um protocolo aberto, apresentado pela Anthropic em novembro de 2024, que padroniza a forma como aplicações de IA se conectam a ferramentas e fontes de dados. Em vez de escrever uma integração diferente para cada serviço, a aplicação fala um único protocolo com qualquer servidor compatível, no estilo "plug and play".

## Arquitetura

- **Host:** a aplicação de IA que o usuário utiliza (um assistente, uma IDE ou um agente próprio).
- **Cliente MCP:** componente dentro do host que mantém uma conexão com um servidor específico.
- **Servidor MCP:** programa que expõe capacidades ao cliente. Pode ser local, rodando como processo filho, ou remoto, acessado pela rede.

As mensagens trafegam em formato JSON-RPC 2.0.

## O que um Servidor Expõe

1. **Tools (ferramentas):** ações que o modelo pode pedir para executar, como criar uma tarefa ou ler um arquivo. Cada ferramenta tem nome, descrição e um **JSON Schema** dos parâmetros de entrada.
2. **Resources (recursos):** dados e contextos que o cliente pode ler, como arquivos ou registros.
3. **Prompts:** modelos de instrução reutilizáveis oferecidos pelo servidor.

## Descoberta e Chamada de Ferramentas

O cliente primeiro lista as ferramentas disponíveis (`list_tools`) e recebe nome, descrição e schema de cada uma. Em seguida, executa uma delas com `call_tool`, informando o nome e os argumentos. O resultado volta com o conteúdo produzido e uma indicação de erro quando a execução falha, o que permite ao cliente tratar o problema sem derrubar o fluxo.

## Transportes

- **stdio:** o cliente inicia o servidor como um subprocesso local e conversa por entrada e saída padrão. É simples e indicado para ferramentas que rodam na máquina do usuário.
- **Streamable HTTP:** usado por servidores remotos, que normalmente exigem autenticação, como OAuth. Substituiu o antigo transporte baseado em HTTP com SSE.

Servidores remotos que só aceitam HTTP podem ser acessados por um cliente local através de uma ponte (por exemplo, o pacote `mcp-remote`), que abre o navegador para o usuário fazer login na primeira conexão.

## Segurança em Servidores MCP

- **Menor privilégio:** o servidor deve acessar apenas o que a tarefa exige, como uma única pasta autorizada.
- **Proteção contra path traversal:** ao receber um caminho, resolver o caminho absoluto e verificar que ele continua dentro da pasta autorizada, bloqueando entradas como `../../.env`.
- **Limites e listas de permissão:** restringir extensões de arquivo permitidas, limitar o tamanho de leitura e escrita e nunca sobrescrever arquivos existentes sem autorização.
- **Entradas não confiáveis:** descrições e resultados de ferramentas podem conter instruções maliciosas (prompt injection indireta) e devem ser tratados como dados, não como ordens.
- **Confirmação humana:** operações que alteram ou apagam dados devem ser apresentadas ao usuário antes da execução.

## Servidor Próprio vs. Servidor da Comunidade

Um servidor próprio permite criar ferramentas sob medida para o domínio, com as regras de segurança que o projeto precisa. Servidores da comunidade ou de fornecedores, como o do Todoist, entregam integrações prontas com serviços externos, economizando desenvolvimento, mas dependem do contrato de ferramentas que o fornecedor define.
