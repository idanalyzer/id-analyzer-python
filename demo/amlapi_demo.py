import idanalyzer

try:
    # Initialize AML API with your api key and region (US/EU)
    aml = idanalyzer.AMLAPI("Your API Key", "US")

    # Raise exceptions for API level errors
    aml.throw_api_exception(True)

    # Set AML database to only search the PEP category
    aml.set_aml_database("global_politicians,eu_cors,eu_meps")

    # Search for a politician
    response1 = aml.search_by_name("Joe Biden")

    print(response1)

    # Set AML database to all databases
    aml.set_aml_database("")

    # Search for a sanctioned ID number
    response2 = aml.search_by_id_number("AALH750218HBCLPC02")

    print(response2)

except idanalyzer.APIError as e:
    # If API returns an error, catch it
    details = e.args[0]
    print("API error code: {}, message: {}".format(details["code"], details["message"]))
except Exception as e:
    print(e)
