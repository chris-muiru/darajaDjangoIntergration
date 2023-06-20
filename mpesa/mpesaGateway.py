import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import environ
import time
import base64
from .models import Transactional

env = environ.Env()


class MpesaGateWay:
    shortcode = None
    consumer_key = None
    consumer_secret = None
    access_token_url = None
    access_token = None
    access_token_expiration = None
    access_token_url = None

    def __init__(self):
        self.shortcode = env("shortcode")
        self.consumer_key = env("consumer_key")
        self.consumer_secret = env("consumer_secret")
        self.access_token_url = env("access_token_url")

        try:
            self.access_token = self.get_access_token()
            if self.access_token == None:
                raise Exception("an error occured")
        except Exception as e:
            raise e
        else:
            self.access_token_expiration = time.time() + 3400

    # refresh token which expires after 3599s
    class Decorators:

        @staticmethod
        def refreshToken(decorator):

            def wrapper(gateway: MpesaGateWay, *args, **kwargs):
                if (gateway.access_token_expiration
                        and time.time() > gateway.access_token_expiration):
                    token = gateway.get_access_token()
                    gateway.access_token = token
                return decorator(gateway, *args, **kwargs)

            return wrapper

    # get access token which will be used from auth when paying
    def get_access_token(self):
        try:
            res = requests.get(self.access_token_url,
                               auth=HTTPBasicAuth(self.consumer_key,
                                                  self.consumer_secret))
        except Exception as e:
            raise e
        else:
            accessToken = res.json()["accessToken"]
            self.headers = {"Authorization": f"Bearer {accessToken}"}
            return accessToken

    # password to be used in request to be sent to mpesa
    def generatePassword(shortCode, passkey, timestamp):
        return base64.b64encode(
            f"{shortCode}{passkey}{timestamp}".encode("ascii")).decode("uft-8")

    def stk_push_request(self, payload):
        # its functionality should be just receiving thw payload and posting it to saf

        res = requests.post(env("checkout_url"),
                            json=payload,
                            timeout=env("mpesaTimeout"))
        res_data = res.json()

        # persist the data to a database

    def get_mpesa_status(data):
        # todo: there are two objects we can get from callback,a success one and one which can fail...baset way to handle that??
        try:
            status = data["Body"["stkCallback"]
                          ["ResultCode"]]  # the value is usually 0
        except Exception as e:
            status = 1  # this is when are exception occurs
        return status

    def get_transaction_object(data):
        return Transactional.objects.get_or_create(checkout_request_id=data[
            "Body"["stkCallback"]["CheckoutRequestID"]])

    def handle_successful_pay(data, transaction: Transactional):
        itemJson = data["Body"]["stkCallback"]["CallbackMetadata"["Item"]]

        for obj in itemJson:
            if obj["Name"] == "Amount":
                amount = obj["Value"]
            elif obj["Name"] == "MpesaReceiptNumber":
                receipt_num = obj["Value"]
            elif obj["Name"] == "PhoneNumber":
                phone_num = obj["Value"]

        transaction.amount = amount
        transaction.phone_num = phone_num
        transaction.mpesa_receipt_num = receipt_num
        transaction.payment_status = 2  # todo: how will you handle status??
