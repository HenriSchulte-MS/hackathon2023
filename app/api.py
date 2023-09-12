import requests


# set the headers
headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0"
    }


def get_account_id(account_name):
    url = "https://microsoftsales.api.crm.dynamics.com/api/data/v9.1/accounts"

    # set the query parameters to filter the results for a specific account
    query_params = {
        "$filter": "startswith(name, 'Nordea') and address1_country eq 'Denmark' and _parentaccountid_value ne null"
    }

    # send the GET request to the API endpoint
    response = requests.get(url, params=query_params, headers=headers)

    # check if the request was successful
    if response.status_code == 200:
        # parse the response JSON data
        data = response.json()

        # print the account names
        for account in data["value"]:
            print(account["name"], account["_parentaccountid_value"])
            return account["_parentaccountid_value"]
            # print everything in account

    else:
        # print the error message
        print(f"Error: {response.status_code}", response.text)

# # call api url
def get_opportunities_for_account(account_name):
    url = "https://microsoftsales.api.crm.dynamics.com/api/data/v9.1/opportunities"

    account_id = get_account_id(account_name)
    print(account_id)
    # set the query parameters to filter the results

    query_params = {
        "$filter": f"_parentaccountid_value eq '{account_id}' and createdon gt '2023-01-01T00:00:00Z'"
    }

    # send the GET request to the API endpoint
    response = requests.get(url, params=query_params, headers=headers)

    # check if the request was successful
    if response.status_code == 200:
        # parse the response JSON data
        data = response.json()

        # print the account names
        for opportunity in data["value"]:
            print(opportunity["msp_opportunitynumber"], opportunity["name"], opportunity["createdon"], opportunity["msp_actualclosedatetime"])
    else:
        # print the error message
        print(f"Error: {response.status_code}", response.text)

#get_account_id("Nordea")
get_opportunities_for_account("Nordea")