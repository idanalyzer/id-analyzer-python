import re
import requests
import base64
import os.path


def is_valid_url(string):
    return re.search(r'(http(s)?://.)(www\.)?[-a-zA-Z0-9@:%._+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_+.~#?&/=]*)',
                     string)


def is_hex_color(string):
    return re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', string)


class APIError(Exception):
    pass


client_library = "python-sdk"

class CoreAPI:
    """
    Initialize Core API with an API key and optional region (US, EU)
    Core API is used to directly scan and validate global driver license, passport, and ID card.

    :param apikey: You API key
    :param region: US/EU, defaults to US
    :raises ValueError: Invalid input argument
    """
    DEFAULT_CONFIG = {
        "accuracy": 2,
        "authenticate": False,
        "authenticate_module": 1,
        "ocr_scaledown": 2000,
        "outputimage": False,
        "outputface": False,
        "outputmode": "url",
        "dualsidecheck": False,
        "verify_expiry": True,
        "verify_documentno": "",
        "verify_name": "",
        "verify_dob": "",
        "verify_age": "",
        "verify_address": "",
        "verify_postcode": "",
        "country": "",
        "region": "",
        "type": "",
        "checkblocklist": "",
        "vault_save": True,
        "vault_saveunrecognized": "",
        "vault_noduplicate": "",
        "vault_automerge": "",
        "vault_customdata1": "",
        "vault_customdata2": "",
        "vault_customdata3": "",
        "vault_customdata4": "",
        "vault_customdata5": "",
        "barcodemode": False,
        "biometric_threshold": 0.4,
        "aml_check": False,
        "aml_strict_match": False,
        "aml_database": "",
        "contract_generate": "",
        "contract_format": "",
        "contract_prefill_data": "",
        "client": client_library
    }

    def __init__(self, apikey, region="US"):
        if not apikey:
            raise ValueError("Please provide an API key")
        if not region:
            raise ValueError("Please set an API region (US, EU)")
        self.config = self.DEFAULT_CONFIG
        self.apikey = apikey
        self.throw_error = False
        if region.upper() == "EU":
            self.apiendpoint = "https://api-eu.idanalyzer.com/"
        elif region.upper() == "US":
            self.apiendpoint = "https://api.idanalyzer.com/"
        else:
            self.apiendpoint = region

    def throw_api_exception(self, throw_exception = False):
        """
        Whether an exception should be thrown if API response contains an error message

        :param throw_exception: Throw exception upon API error, defaults to false
        """
        self.throw_error = throw_exception is True

    def reset_config(self):
        """
        Reset all API configurations except API key and region.
        """
        self.config = self.DEFAULT_CONFIG

    def set_accuracy(self, accuracy=2):
        """
        Set OCR Accuracy

        :param accuracy: 0 = Fast, 1 = Balanced, 2 = Accurate, defaults to 2
        """
        self.config['accuracy'] = accuracy

    def enable_authentication(self, enabled=False, module=2):
        """
        Validate the document to check whether the document is authentic and has not been tampered,
        and set authentication module

        :param enabled: Enable or disable Document Authentication, defaults to False
        :param module: Authentication module version: 1, 2 or quick, defaults to 2
        :raises ValueError: Invalid input argument Invalid input argumentInvalid input argument
        """
        self.config['authenticate'] = enabled is True

        if enabled and module != 1 and module != 2 and module != 'quick':
            raise ValueError("Invalid authentication module, 1, 2 or 'quick' accepted.")

        self.config['authenticate_module'] = module

    def set_ocr_image_resize(self, max_scale=2000):
        """
        Scale down the uploaded image before sending to OCR engine. Adjust this value to fine tune recognition
        accuracy on large full-resolution images. Set 0 to disable image resizing.

        :param max_scale: 0 or 500~4000, defaults to 2000
        :raises ValueError: Invalid input argument Invalid input argumentInvalid input argument
        """
        if max_scale != 0 and (max_scale < 500 or max_scale > 4000):
            raise ValueError("Invalid scale value, 0, or 500 to 4000 accepted.")

        self.config['ocr_scaledown'] = max_scale

    def set_biometric_threshold(self, threshold=0.4):
        """
        Set the minimum confidence score to consider faces being identical

        :param threshold: float between 0 to 1, higher value yields more strict verification, defaults to 0.4
        :raises ValueError: Invalid input argument Invalid input argumentInvalid input argument
        """
        if threshold <= 0 or threshold > 1:
            raise ValueError("Invalid threshold value, float between 0 to 1 accepted.")

        self.config['biometric_threshold'] = threshold

    def enable_image_output(self, crop_document=False, crop_face=False, output_format="url"):
        """
        Generate cropped image of document and/or face, and set output format [url, base64]

        :param crop_document: Enable or disable document cropping, defaults to False
        :param crop_face: Enable or disable face cropping, defaults to False
        :param output_format: url or base64, defaults to url
        :raises ValueError: Invalid input argument Invalid input argumentInvalid input argument
        """
        if output_format != 'url' and output_format != 'base64':
            raise ValueError("Invalid output format, 'url' or 'base64' accepted.")

        self.config['outputimage'] = crop_document is True
        self.config['outputface'] = crop_face is True
        self.config['outputmode'] = output_format

    def enable_aml_check(self, enabled=False):
        """
        Check document holder's name and document number against ID Analyzer AML Database for sanctions, crimes and PEPs.

        :param enabled: Enable or disable AML/PEP check
        """
        self.config["aml_check"] = enabled is True

    def set_aml_database(self, databases="au_dfat,ca_dfatd,ch_seco,eu_fsf,fr_tresor_gels_avoir,gb_hmt,ua_sfms,un_sc,us_ofac,eu_cor,eu_meps,global_politicians,interpol_red"):
        """
        Specify the source databases to perform AML check, if left blank, all source databases will be checked.
        Separate each database code with comma, for example: un_sc,us_ofac. For full list of source databases and corresponding code visit AML API Overview.

        :param databases: Database codes separated by comma
        """
        self.config["aml_database"] = databases

    def enable_aml_strict_match(self, enabled=False):
        """
        By default, entities with identical name or document number will be considered a match even though their birthday or nationality may be unknown.
        Enable this parameter to reduce false-positives by only matching entities with exact same nationality and birthday.

        :param enabled: Enable or disable AML strict match mode
        """
        self.config["aml_strict_match"] = enabled is True

    def enable_dualside_check(self, enabled=False):
        """
        Check if the names, document number and document type matches between the front and the back of the document
        when performing dual-side scan. If any information mismatches error 14 will be thrown.

        :param enabled: Enable or disable dual-side information check, defaults to False
        """
        self.config['dualsidecheck'] = enabled is True

    def verify_expiry(self, enabled=False):
        """
        Check if the document is still valid based on its expiry date.

        :param enabled: Enable or disable expiry check, defaults to False
        """
        self.config['verify_expiry'] = enabled is True

    def verify_document_number(self, document_number):
        """
        Check if supplied document or personal number matches with document.

        :param document_number: Document or personal number requiring validation
        :raises ValueError: Invalid input argument Invalid input argumentInvalid input argument
        """
        if not document_number:
            self.config['verify_documentno'] = ""
        else:
            self.config['verify_documentno'] = document_number

    def verify_name(self, full_name):
        """
        Check if supplied name matches with document.

        :param full_name: Full name requiring validation
        :raises ValueError: Invalid input argument Invalid input argument
        """
        if not full_name:
            self.config['verify_name'] = ""
        else:
            self.config['verify_name'] = full_name

    def verify_dob(self, dob):
        """
        Check if supplied date of birth matches with document.

        :param dob: Date of birth in YYYY/MM/DD
        :raises ValueError: Invalid input argument
        """
        if not dob:
            self.config['verify_dob'] = ""
        else:
            if not re.search(r'^(\d{4}/\d{2}/\d{2})$', dob):
                raise ValueError("Invalid birthday format (YYYY/MM/DD)")

            self.config['verify_dob'] = dob

    def verify_age(self, age_range):
        """
        Check if the document holder is aged between the given range.

        :param age_range: Age range, example: 18-40
        :raises ValueError: Invalid input argument
        """
        if not age_range:
            self.config['verify_age'] = ""
        else:
            if not re.search(r'^(\d+-\d+)$', age_range):
                raise ValueError("Invalid age range format (minAge-maxAge)")

            self.config['verify_age'] = age_range

    def verify_address(self, address):
        """
        Check if supplied address matches with document.

        :param address: Address requiring validation
        """
        if not address:
            self.config['verify_address'] = ""
        else:
            self.config['verify_address'] = address

    def verify_postcode(self, postcode):
        """
        Check if supplied postcode matches with document.

        :param postcode: Postcode requiring validation
        """
        if not postcode:
            self.config['verify_postcode'] = ""
        else:
            self.config['verify_postcode'] = postcode

    def restrict_country(self, country_codes):
        """
        Check if the document was issued by specified countries, if not error code 10 will be thrown.
        Separate multiple values with comma. For example "US,CA" would accept documents from United States and Canada.

        :param country_codes: ISO ALPHA-2 Country Code separated by comma
        """
        if not country_codes:
            self.config['country'] = ""
        else:
            self.config['country'] = country_codes

    def restrict_state(self, states):
        """
        Check if the document was issued by specified state, if not error code 11 will be thrown.
        Separate multiple values with comma. For example "CA,TX" would accept documents from California and Texas.

        :param states: State full name or abbreviation separated by comma
        """
        if not states:
            self.config['region'] = ""
        else:
            self.config['region'] = states

    def restrict_type(self, document_type="DIP"):
        """
        Check if the document was one of the specified types, if not error code 12 will be thrown.
        For example, "PD" would accept both passport and drivers license.

        :param document_type: P: Passport, D: Driver's License, I: Identity Card
        """
        if not document_type:
            self.config['type'] = ""
        else:
            self.config['type'] = document_type

    def enable_barcode_mode(self, enabled=False):
        """
        Disable Visual OCR and read data from AAMVA Barcodes only

        :param enabled: Enable or disable Barcode Mode
        """
        self.config['barcodemode'] = enabled is True

    def enable_vault(self, enabled=True, save_unrecognized=False, no_duplicate_image=False, auto_merge_document=False):
        """
        Save document image and parsed information in your secured vault.
        You can list, search and update document entries in your vault through Vault API or web portal.

        :param enabled: Enable or disable Vault
        :param save_unrecognized: Save document image in your vault even if the document cannot be recognized.
        :param no_duplicate_image: Prevent duplicated images from being saved.
        :param auto_merge_document: Merge images with same document number into a single entry inside vault.
        """
        self.config['vault_save'] = enabled is True
        self.config['vault_saveunrecognized'] = save_unrecognized is True
        self.config['vault_noduplicate'] = no_duplicate_image is True
        self.config['vault_automerge'] = auto_merge_document is True

    def set_vault_data(self, data1="", data2="", data3="", data4="", data5=""):
        """
        Add up to 5 custom strings that will be associated with the vault entry,
        this can be useful for filtering and searching entries.

        :param data1: Custom data field 1
        :param data2: Custom data field 2
        :param data3: Custom data field 3
        :param data4: Custom data field 4
        :param data5: Custom data field 5
        """
        self.config['vault_customdata1'] = data1
        self.config['vault_customdata2'] = data2
        self.config['vault_customdata3'] = data3
        self.config['vault_customdata4'] = data4
        self.config['vault_customdata5'] = data5

    def generate_contract(self, template_id, out_format="PDF", prefill_data=None):
        """
        Generate legal document using data from user uploaded ID

        :param template_id: Contract Template ID displayed under web portal
        :param out_format: Output file format: PDF, DOCX or HTML
        :param prefill_data: Dictionary or JSON string, to autofill dynamic fields in contract template.
        :raises ValueError: Invalid input argument
        """
        if prefill_data is None:
            prefill_data = {}
        if not template_id:
            raise ValueError("Invalid template ID")

        self.config['contract_generate'] = template_id
        self.config['contract_format'] = out_format
        self.config['contract_prefill_data'] = prefill_data

    def set_parameter(self, parameter_key, parameter_value):
        """
        Set an API parameter and its value, this function allows you to set any API parameter without using the built-in functions

        :param parameter_key: Parameter key
        :param parameter_value: Parameter value
        """
        self.config[parameter_key] = parameter_value

    def scan(self, **options):
        r"""
        Perform scan on ID document with Core API,
        optionally specify document back image, face verification image, face verification video and video passcode

        :param \**options:
            See below

        :Keyword Arguments:
            * *document_primary* (``str``) --
              Front of Document (File path, base64 content or URL)
            * *document_secondary* (``str``) --
              Back of Document (File path, base64 content or URL)
            * *biometric_photo* (``str``) --
              Face Photo (File path, base64 content or URL)
            * *biometric_video* (``str``) --
              Face Video (File path, base64 content or URL)
            * *biometric_video* (``str``) --
              Face Video Passcode (4 Digit Number)


        :return Scan and verification results of ID document
        :rtype: dict
        :raises ValueError: Invalid input argument
        :raises APIError: API returned an error
        """
        payload = self.config
        payload["apikey"] = self.apikey

        if not options.get('document_primary'):
            raise ValueError("Primary document image required.")

        if is_valid_url(options['document_primary']):
            payload['url'] = options['document_primary']
        elif os.path.isfile(options['document_primary']):
            with open(options['document_primary'], "rb") as image_file:
                payload['file_base64'] = base64.b64encode(image_file.read())
        elif len(options['document_primary']) > 100:
            payload['file_base64'] = options['document_primary']
        else:
            raise ValueError("Invalid primary document image, file not found or malformed URL.")

        if options.get('document_secondary'):
            if is_valid_url(options['document_secondary']):
                payload['url_back'] = options['document_secondary']
            elif os.path.isfile(options['document_secondary']):
                with open(options['document_secondary'], "rb") as image_file:
                    payload['file_back_base64'] = base64.b64encode(image_file.read())
            elif len(options['document_secondary']) > 100:
                payload['file_back_base64'] = options['document_secondary']
            else:
                raise ValueError("Invalid secondary document image, file not found or malformed URL.")

        if options.get('biometric_photo'):
            if is_valid_url(options['biometric_photo']):
                payload['faceurl'] = options['biometric_photo']
            elif os.path.isfile(options['biometric_photo']):
                with open(options['biometric_photo'], "rb") as image_file:
                    payload['face_base64'] = base64.b64encode(image_file.read())
            elif len(options['biometric_photo']) > 100:
                payload['face_base64'] = options['biometric_photo']
            else:
                raise ValueError("Invalid face image, file not found or malformed URL.")

        if options.get('biometric_video'):
            if is_valid_url(options['biometric_video']):
                payload['videourl'] = options['biometric_video']
            elif os.path.isfile(options['biometric_video']):
                with open(options['biometric_video'], "rb") as image_file:
                    payload['video_base64'] = base64.b64encode(image_file.read())
            elif len(options['biometric_video']) > 100:
                payload['video_base64'] = options['biometric_video']
            else:
                raise ValueError("Invalid face video, file not found or malformed URL.")

            if not options.get('biometric_video_passcode') or not re.search(r'^([0-9]{4})$',
                                                                            options['biometric_video_passcode']):
                raise ValueError("Please provide a 4 digit passcode for video biometric verification.")
            else:
                payload['passcode'] = options['biometric_video_passcode']

        r = requests.post(self.apiendpoint, data=payload)
        r.raise_for_status()
        result = r.json()

        if not self.throw_error:
            return result

        if result.get('error'):
            raise APIError(result['error'])
        else:
            return result


