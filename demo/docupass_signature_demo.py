import idanalyzer

try:
    # Initialize DocuPass API with your api key and region (US/EU)
    docupass = idanalyzer.DocuPass("Your API Key", "Your Company Name Inc.", "US")

    # Raise exceptions for API level errors
    docupass.throw_api_exception(True)

    # We need to set an identifier so that we know internally who is signing the document,
    # this string will be returned in the callback. You can use your own user/customer id.
    docupass.set_custom_id("CUSTOMER1234")
    
    # Enable vault cloud storage to store signed document
    docupass.enable_vault(True)
    
    # Set a callback URL where signed document will be sent,
    # you can use docupass_callback.php under this folder as a template to receive the result
    docupass.set_callback_url("https://www.your-website.com/docupass_callback.php")

    # We want to redirect user back to your website when they are done with document signing,
    # there will be no fail URL unlike identity verification
    docupass.set_redirection_url("https://www.your-website.com/document_signed.html", "")

    """ More parameters
    docupass.set_reusable(True) # allow docupass URL/QR Code to be used by multiple users
    docupass.set_language("en") # override auto language detection
    docupass.set_qrcode_format("000000","FFFFFF",5,1) # generate a QR code using custom colors and size
    docupass.hide_branding_logo(True) # hide footer logo
    docupass.set_custom_html_url("https://www.yourwebsite.com/docupass_template.html") # use your own HTML/CSS for DocuPass page
    docupass.sms_contract_link("+1333444555")  # Send signing link to user's mobile phone
    """

    #Assuming in your contract template you have a dynamic field %{email} and you want to fill it with user email
    prefill = {
        "email": "user@example.com"
    }

    # Create a signature session for this user
    response = docupass.create_signature("Template ID", "PDF", prefill)

    print(response)

    print("Scan the QR Code below to sign document: ")
    print(response['qrcode'])
    print("Or open your mobile browser and navigate to: ")
    print(response['url'])

except idanalyzer.APIError as e:
    # If API returns an error, catch it
    details = e.args[0]
    print("API error code: {}, message: {}".format(details["code"], details["message"]))
except Exception as e:
    print(e)
