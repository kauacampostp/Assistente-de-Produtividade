
import asyncio

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from graph.workflow import build_graph


async def main():
    print("Assistente de Produtividade iniciado!")
    print("Digite 'sair' para encerrar.\n")

    # Abre o banco SQLite e mantém o checkpointer ativo
    async with AsyncSqliteSaver.from_conn_string(
        "checkpoints.sqlite"
    ) as checkpointer:

        await checkpointer.setup()
        graph = build_graph(checkpointer)

        # Identifica a conversa; use o mesmo ID para recuperá-la depois
        thread_id = input(
            "ID da conversa (Enter para conversa-1): "
        ).strip() or "conversa-1"

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        while True:
            mensagem = input("\nVocê: ").strip()

            if mensagem.lower() == "sair":
                break

            # Recupera o histórico salvo nessa conversa
            snapshot = await graph.aget_state(config)
            history = snapshot.values.get("conversation_history", [])

            resultado = await graph.ainvoke(
                {"user_message": mensagem},
                config=config,
            )

            resposta = resultado.get("llm_answer", "Sem resposta.")

            # Atualiza o histórico da conversa
            history.append({
                "user": mensagem,
                "assistant": resposta,
            })

            await graph.aupdate_state(
                config,
                {"conversation_history": history},
            )

            print(
                "Skill carregada:",
                resultado.get("skill_name") or "Nenhuma",
            )
            print("\nAssistente:", resposta)


if __name__ == "__main__":
    asyncio.run(main())
