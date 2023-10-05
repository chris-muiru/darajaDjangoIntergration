import json

import requests
from requests import Request, Session
# todo: why is the token created invalid??
from requests.auth import HTTPBasicAuth
from datetime import datetime
import environ
import time
import base64
from .models import Transactional
from rest_framework.response import Response
import math

env = environ.Env()


def get_mpesa_status(data):
    # todo: there are two objects we can get from callback,a success one and one which can fail...best way to handle that??
    try:
        status = data["Body"["stkCallback"]
                      ["ResultCode"]]  # the value is usually 0
    except Exception as e:
        status = 1  # this is when exception occurs
    return status


def get_transaction_object(data):
    return Transactional.objects.get_or_create(
        checkout_request_id=data["Body"["stkCallback"]["CheckoutRequestID"]])


class MpesaGateWay:
    shortcode = None
    consumer_key = None
    consumer_secret = None
    access_token_url = None
    access_token = None
    access_token_expiration = None
    pass_key = None
    short_code = None
    headers = None

    def __init__(self):
        self.short_code = env("short_code")
        self.consumer_key = env("consumer_key")
        self.consumer_secret = env("consumer_secret")
        self.access_token_url = env("access_token_url")
        # self.pass_key = env("pass_key")

        try:
            self.access_token = self.get_access_token()
            if self.access_token is None:
                raise Exception("an error occured")
        except Exception as e:
            raise e
        else:
            self.access_token_expiration = time.time() + 3400

    # refresh token which expires after 3599s
    class Decorators:

        @staticmethod
        def refreshToken(decorator):

            def wrapper(gateway, *args, **kwargs):
                if (gateway.access_token_expiration
                        and time.time() > gateway.access_token_expiration):
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
            print(res.json())
            accessToken = res.json()["access_token"]
            self.headers = {
                'Authorization': f'Bearer {accessToken}',
                'Content-Type': 'application/json'
            }
            return accessToken

    # password to be used in stk requst payload
    def generatePassword(self, shortCode, passkey, timestamp):
        return base64.b64encode(
            f"{shortCode}{passkey}{timestamp}".encode()).decode("utf-8")

    def get_stk_data(
        self, payload
    ):  # todo: we cannot manually enter the amount,why we need payload
        # todo: we need to customize this payload
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        # todo: i dont like this,automate it as value can be another value :)
        return {
            "BusinessShortCode":
            int(self.short_code),
            "Password":
            self.generatePassword(self.shortcode, self.pass_key,
                                  self.access_token_expiration),
            "Timestamp":
            timestamp,
            "TransactionType":
            "CustomerBuyGoodsOnline",
            "Amount":
            int(payload["amount"]),
            "PartyA":
            int(payload["phone_num"]),
            "PartyB":
            int(self.short_code),
            "PhoneNumber":
            int(payload["phone_num"]),
            "CallBackURL":
            env("mpesa_callback_url"),
            "AccountReference":
            "CompanyXLTD1234V",
            "TransactionDesc":
            "Payment of X"
        }

    # @Decorators.refreshToken
    def stk_push_request(self, payload):
        access_token = self.get_access_token()
        stk_data = self.get_stk_data(payload)
        session = Session()

        res = requests.request(
            "POST",
            env("mpesa_checkout_url"),
            headers={'Authorization': f'Bearer {access_token}'},
            json=stk_data)
        print(res.text.encode('utf8'))

        res_data = res.json()

        transaction = Transactional()
        transaction.merchant_request_id = res["MerchantRequestID"]
        transaction.checkout_request_id = res["CheckoutRequestID"]
        transaction.result_code = res["ResponseCode"]
        transaction.response_desc = res["ResponseDescription"]

        # persist the data to a database
        transaction.save()

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
        status_code = get_mpesa_status(data)
        transaction: Transactional = get_transaction_object(data)

        if status_code == 0:
            self.handle_successful_pay(data, transaction)
        else:
            transaction.response_code = 1
        transaction.response_code = status_code
        transaction.save()
        return Response({"status": "ok", "code": 0}, status=200)
