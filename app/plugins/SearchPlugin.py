from semantic_kernel.skill_definition import sk_function
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import os

class SearchPlugin:

    # Load environment
    load_dotenv()

    # Create Cognitive Search client with configuration from .env file
    search_client = SearchClient(
        endpoint=os.getenv("AZURE_COGNITIVE_SEARCH_ENDPOINT"),
        index_name=os.getenv("AZURE_COGNITIVE_SEARCH_INDEX_NAME"),
        credential=AzureKeyCredential(os.getenv("AZURE_COGNITIVE_SEARCH_API_KEY")),
    )
    
    @sk_function(
        description="Retrieves account information from the search index",
        name="getAccount",
        input_description="The account name",
    )
    def get_account(self, query: str) -> str:
        # Get search client
        search_client = self.search_client

        # Search the index
        results = search_client.search(search_text=query, top=1)

        top_result = next(results, None)
        if top_result:
            return str(top_result)
        else:
            raise Exception(f"Search for {query} did not return any results.")