class DocuPass:
    """
    Initialize DocuPass API with an API key, company name and optional region (US, EU)
    DocuPass allows rapid identity verification using a webpage or mobile app

    :param apikey: You API key
    :param company_name: Your company name to display in DocuPass pages
    :param region: US/EU, defaults to US
    :raises ValueError: Invalid input argument
    """
    DEFAULT_CONFIG = {
        "companyname": "",
        "callbackurl": "",
        "biometric": 0,
        "authenticate_minscore": 0,
        "authenticate_module": 2,
        "maxattempt": 1,
        "documenttype": "",
        "documentcountry": "",
        "documentregion": "",
        "dualsidecheck": False,
        "verify_expiry": False,
        "verify_documentno": "",
        "verify_name": "",
        "verify_dob": "",
        "verify_age": "",
        "verify_address": "",
        "verify_postcode": "",
        "successredir": "",
        "failredir": "",
        "customid": "",
        "vault_save": True,
        "return_documentimage": True,
        "return_faceimage": True,
        "return_type": 1,
        "qr_color": "",
        "qr_bgcolor": "",
        "qr_size": "",
        "qr_margin": "",
        "welcomemessage": "",
        "nobranding": "",
        "logo": "",
        "language": "",
        "biometric_threshold": 0.4,
        "reusable": False,
        "aml_check": False,
        "aml_strict_match": False,
        "aml_database": "",
        "phoneverification": False,
        "verify_phone": "",
        "sms_verification_link": "",
        "customhtmlurl": "",
        "contract_generate": "",
        "contract_sign": "",
        "contract_format": "",
        "contract_prefill_data": "",
        "sms_contract_link": "",
        "client": client_library

    }

    def __init__(self, apikey, company_name="My Company Name", region="US"):
        if not apikey:
            raise ValueError("Please provide an API key")
        if not company_name:
            raise ValueError("Please provide your company name")
        if not region:
            raise ValueError("Please set an API region (US, EU)")
        self.config = self.DEFAULT_CONFIG
        self.apikey = apikey
        self.throw_error = False
        self.config['companyname'] = company_name
        if region.upper() == "EU":
            self.apiendpoint = "https://api-eu.idanalyzer.com/"
        elif region.upper() == 'US':
            self.apiendpoint = "https://api.idanalyzer.com/"
        else:
            self.apiendpoint = region

    def throw_api_exception(self, throw_exception = False):
        """
        Whether an exception should be thrown if API response contains an error message

        :param throw_exception: Throw exception upon API error, defaults to false
        """
        self.throw_error = throw_exception is True

    def reset_config(self):
        """
        Reset all API configurations except API key and region.
        """
        self.config = self.DEFAULT_CONFIG

    def set_max_attempt(self, max_attempt=1):
        """
        Set max verification attempt per user

        :param max_attempt: 1 to 10
        :raises ValueError: Invalid input argument
        """
        if max_attempt not in range(1, 10):
            raise ValueError("Invalid max attempt, please specify integer between 1 to 10.")

        self.config['maxattempt'] = max_attempt

    def set_custom_id(self, custom_id):
        """
        Set a custom string that will be sent back to your server's callback, and appended to redirection URLs as a query string.
        It is useful for identifying your user within your database. This value will be stored under docupass_customid under Vault.

        :param custom_id: A string used to identify your customer internally
        """
        self.config['customid'] = custom_id

    def set_welcome_message(self, message):
        """
        Display a custom message to the user in the beginning of verification

        :param message: Plain text string
        """
        self.config['welcomemessage'] = message

    def set_logo(self, url="https://docupass.app/asset/logo1.png"):
        """
        Replace footer logo with your own logo

        :param url: Logo URL
        """
        self.config['logo'] = url

    def hide_branding_logo(self, hidden=False):
        """
        Hide all branding logo

        :param: hide logo, defaults to False
        """
        self.config['nobranding'] = hidden is True

    def set_custom_html_url(self, url):
        """
        Replace DocuPass page content with your own HTML and CSS, you can download the HTML/CSS template from DocuPass API Reference page

        :param url: URL pointing to your own HTML page
        """
        self.config['customhtmlurl'] = url

    def set_language(self, language):
        """
        DocuPass automatically detects user device language and display corresponding language.
        Set this parameter to override automatic language detection.

        :param language: Check DocuPass API reference for language code
        """
        self.config['language'] = language

    def set_callback_url(self, url="https://www.example.com/docupass_callback.php"):
        """
        Set server-side callback/webhook URL to receive verification results

        :param url: Callback URL
        :raises ValueError: Invalid input argument
        """
        if url and not is_valid_url(url):
            raise ValueError("Invalid URL, the host does not appear to be a remote host.")

        self.config['callbackurl'] = url

    def set_redirection_url(self, success_url="https://www.example.com/success.php",
                            fail_url="https://www.example.com/failed.php"):
        """
        Redirect client browser to set URLs after verification.
        DocuPass reference code and customid will be appended to the end of URL
        e.g. https://www.example.com/success.php?reference=XXXXXXXX&customid=XXXXXXXX

        :param success_url: Redirection URL after verification succeeded
        :param fail_url: Redirection URL after verification failed
        :raises ValueError: Invalid input argument
        """
        if success_url and not is_valid_url(success_url):
            raise ValueError("Invalid URL format for success URL")

        if fail_url and not is_valid_url(fail_url):
            raise ValueError("Invalid URL format for fail URL")

        self.config['successredir'] = success_url
        self.config['failredir'] = fail_url

    def enable_authentication(self, enabled=False, module=2, minimum_score=0.3):
        """
        Validate the document to check whether the document is authentic and has not been tampered

        :param enabled: Enable or disable document authentication, defaults to False
        :param module: Authentication Module: "1", "2" or "quick", defaults to "2"
        :param minimum_score: Minimum score to pass verification, defaults to 0.3
        :raises ValueError: Invalid input argument
        """
        if not enabled:
            self.config['authenticate_minscore'] = 0
        else:
            if not 0 < minimum_score <= 1:
                raise ValueError("Invalid minimum score, please specify float between 0 to 1.")

            if enabled and module != 1 and module != 2 and module != 'quick':
                raise ValueError("Invalid authentication module, 1, 2 or 'quick' accepted.")

            self.config['authenticate_module'] = module
            self.config['authenticate_minscore'] = minimum_score

    def enable_face_verification(self, enabled=False, verification_type=1, threshold=0.4):
        """
        Whether users will be required to submit a selfie photo or record selfie video for facial verification.

        :param enabled: Enable or disable facial biometric verification, defaults to False
        :param verification_type: 1 for photo verification, 2 for video verification, defaults to 1
        :param threshold: Minimum confidence score required to pass verification, value between 0 to 1, defaults to 0.4
        :raises ValueError: Invalid input argument
        """
        if not enabled:
            self.config['biometric'] = 0
        else:
            if verification_type == 1 or verification_type == 2:
                self.config['biometric'] = verification_type
                self.config['biometric_threshold'] = threshold
            else:
                raise ValueError("Invalid verification type, 1 for photo verification, 2 for video verification.")

    def set_reusable(self, reusable=False):
        """
        Enabling this parameter will allow multiple users to verify their identity through the same URL,
        a new DocuPass reference code will be generated for each user automatically.

        :param reusable: Set True to allow unlimited verification for a single DocuPass session, defaults to False
        """
        self.config['reusable'] = reusable is True

    def set_callback_image(self, return_documentimage=True, return_faceimage=True, return_type=1):
        """
        Enable or disable returning user uploaded document and face image in callback, and image data format.

        :param return_documentimage: Return document image in callback data, defaults to True
        :param return_faceimage: Return face image in callback data, defaults to True
        :param return_type: Image type: 0=base64, 1=url, defaults to 1
        """
        self.config['return_documentimage'] = return_documentimage is True
        self.config['return_faceimage'] = return_faceimage is True
        self.config['return_type'] = 0 if return_type == 0 else 1

    def set_qrcode_format(self, foreground_color="000000", background_color="FFFFFF", size=5, margin=1):
        """
        Configure QR code generated for DocuPass Mobile and Live Mobile

        :param foreground_color: Image foreground color HEX code, defaults to 000000
        :param background_color: Image background color HEX code, defaults to FFFFFF
        :param size: Image size: 1 to 50, defaults to 5
        :param margin: Image margin: 1 to 50, defaults to 1
        :raises ValueError: Invalid input argument
        """
        if not is_hex_color(foreground_color):
            raise ValueError("Invalid foreground color HEX code")

        if not is_hex_color(background_color):
            raise ValueError("Invalid background color HEX code")

        if size not in range(1, 50):
            raise ValueError("Invalid image size (1-50)")

        if margin not in range(0, 50):
            raise ValueError("Invalid margin (0-50)")

        self.config['qr_color'] = foreground_color
        self.config['qr_bgcolor'] = background_color
        self.config['qr_size'] = size
        self.config['qr_margin'] = margin

    def enable_dualside_check(self, enabled=False):
        """
        Check if the names, document number and document type matches between the front and the back of the document
        when performing dual-side scan. If any information mismatches error 14 will be thrown.

        :param enabled: Enable or disable dual-side information check, defaults to False
        """
        self.config['dualsidecheck'] = enabled is True

    def enable_aml_check(self, enabled=False):
        """
        Check document holder's name and document number against ID Analyzer AML Database for sanctions, crimes and PEPs.

        :param enabled: Enable or disable AML/PEP check
        """
        self.config["aml_check"] = enabled is True

    def set_aml_database(self,
                         databases="au_dfat,ca_dfatd,ch_seco,eu_fsf,fr_tresor_gels_avoir,gb_hmt,ua_sfms,un_sc,us_ofac,eu_cor,eu_meps,global_politicians,interpol_red"):
        """
        Specify the source databases to perform AML check, if left blank, all source databases will be checked.
        Separate each database code with comma, for example: un_sc,us_ofac. For full list of source databases and corresponding code visit AML API Overview.

        :param databases: Database codes separated by comma
        """
        self.config["aml_database"] = databases

    def enable_aml_strict_match(self, enabled=False):
        """
        By default, entities with identical name or document number will be considered a match even though their birthday or nationality may be unknown.
        Enable this parameter to reduce false-positives by only matching entities with exact same nationality and birthday.

        :param enabled: Enable or disable AML strict match mode
        """
        self.config["aml_strict_match"] = enabled is True

    def enable_phone_verification(self, enabled=False):
        """
        Whether to ask user to enter a phone number for verification, DocuPass supports both mobile or landline number verification.
        Verified phone number will be returned in callback JSON.

        :param enabled: Enable or disable user phone verification
        """
        self.config["phoneverification"] = enabled

    def sms_verification_link(self, mobile_number="+1333444555"):
        """
        DocuPass will send SMS to this number containing DocuPass link to perform identity verification, the number provided will be automatically considered as verified if user completes identity verification. If an invalid or unreachable number is provided error 1050 will be thrown.
        You should add your own thresholding mechanism to prevent abuse as you will be charged 1 quota to send the SMS.

        :param mobile_number: Mobile number should be provided in international format such as +1333444555
        """
        self.config["sms_verification_link"] = mobile_number

    def sms_contract_link(self, mobile_number="+1333444555"):
        """
        DocuPass will send SMS to this number containing DocuPass link to review and sign legal document. If an invalid or unreachable number is provided error 1050 will be thrown.
        You should add your own thresholding mechanism to prevent abuse as you will be charged 1 quota to send the SMS.

        :param mobile_number: Mobile number should be provided in international format such as +1333444555
        """
        self.config["sms_contract_link"] = mobile_number

    def verify_phone(self, phone_number="+1333444555"):
        """
        DocuPass will attempt to verify this phone number as part of the identity verification process,
        both mobile or landline are supported, users will not be able to enter their own numbers or change the provided number.

        :param phone_number: Mobile or landline number should be provided in international format such as +1333444555
        """
        self.config["verify_phone"] = phone_number

    def verify_expiry(self, enabled=False):
        """
        Check if the document is still valid based on its expiry date.

        :param enabled: Enable or disable expiry check
        """
        self.config['verify_expiry'] = enabled is True

    def verify_document_number(self, document_number):
        """
        Check if supplied document or personal number matches with document.

        :param document_number: Document or personal number requiring validation
        :raises ValueError: Invalid input argument
        """
        if not document_number:
            self.config['verify_documentno'] = ""
        else:
            self.config['verify_documentno'] = document_number

    def verify_name(self, full_name):
        """
        Check if supplied name matches with document.

        :param full_name: Full name requiring validation
        :raises ValueError: Invalid input argument
        """
        if not full_name:
            self.config['verify_name'] = ""
        else:
            self.config['verify_name'] = full_name

    def verify_dob(self, dob):
        """
        Check if supplied date of birth matches with document.

        :param dob: Date of birth in YYYY/MM/DD
        :raises ValueError: Invalid input argument
        """
        if not dob:
            self.config['verify_dob'] = ""
        else:
            if not re.search(r'^(\d{4}/\d{2}/\d{2})$', dob):
                raise ValueError("Invalid birthday format (YYYY/MM/DD)")

            self.config['verify_dob'] = dob

    def verify_age(self, age_range="18-99"):
        """
        Check if the document holder is aged between the given range.

        :param age_range: Age range, example: 18-40
        :raises ValueError: Invalid input argument
        """
        if not age_range:
            self.config['verify_age'] = ""
        else:
            if not re.search(r'^(\d+-\d+)$', age_range):
                raise ValueError("Invalid age range format (minAge-maxAge)")

            self.config['verify_age'] = age_range

    def verify_address(self, address):
        """
        Check if supplied address matches with document.

        :param address: Address requiring validation
        """
        if not address:
            self.config['verify_address'] = ""
        else:
            self.config['verify_address'] = address

    def verify_postcode(self, postcode):
        """
        Check if supplied postcode matches with document.

        :param postcode: Postcode requiring validation
        """
        if not postcode:
            self.config['verify_postcode'] = ""
        else:
            self.config['verify_postcode'] = postcode

    def restrict_country(self, country_codes):
        """
        Only accept document issued by specified countries. Separate multiple values with comma.
        For example "US,CA" would accept documents from United States and Canada.

        :param country_codes: ISO ALPHA-2 Country Code separated by comma
        """
        if not country_codes:
            self.config['documentcountry'] = ""
        else:
            self.config['documentcountry'] = country_codes

    def restrict_state(self, states):
        """
        Only accept document issued by specified state. Separate multiple values with comma.
        For example "CA,TX" would accept documents from California and Texas.

        :param states: State full name or abbreviation separated by comma
        """
        if not states:
            self.config['documentregion'] = ""
        else:
            self.config['documentregion'] = states

    def restrict_type(self, document_type="DIP"):
        """
        Only accept document of specified types. For example, "PD" would accept both passport and drivers license.

        :param document_type: P: Passport, D: Driver's License, I: Identity Card, defaults to DIP
        """
        if not document_type:
            self.config['documenttype'] = ""
        else:
            self.config['documenttype'] = document_type

    def enable_vault(self, enabled=True):
        """
        Save document image and parsed information in your secured vault.
        You can list, search and update document entries in your vault through Vault API or web portal.

        :param enabled Enable or disable Vault, defaults to True
        """
        self.config['vault_save'] = enabled is True

    def set_parameter(self, parameter_key, parameter_value):
        """
        Set an API parameter and its value, this function allows you to set any API parameter without using the built-in functions

        :param parameter_key: Parameter key
        :param parameter_value: Parameter value
        """
        self.config[parameter_key] = parameter_value

    def generate_contract(self, template_id, out_format="PDF", prefill_data=None):
        """
        Generate legal document using data from user uploaded ID

        :param template_id: Contract Template ID displayed under web portal
        :param out_format: Output file format: PDF, DOCX or HTML
        :param prefill_data: Dictionary or JSON string, to autofill dynamic fields in contract template.
        :raises ValueError: Invalid input argument
        """
        if prefill_data is None:
            prefill_data = {}
        if not template_id:
            raise ValueError("Invalid template ID")
        self.config['contract_sign'] = ""
        self.config['contract_generate'] = template_id
        self.config['contract_format'] = out_format
        self.config['contract_prefill_data'] = prefill_data

    def sign_contract(self, template_id, out_format="PDF", prefill_data=None):
        """
        Have user review and sign autofilled legal document after successful identity verification

        :param template_id: Contract Template ID displayed under web portal
        :param out_format: Output file format: PDF, DOCX or HTML
        :param prefill_data: Dictionary or JSON string, to autofill dynamic fields in contract template.
        :raises ValueError: Invalid input argument
        """
        if prefill_data is None:
            prefill_data = {}
        if not template_id:
            raise ValueError("Invalid template ID")
        self.config['contract_generate'] = ""
        self.config['contract_sign'] = template_id
        self.config['contract_format'] = out_format
        self.config['contract_prefill_data'] = prefill_data

    def create_signature(self,  template_id, out_format="PDF", prefill_data=None):
        """
        Create a DocuPass signature session for user to review and sign legal document without identity verification

        :param template_id: Contract Template ID displayed under web portal
        :param out_format: Output file format: PDF, DOCX or HTML
        :param prefill_data: Dictionary or JSON string, to autofill dynamic fields in contract template.
        :return DocuPass signature request response
        :rtype dict
        :raises ValueError: Invalid input argument
        :raises APIError: API error exception
        """
        if prefill_data is None:
            prefill_data = {}
        if not template_id:
            raise ValueError("Invalid template ID")
        payload = self.config
        payload["apikey"] = self.apikey
        payload["template_id"] = template_id
        payload['contract_format'] = out_format
        payload['contract_prefill_data'] = prefill_data

        r = requests.post(self.apiendpoint + "docupass/sign", data=payload)
        r.raise_for_status()
        result = r.json()

        if not self.throw_error:
            return result

        if result.get('error'):
            raise APIError(result['error'])
        else:
            return result

    def create_iframe(self):
        """
        Create a DocuPass session for embedding in web page as iframe

        :return DocuPass verification request response
        :rtype dict
        :raises ValueError: Invalid input argument
        :raises APIError: API error exception
        """
        return self.__create(0)

    def create_mobile(self):
        """
        Create a DocuPass session for users to open on mobile phone, or embedding in mobile app

        :return DocuPass verification request response
        :rtype dict
        :raises ValueError: Invalid input argument
        :raises APIError: API error exception
        """
        return self.__create(1)

    def create_redirection(self):
        """
        Create a DocuPass session for users to open in any browser

        :return DocuPass verification request response
        :rtype dict
        :raises ValueError: Invalid input argument
        :raises APIError: API error exception
        """
        return self.__create(2)

    def create_live_mobile(self):
        """
        Create a DocuPass Live Mobile verification session for users to open on mobile phone

        :return DocuPass verification request response
        :rtype dict
        :raises ValueError: Invalid input argument
        :raises APIError: API error exception
        """
        return self.__create(3)

    def __create(self, docupass_module):

        payload = self.config
        payload["apikey"] = self.apikey
        payload["type"] = docupass_module

        r = requests.post(self.apiendpoint + "docupass/create", data=payload)
        r.raise_for_status()
        result = r.json()

        if not self.throw_error:
            return result

        if result.get('error'):
            raise APIError(result['error'])
        else:
            return result

    def validate(self, reference, hash):
        """
        Validate data received through DocuPass Callback against DocuPass Server to prevent request spoofing

        :param reference: DocuPass Reference
        :param hash: DocuPass callback hash
        :return Whether validation succeeded
        :rtype bool
        :raises ValueError: Invalid input argument
        """
        payload = {
            "apikey": self.apikey,
            "reference": reference,
            "hash": hash,
            "client": client_library
        }

        r = requests.post(self.apiendpoint + "docupass/validate", data=payload)
        r.raise_for_status()
        result = r.json()
        return result.get('success')


