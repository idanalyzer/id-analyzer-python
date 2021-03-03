import idanalyzer

try:
    # initialize Core API with your api key and region (US/EU)
    docupass = idanalyzer.DocuPass("Your API Key", "Your Company Name Inc.", "US")

    # We need to set an identifier so that we know internally who we are verifying,
    # this string will be returned in the callback. You can use your own user/customer id.
    docupass.set_custom_id("CUSTOMER1234")
    
    # Enable vault cloud storage to store verification results
    docupass.enable_vault(True)
    
    # Set a callback URL where verification results will be sent,
    # you can use docupass_callback.php under this folder as a template
    docupass.set_callback_url("https://www.your-website.com/docupass_callback.php")
    
    # We want DocuPass to return document image and user face image in URL format.
    docupass.set_callback_image(True, True, 1)
    
    # We will do a quick check on whether user have uploaded a fake ID
    docupass.enable_authentication(True, "quick", 0.3)
    
    # Enable photo facial biometric verification with threshold of 0.5
    docupass.enable_face_verification(True, 1, 0.5)
    
    # Users will have only 1 attempt for verification
    docupass.set_max_attempt(1)
    
    # We want to redirect user back to your website when they are done with verification
    docupass.set_redirection_url("https://www.your-website.com/verification_succeeded.html",
                                 "https://www.your-website.com/verification_failed.html")

    """ More parameters
    docupass.set_reusable(True) # allow docupass URL/QR Code to be used by multiple users
    docupass.set_language("en") # override auto language detection
    docupass.set_qrcode_format("000000","FFFFFF",5,1) # generate a QR code using custom colors and size
    docupass.set_welcome_message("We need to verify your driver license before you make a rental booking with our company.") # Display your own greeting message
    docupass.set_logo("https://www.your-website.com/logo.png") # change default logo to your own
    docupass.hide_branding_logo(True) # hide footer logo
    docupass.restrict_country("US,CA,AU") # accept documents from United States, Canada and Australia
    docupass.restrict_state("CA,TX,WA") # accept documents from california, texas and washington
    docupass.restrict_type("DI") # accept only driver license and identification card
    docupass.verify_expiry(True) # check document expiry
    docupass.verify_age("18-120") # check if person is above 18
    docupass.verify_dob("1990/01/01") # check if person's birthday is 1990/01/01
    docupass.verify_document_number("X1234567") # check if the person's ID number is X1234567
    docupass.verify_name("Elon Musk") # check if the person is named Elon Musk
    docupass.verify_address("123 Sunny Rd, California") # Check if address on ID matches with provided address
    docupass.verify_postcode("90001") # check if postcode on ID matches with provided postcode
    """

    # Create a mobile verification session for this user
    response = docupass.create_mobile()

    # Create Live Mobile Module
    # docupass.create_live_mobile()

    # Create URL Redirection Module
    # docupass.create_redirection()

    # Create Iframe Module
    # docupass.create_iframe()

    print(response)

    print("Scan the QR Code below to verify your identity: ")
    print(response['qrcode'])
    print("Or open your mobile browser and type in: ")
    print(response['url'])

except idanalyzer.APIError as e:
    # If API returns an error, catch it
    details = e.args[0]
    print("API error code: {}, message: {}".format(details["code"], details["message"]))
except Exception as e:
    print(e)
