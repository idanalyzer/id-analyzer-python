
# ID Analyzer Python SDK
This is a python SDK library for [ID Analyzer Identity Verification APIs](https://www.idanalyzer.com), though all the APIs can be called with without the SDK using simple HTTP requests as outlined in the [documentation](https://developer.idanalyzer.com), you can use this SDK to accelerate server-side development.

We strongly discourage users to connect to ID Analyzer API endpoint directly from client-side applications that will be distributed to end user, such as mobile app, or in-browser JavaScript. Your API key could be easily compromised, and if you are storing your customer's information inside Vault they could use your API key to fetch all your user details. Therefore, the best practice is always to implement a client side connection to your server, and call our APIs from the server-side.

## Installation
Install through PIP

```shell
pip install idanalyzer
```

## Core API

[ID Analyzer Core API](https://www.idanalyzer.com/products/id-analyzer-core-api.html) allows you to perform OCR data extraction, facial biometric verification, identity verification, age verification, document cropping, document authentication (fake ID check), and paperwork automation using an ID image (JPG, PNG, PDF accepted) and user selfie photo or video. Core API has great global coverage, supporting over 98% of the passports, driver licenses and identification cards currently being circulated around the world.

![Sample ID](https://www.idanalyzer.com/img/sampleid1.jpg)

The sample code below will extract data from this sample Driver License issued in California, compare it with a [photo of Lena](https://upload.wikimedia.org/wikipedia/en/7/7d/Lenna_%28test_image%29.png), and check whether the ID is real or fake.

```python
import idanalyzer

try:
    # Initialize Core API with your api key and region (US/EU)
    coreapi = idanalyzer.CoreAPI("Your API Key", "US")

    # Raise exceptions for API level errors
    coreapi.throw_api_exception(True)
    
    # enable document authentication using quick module
    coreapi.enable_authentication(True, 'quick')

    # perform scan
    response = coreapi.scan(document_primary="https://www.idanalyzer.com/img/sampleid1.jpg", biometric_photo="https://upload.wikimedia.org/wikipedia/en/7/7d/Lenna_%28test_image%29.png")

    # All the information about this ID will be returned in response dictionary
    print(response)

    # Print document holder name
    if response.get('result'):
        data_result = response['result']
        print("Hello your name is {} {}".format(data_result['firstName'],data_result['lastName']))

    # Parse document authentication results
    if response.get('authentication'):
        authentication_result = response['authentication']
        if authentication_result['score'] > 0.5:
            print("The document uploaded is authentic")
        elif authentication_result['score'] > 0.3:
            print("The document uploaded looks little bit suspicious")
        else:
            print("The document uploaded is fake")

    # Parse biometric verification results
    if response.get('face'):
        face_result = response['face']
        if face_result['isIdentical']:
            print("Face verification PASSED!")
        else:
            print("Face verification FAILED!")

        print("Confidence Score: "+face_result['confidence'])

except idanalyzer.APIError as e:
    # If API returns an error, catch it
    details = e.args[0]
    print("API error code: {}, message: {}".format(details["code"], details["message"]))
    
except Exception as e:
    print(e)
```

You could also set additional parameters before performing ID scan:

```python
coreapi.enable_vault(True,False,False,False)  # enable vault cloud storage to store document information and image
coreapi.set_biometric_threshold(0.6) # make face verification more strict
coreapi.enable_authentication(True, 2) # check if document is real using module v2
coreapi.enable_barcode_mode(False) # disable OCR and scan for AAMVA barcodes only
coreapi.enable_image_output(True,True,"url") # output cropped document and face region in URL format
coreapi.enable_dualside_check(True) # check if data on front and back of ID matches
coreapi.set_vault_data("user@example.com",12345,"AABBCC") # store custom data into vault
coreapi.restrict_country("US,CA,AU") # accept documents from United States, Canada and Australia
coreapi.restrict_state("CA,TX,WA") # accept documents from california, texas and washington
coreapi.restrict_type("DI") # accept only driver license and identification card
coreapi.set_ocr_image_resize(0) # disable OCR resizing
coreapi.verify_expiry(True) # check document expiry
coreapi.verify_age("18-120") # check if person is above 18
coreapi.verify_dob("1990/01/01") # check if person's birthday is 1990/01/01
coreapi.verify_document_number("X1234567") # check if the person's ID number is X1234567
coreapi.verify_name("Elon Musk") # check if the person is named Elon Musk
coreapi.verify_address("123 Sunny Rd, California") # check if address on ID matches with provided address
coreapi.verify_postcode("90001") # check if postcode on ID matches with provided postcode
coreapi.enable_aml_check(True)  # enable AML/PEP compliance check
coreapi.set_aml_database("global_politicians,eu_meps,eu_cors")  # limit AML check to only PEPs
coreapi.enable_aml_strict_match(True)  # make AML matching more strict to prevent false positives
coreapi.generate_contract("Template ID", "PDF", {"email":"user@example.com"}); # generate a PDF document autofilled with data from user ID
```

To **scan both front and back of ID**:

```python
response = coreapi.scan(document_primary="id_front.jpg", document_secondary="id_back.jpg")
```

To perform **biometric video verification**:

```python
response = coreapi.scan(document_primary="id_front.jpg", biometric_video="face_video.mp4", biometric_video_passcode="1234")
```

Check out sample response array fields visit [Core API reference](https://developer.idanalyzer.com/coreapi.html##readingresponse).

## DocuPass API

[DocuPass](https://www.idanalyzer.com/products/docupass.html) allows you to verify your users without designing your own web page or mobile UI. A unique DocuPass URL can be generated for each of your users and your users can verify their own identity by simply opening the URL in their browser. DocuPass URLs can be directly opened using any browser,  you can also embed the URL inside an iframe on your website, or within a WebView inside your iOS/Android/Cordova mobile app.

![DocuPass Screen](https://www.idanalyzer.com/img/docupassliveflow.jpg)

DocuPass comes with 4 modules and you need to [choose an appropriate DocuPass module](https://www.idanalyzer.com/products/docupass.html) for integration.

To start, we will assume you are trying to **verify one of your user that has an ID of "5678"** in your own database, we need to **generate a DocuPass verification request for this user**. A unique **DocuPass reference code** and **URL** will be generated.

```python
import idanalyzer

try:
    # Initialize Core API with your api key and region (US/EU)
    docupass = idanalyzer.DocuPass("Your API Key", "Your Company Name Inc.", "US")

    # Raise exceptions for API level errors
    docupass.throw_api_exception(True)
    
    # We need to set an identifier so that we know internally who we are verifying,
    # this string will be returned in the callback. You can use your own user/customer id.
    docupass.set_custom_id("5678")
    
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
```

If you are looking to embed DocuPass into your mobile application, simply embed `$result['url']` inside a WebView. To tell if verification has been completed monitor the WebView URL and check if it matches the URLs set in setRedirectionURL. (DocuPass Live Mobile currently cannot be embedded into native iOS App due to OS restrictions, you will need to open it with Safari)

Check out additional DocuPass settings:

```python
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
docupass.set_custom_html_url("https://www.yourwebsite.com/docupass_template.html") # use your own HTML/CSS for DocuPass page
docupass.sms_verification_link("+1333444555")  # Send verification link to user's mobile phone
docupass.enable_phone_verification(True)  # get user to input their own phone number for verification
docupass.verify_phone("+1333444555")  # verify user's phone number you already have in your database
docupass.enable_aml_check(True)  # enable AML/PEP compliance check
docupass.set_aml_database("global_politicians,eu_meps,eu_cors")  # limit AML check to only PEPs
docupass.enable_aml_strict_match(True)  # make AML matching more strict to prevent false positives
docupass.generate_contract("Template ID", "PDF", {"somevariable": "somevalue"}) # automate paperwork by generating a document autofilled with ID data
docupass.sign_contract("Template ID", "PDF", {"somevariable": "somevalue"}) # get user to review and sign legal document prefilled with ID data
```

Now you should write a **callback script** or a **webhook**, to receive the verification results.  Visit [DocuPass Callback reference](https://developer.idanalyzer.com/docupass_callback.html) to check out the full payload returned by DocuPass. Callback script is generally programmed in a server environment and is beyond the scope of this guide, you can check out our [PHP SDK](https://github.com/idanalyzer/id-analyzer-php-sdk) for creating a callback script in PHP.

For the final step, you could create two web pages (URLS set via `set_redirection_url`) that display the results to your user. DocuPass reference will be passed as a GET parameter when users are redirected, for example: https://www.your-website.com/verification_succeeded.php?reference=XXXXXXXXX, you could use the reference code to fetch the results from your database. P.S. We will always send callbacks to your server before redirecting your user to the set URL.

## DocuPass Signature API

You can get user to review and remotely sign legal document in DocuPass without identity verification, to do so you need to create a DocuPass Signature session.

```python
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
```

Once user has reviewed and signed the document, the signed document will be sent back to your server using callback under the `contract.document_url` field, the contract will also be saved to vault if you have enabled vault.

## Vault API

ID Analyzer provides free cloud database storage (Vault) for you to store data obtained through Core API and DocuPass. You can set whether you want to store your user data into Vault through `enable_vault` while making an API request with PHP SDK. Data stored in Vault can be looked up through [Web Portal](https://portal.idanalyzer.com) or via Vault API.

If you have enabled Vault, Core API and DocuPass will both return a vault entry identifier string called `vaultid`,  you can use the identifier to look up your user data:

```python
import idanalyzer

try:
    # Initialize Core API with your api key and region (US/EU)
    vault = idanalyzer.Vault("Your API Key", "US")

    # Get vault item with vault ID
    response = vault.get("Vault_id")

    print(response)

except idanalyzer.APIError as e:
    # If API returns an error, catch it
    details = e.args[0]
    print("API error code: {}, message: {}".format(details["code"], details["message"]))
except Exception as e:
    print(e)
```

You can also list some of the items in your vault: 

```python
# List 5 items created on or after 2021/02/25
# sort result by first name in ascending order, starting from first item.
response = vault.list(filter=["createtime>=2021/02/25"], orderby="firstName", sort="ASC", limit=5, offset=0)
```


Alternatively, you may have a DocuPass reference code which you want to search through vault to check whether user has completed identity verification:

```python
response = vault.list(filter=["docupass_reference=XXXXXXXXXXXXX"])
```

Learn more about [Vault API](https://developer.idanalyzer.com/vaultapi.html).

## AML API

ID Analyzer provides Anti-Money Laundering AML database consolidated from worldwide authorities,  AML API allows our subscribers to lookup the database using either a name or document number. It allows you to instantly check if a person or company is listed under **any kind of sanction, criminal record or is a politically exposed person(PEP)**, as part of your **AML compliance KYC**. You may also use automated check built within Core API and DocuPass.

```python
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
```

Learn more about [AML API](https://developer.idanalyzer.com/amlapi.html).

## Demo

Check out **/demo** folder for more Python demos.

## SDK Reference

Check out [ID Analyzer Python SDK Reference](https://idanalyzer.github.io/id-analyzer-python/)