class Vault:
    """
    Initialize Vault API with an API key, and optional region (US, EU)
    Vault API allows cloud storage of user ID and information retrieved from Core API and DocuPass

    :param apikey: You API key
    :param region: API Region US/EU, defaults to US
    :raises ValueError: Invalid input argument
    """

    def __init__(self, apikey, region="US"):
        if not apikey:
            raise ValueError("Please provide an API key")
        if not region:
            raise ValueError("Please set an API region (US, EU)")
        self.apikey = apikey
        self.throw_error = False
        if region.upper() == 'EU':
            self.apiendpoint = "https://api-eu.idanalyzer.com/"
        elif region.upper() == "US":
            self.apiendpoint = "https://api.idanalyzer.com/"
        else:
            self.apiendpoint = region

    def throw_api_exception(self, throw_exception = False):
        """
        Whether an exception should be thrown if API response contains an error message

        :param throw_exception: Throw exception upon API error, defaults to false
        """
        self.throw_error = throw_exception is True

    def get(self, vault_id):
        """
        Get a single vault entry

        :param str vault_id: Vault entry ID
        :return Vault entry data
        :rtype dict
        :raises ValueError: Invalid input argument
        :raises APIError: API Error
        """
        if not vault_id:
            raise ValueError("Vault entry ID required.")

        return self.__api("get", {"id": vault_id})

    def list(self, **options):
        r"""
        List multiple vault entries with optional filter, sorting and paging arguments
        Refer to https://developer.idanalyzer.com/vaultapi.html for filter statements and field names

        :param \**options:
            See below

        :Keyword Arguments:
            * *filter* (``list[str]``) --
              List of filter statements
            * *orderby* (``str``) --
              Field name used to order the results
            * *sort* (``str``) --
              Sort results by ASC = Ascending, DESC = DESCENDING
            * *limit* (``int``) --
              Number of results to return
            * *offset* (``int``) --
              Offset the first result using specified index


        :return A list of vault items
        :rtype dict
        :raises ValueError: Invalid input argument
        :raises APIError: API Error
        """
        payload = {}
        if options.get('filter'):
            if not isinstance(options['filter'], list) or len(options['filter']) > 5:
                raise ValueError("Filter must be an array and must not exceed maximum 5 filter strings.")

            payload['filter'] = options['filter']

        if options.get('orderby'):
            payload['orderby'] = options['orderby']
        else:
            payload['orderby'] = "createtime"

        if options.get('sort'):
            payload['sort'] = options['sort']
        else:
            payload['sort'] = "DESC"

        if options.get('limit'):
            payload['limit'] = options['limit']
        else:
            payload['limit'] = 10

        if options.get('offset'):
            payload['offset'] = options['offset']
        else:
            payload['offset'] = 0

        return self.__api("list", payload)

    def update(self, vault_id, data=None):
        """
        Update vault entry with new data

        :param vault_id: Vault entry ID
        :param data: dictionary of the field key and its value
        :return Whether updates succeeded
        :rtype dict
        :raises ValueError: Invalid input argument
        :raises APIError: API Error
        """
        if not vault_id:
            raise ValueError("Vault entry ID required.")

        if not isinstance(data, dict):
            raise ValueError("Data needs to be a dictionary.")

        if len(data) < 1:
            raise ValueError("Minimum one set of data required.")

        data['id'] = vault_id
        return self.__api("update", data)

    def delete(self, vault_id):
        """
        Delete a single or multiple vault entries

        :param vault_id: Vault entry ID or array of IDs
        :return Whether delete succeeded
        :rtype dict
        :raises ValueError: Invalid input argument
        :raises APIError: API Error
        """
        if not vault_id:
            raise ValueError("Vault entry ID required.")

        return self.__api("delete", {"id": vault_id})

    def add_image(self, id, image, type=0):
        """
        Add a document or face image into an existing vault entry

        :param id: Vault entry ID
        :param image: Image file path, base64 content or URL
        :param type: Type of image: 0 = document, 1 = person
        :return New image object
        :rtype dict
        :raises ValueError: Invalid input argument
        :raises APIError: API Error
        """
        if not id:
            raise ValueError("Vault entry ID required.")

        if type != 0 and type != 1:
            raise ValueError("Invalid image type, 0 or 1 accepted.")

        payload = {"id": id, "type": type}
        if is_valid_url(image):
            payload['imageurl'] = image
        elif os.path.isfile(image):
            with open(image, "rb") as image_file:
                payload['image'] = base64.b64encode(image_file.read())
        elif len(image) > 100:
            payload['image'] = image
        else:
            raise ValueError("Invalid image, file not found or malformed URL.")

        return self.__api("addimage", payload)

    def delete_image(self, vault_id, image_id):
        """
        Delete an image from vault

        :param vault_id: Vault entry ID
        :param image_id: Image ID
        :return Whether delete succeeded
        :rtype dict
        :raises ValueError: Invalid input argument
        :raises APIError: API Error
        """
        if not vault_id:
            raise ValueError("Vault entry ID required.")

        if not image_id:
            raise ValueError("Image ID required.")

        return self.__api("deleteimage", {"id": vault_id, "imageid": image_id})

    def search_face(self, image, max_entry=10, threshold=0.5):
        """
        Search vault using a person's face image

        :param image: Face image file path, base64 content or URL
        :param max_entry: Number of entries to return, 1 to 10.
        :param threshold: Minimum confidence score required for face matching
        :return List of vault entries
        :rtype dict
        :raises ValueError: Invalid input argument
        :raises APIError: API Error
        """
        payload = {"maxentry": max_entry, "threshold": threshold}
        if is_valid_url(image):
            payload['imageurl'] = image
        elif os.path.isfile(image):
            with open(image, "rb") as image_file:
                payload['image'] = base64.b64encode(image_file.read())
        elif len(image) > 100:
            payload['image'] = image
        else:
            raise ValueError("Invalid image, file not found or malformed URL.")

        return self.__api("searchface", payload)

    def train_face(self):
        """
        Train vault for face search

        :return Face training result
        :rtype dict
        :raises ValueError: Invalid input argument
        :raises APIError: API Error
        """
        return self.__api("train")

    def training_status(self):
        """
        Get vault training status

        :return Training status
        :rtype dict
        :raises ValueError: Invalid input argument
        :raises APIError: API Error
        """
        return self.__api("trainstatus")

    def __api(self, action, payload=None):
        if not payload:
            payload = {}

        payload['apikey'] = self.apikey
        payload['client'] = client_library
        r = requests.post(self.apiendpoint + "vault/" + action, data=payload)
        r.raise_for_status()
        result = r.json()

        if not self.throw_error:
            return result

        if result.get('error'):
            raise APIError(result['error'])
        else:
            return result


