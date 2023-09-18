import requests
from semantic_kernel.skill_definition import sk_function
from keyvault import KeyVault

class MSSalesPlugin:
    
    # Get secrets from keyvault
    keyvault = KeyVault()
    TOKEN_NAME = 'CRMToken'
    token = keyvault.get_secret(TOKEN_NAME)

    # set the headers
    headers = {
            "Authorization": "Bearer " + token,
            "Accept": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0"
    }

    @sk_function(
        description="Retrieves account id from MSSales",
        name="getAccountID",
        input_description="The account name",
    )
    def get_account_id(self, account_name: str) -> str:
        url = "https://<ORG NAME>.api.crm.dynamics.com/api/data/v9.1/accounts"
        country = "Denmark"

        # set the query parameters to filter the results for a specific account
        query_params = {
            "$filter": f"startswith(name, '{account_name}') and address1_country eq '{country}' and _parentaccountid_value ne null"
        }

        # send the GET request to the API endpoint
        response = requests.get(url, params=query_params, headers=self.headers)

        # check if the request was successful
        if response.status_code == 200:
            # parse the response JSON data
            data = response.json()

            # print the account names
            for account in data["value"]:
                #print(account["name"], account["_parentaccountid_value"])
                return account["_parentaccountid_value"]

        else:
            # print the error message
            print(f"Error: {response.status_code}", response.text)


    @sk_function(
        description="Get opportunities for account from MSSales",
        name="getOpportunities",
        input_description="The account ID",
    )
    def get_opportunities_for_account(self, account_id: str) -> str:
        url = "https://<ORG NAME>.api.crm.dynamics.com/api/data/v9.1/opportunities"
        cutoff_date = "2023-01-01T00:00:00Z"

        query_params = {
            "$filter": f"_parentaccountid_value eq '{account_id}' and createdon gt '{cutoff_date}'"
        }

        # send the GET request to the API endpoint
        response = requests.get(url, params=query_params, headers=self.headers)

        # check if the request was successful
        if response.status_code == 200:
            # parse the response JSON data
            data = response.json()

            # print the account names
            # for opportunity in data["value"]:
            #     print(opportunity["msp_opportunitynumber"], opportunity["name"], opportunity["createdon"], opportunity["msp_actualclosedatetime"])
            return "\n".join([f'Opportunity ID: {o["msp_opportunitynumber"]}, Opportunity name: {o["name"]}, Created: {o["createdon"]}, Closed: {o["msp_actualclosedatetime"]}' for o in data["value"]])
        else:
            raise Exception(f"Error: {response.status_code}", response.text)

