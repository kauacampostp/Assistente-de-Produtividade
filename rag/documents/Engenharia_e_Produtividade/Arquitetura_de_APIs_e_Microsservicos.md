# Arquitetura de APIs e Microsserviços

## Monolito Modular vs. Microsserviços

A escolha arquitetural de um sistema deve equilibrar velocidade de desenvolvimento e escala operacional:

- **Monolito Modular:** Mantém todo o código em uma única unidade de implantação, mas organizado em módulos com fronteiras bem definidas. Reduz latência de rede, simplifica transações em banco de dados e é ideal para equipes pequenas e produtos em validação.
- **Microsserviços:** Decompõe o sistema em serviços independentes orientados a domínios de negócio, cada um com seu próprio ciclo de deploy e armazenamento. Exige maturidade em observabilidade, automação e tolerância a falhas.

## Padrões de Comunicação entre Serviços

1. **Comunicação Síncrona (REST / gRPC):** O cliente aguarda a resposta imediata. Simples de implementar, mas cria acoplamento temporal: se o serviço de destino ficar indisponível, a cadeia inteira pode falhar sem mecanismos como _Circuit Breaker_ e _Timeouts_.
2. **Comunicação Assíncrona (Mensageria / Eventos):** Serviços publicam eventos em brokers (como RabbitMQ ou Kafka) e consumidores processam as mensagens no seu próprio ritmo. Aumenta a resiliência e absorve picos de carga.

## Idempotência e Consistência Eventual

Em sistemas distribuídos, falhas de rede exigem retentativas (_retries_). Operações críticas (como criação de pedidos ou cobranças) devem ser **idempotentes**, utilizando chaves únicas de requisição para garantir que o processamento repetido não duplique efeitos colaterais. Além disso, transações distribuídas costumam adotar **consistência eventual** por meio do padrão _Saga_ em vez de bloqueios distribuídos rígidos.
