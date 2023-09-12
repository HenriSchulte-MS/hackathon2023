from semantic_kernel.skill_definition import sk_function
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from keyvault import KeyVault

class SearchPlugin:

    # Get secrets from keyvault
    keyvault = KeyVault()
    SEARCH_ENDPOINT_NAME = 'CogSearchEndpoint'
    SEARCH_KEY_NAME = 'CogSearchKey'
    search_endpoint = keyvault.get_secret(SEARCH_ENDPOINT_NAME)
    search_key = keyvault.get_secret(SEARCH_KEY_NAME)

    # Create Cognitive Search client with configuration from .env file
    search_client = SearchClient(
        endpoint=search_endpoint,
        index_name='mal-idx',
        credential=AzureKeyCredential(search_key)
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
