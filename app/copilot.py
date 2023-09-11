import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureTextCompletion
from semantic_kernel.planning.sequential_planner import SequentialPlanner
from plugins.SearchPlugin import SearchPlugin


async def main():

    # Instantiate your kernel
    kernel = sk.Kernel()

    # Prepare Azure OpenAI service using credentials stored in the `.env` file
    deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
    kernel.add_chat_service("chat", AzureTextCompletion(deployment, endpoint, api_key))

    # Register plugins
    search_plugin = kernel.import_skill(SearchPlugin(), skill_name="search_plugin")
    answer_plugin = kernel.import_semantic_skill_from_directory("plugins", "AnswerPlugin")
    orchestrator_plugin = kernel.import_semantic_skill_from_directory("plugins", "OrchestratorPlugin")

    # Chat loop
    while True:

        # Starting message
        ask = input("What can I help you with?\n")

        # Detect user intent
        intent_vars = sk.ContextVariables()
        intent_vars["input"] = ask
        intent_vars["options"] = "AccountQuery, Other"
        intent = await orchestrator_plugin["getIntent"].invoke_async(variables=intent_vars)
        intent_result = intent.result.strip()

        if intent_result == "AccountQuery":

            # Extract organization name to use as search query
            query = await orchestrator_plugin["getQuery"].invoke_async(ask)
            query_clean = query.result.replace("<|im_end|>", "").strip()
            #print(f"Query: {query_clean}")

            # Search for the account
            search_result = await search_plugin["getAccount"].invoke_async(query_clean)
            #print(f"Search result: {search_result}")

            # Set up context variables
            answer_vars = sk.ContextVariables()
            answer_vars["input"] = ask
            answer_vars["context"] = search_result.result

            # Generate answer
            answer = await answer_plugin["getAnswer"].invoke_async(variables=answer_vars)
            answer = answer.result.strip()
            print(answer)

        else:
            
            # Generate answer
            answer = await answer_plugin["getAnswer"].invoke_async(ask)
            answer = answer.result.strip()
            print(answer)



# Run the main function
if __name__ == "__main__":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) # Necessary to avoid errors on Windows
    asyncio.run(main())