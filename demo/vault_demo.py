import idanalyzer

try:
    # initialize Core API with your api key and region (US/EU)
    vault = idanalyzer.Vault("Your API Key", "US")

    # List 5 items created on or after 2021/02/25
    # sort result by first name in ascending order, starting from first item.
    response = vault.list(filter=["createtime>=2021/02/25"], orderby="firstName", sort="ASC", limit=5, offset=0)

    # Get a single entry
    # response = vault.get("Vault_id")

    print(response)

except idanalyzer.APIError as e:
    # If API returns an error, catch it
    details = e.args[0]
    print("API error code: {}, message: {}".format(details["code"], details["message"]))
except Exception as e:
    print(e)
