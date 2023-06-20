from django.shortcuts import render
from rest_framework.views import APIView

from mpesa.mpesaGateway import MpesaGateWay
from .serializers import MpesaCheckoutSerializer
import json

gateway = MpesaGateWay()


# initiate skt push view
class MpesaCheckout(APIView):
    serializer = MpesaCheckoutSerializer

    def post(self, request):
        serializer = self.serializer(data=request.data)
        if serializer.is_valid():
            payload = {"data": serializer.validated_data, "request": request}
            res = gateway.stk_push_request(payload)


# mpesa callback view
class MpesaCallBack(APIView):
    serializer = MpesaCheckoutSerializer

    # check the user is authenticated
    def post(self, request):
        data = request.body
        return gateway.mpesa_callback(json.loads(data))