class AMLAPI:
    """
    Initialize AML API with an API key, and optional region (US, EU)
    AML API allows you to monitor politically exposed persons (PEPs), and discover person or organization on under sanctions from worldwide governments.
    ID Analyzer AML solutions allows you to check for comprehensive customer due diligence and Anti Money Laundering (AML) and Know Your Customer (KYC) program.

    :param apikey: You API key
    :param region: API Region US/EU, defaults to US
    :raises ValueError: Invalid input argument
    """
    def __init__(self, apikey, region="US"):
        if not apikey:
            raise ValueError("Please provide an API key")
        if not region:
            raise ValueError("Please set an API region (US, EU)")
        self.apikey = apikey
        self.throw_error = False
        self.AMLDatabases = ""
        self.AMLEntityType = ""
        if region.upper() == 'EU':
            self.apiendpoint = "https://api-eu.idanalyzer.com/aml"
        elif region.upper() == "US":
            self.apiendpoint = "https://api.idanalyzer.com/aml"
        else:
            self.apiendpoint = region

    def throw_api_exception(self, throw_exception=False):
        """
        Whether an exception should be thrown if API response contains an error message

        :param throw_exception: Throw exception upon API error, defaults to false
        """
        self.throw_error = throw_exception is True

    def set_aml_database(self, databases="au_dfat,ca_dfatd,ch_seco,eu_fsf,fr_tresor_gels_avoir,gb_hmt,ua_sfms,un_sc,us_ofac,eu_cor,eu_meps,global_politicians,interpol_red"):
        """
        Specify the source databases to perform AML search, if left blank, all source databases will be checked. 
        Separate each database code with comma, for example: un_sc,us_ofac. For full list of source databases and corresponding code visit AML API Overview.
        
        :param databases: Database codes separated by comma
        """
        self.AMLDatabases = databases

    def set_entity_type(self, entity_type=""):
        """
        Return only entities with specified entity type, leave blank to return both person and legal entity.
        
        :param entity_type: 'person' or 'legalentity'
        :raises ValueError: Invalid input argument
        """
        if entity_type != "person" and entity_type != "legalentity" and entity_type != "":
            raise ValueError("Entity Type should be either empty, 'person' or 'legalentity'")

        self.AMLEntityType = entity_type

    def search_by_name(self, name="", country="", dob=""):
        """
        Search AML Database using a person or company's name or alias

        :param name: Name or alias to search AML Database
        :param country: ISO 2 Country Code
        :param dob: Date of birth in YYYY-MM-DD or YYYY-MM or YYYY format
        :return AML match results
        :rtype dict
        :raises ValueError: Invalid input argument
        :raises APIError: API Error
        """
        if len(name) < 3:
            raise ValueError("Name should contain at least 3 characters.")

        return self.__api({"name": name, "country": country, "dob": dob})

    def search_by_id_number(self, document_number="", country="", dob=""):
        """
        Search AML Database using a document number (Passport, ID Card or any identification documents)

        :param document_number: Document ID Number to perform search
        :param country: ISO 2 Country Code
        :param dob: Date of birth in YYYY-MM-DD or YYYY-MM or YYYY format
        :return AML match results
        :rtype dict
        :raises ValueError: Invalid input argument
        :raises APIError: API Error
        """
        if len(document_number) < 5:
            raise ValueError("Document number should contain at least 5 characters.")

        return self.__api({"documentnumber": document_number, "country": country, "dob": dob})

    def __api(self, payload=None):
        if not payload:
            payload = {}
        payload['database'] = self.AMLDatabases
        payload['entity'] = self.AMLEntityType
        payload['apikey'] = self.apikey
        payload['client'] = client_library
        r = requests.post(self.apiendpoint, data=payload)
        r.raise_for_status()
        result = r.json()

        if not self.throw_error:
            return result

        if result.get('error'):
            raise APIError(result['error'])
        else:
            return result
