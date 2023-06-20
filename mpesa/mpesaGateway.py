import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import environ
import time
import base64
from .models import Transactional
from rest_framework.response import Response

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
                if (
                    gateway.access_token_expiration
                    and time.time() > gateway.access_token_expiration
                ):
                    token = gateway.get_access_token()
                    gateway.access_token = token
                return decorator(gateway, *args, **kwargs)

            return wrapper

    # get access token which will be used from auth when paying
    def get_access_token(self):
        try:
            res = requests.get(
                self.access_token_url,
                auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret),
            )
        except Exception as e:
            raise e
        else:
            accessToken = res.json()["accessToken"]
            self.headers = {"Authorization": f"Bearer {accessToken}"}
            return accessToken

    # password to be used in request to be sent to mpesa
    def generatePassword(shortCode, passkey, timestamp):
        return base64.b64encode(
            f"{shortCode}{passkey}{timestamp}".encode("ascii")
        ).decode("uft-8")

    def get_stk_data(
        self, payload
    ):  # todo: we cannot manually enter the amount,why we need payload
        # todo: we need to customize this payload
        return {
            "BusinessShortCode": "174379",
            "Password": self.generatePassword(
                self.shortcode, self.passKey, self.access_token_expiration
            ),
            "Timestamp": datetime.now(),
            "TransactionType": "CustomerPayBillOnline",  # todo: i dont line this,automate it as value can be another value :)
            "Amount": payload.amount,
            "PartyA": payload.phone_num,
            "PartyB": "174379",
            "PhoneNumber": payload.phone_num,
            "CallBackURL": env("mpesa_callback_url"),
            "AccountReference": "Test",
            "TransactionDesc": "Test",
        }

    @Decorators.refreshToken
    def stk_push_request(self, payload):
        stk_data = self.get_stk_data(payload)
        res = requests.post(
            env("mpesa_checkout_url"), json=stk_data, timeout=env("mpesa_timeout")
        )
        res_data = res.json()

        transaction = Transactional()
        transaction.merchant_request_id = res["MerchantRequestID"]
        transaction.checkout_request_id = res["CheckoutRequestID"]
        transaction.result_code = res["ResponseCode"]
        transaction.response_desc = res["ResponseDescription"]

        # persist the data to a database
        transaction.save()

    def get_mpesa_status(data):
        # todo: there are two objects we can get from callback,a success one and one which can fail...based way to handle that??
        try:
            status = data["Body"["stkCallback"]["ResultCode"]]  # the value is usually 0
        except Exception as e:
            status = 1  # this is when are exception occurs
        return status

    def get_transaction_object(data):
        return Transactional.objects.get_or_create(
            checkout_request_id=data["Body"["stkCallback"]["CheckoutRequestID"]]
        )

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

    def callback_handler(self, data):
        # this data is from daraja after stk push
        status_code = self.get_mpesa_status(data)
        transaction: Transactional = self.get_transaction_object(data)

        if status_code == 0:
            self.handle_successful_pay(data, transaction)
        else:
            transaction.response_code = 1
        transaction.response_code = status_code
        transaction.save()
        return Response({"status": "ok", "code": 0}, status=200)
