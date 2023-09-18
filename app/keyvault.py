from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class KeyVault:
    def __init__(self):
        self.vault_url = '<KEYVAULT URI>'
        self.credential = DefaultAzureCredential(
            exclude_environment_credential=True,
            exclude_managed_identity_credential=True,
            exclude_shared_token_cache_credential=True
        )

    def get_secret(self, secret_name):
        secret_client = SecretClient(vault_url=self.vault_url, credential=self.credential)
        secret = secret_client.get_secret(secret_name)
        return secret.value