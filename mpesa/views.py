from django.shortcuts import render
from rest_framework.views import APIView

from mpesa.mpesaGateway import MpesaGateWay
from .serializers import MpesaCheckoutSerializer
import json

gateway = MpesaGateWay()


# initiate skt push view
class MpesaCheckout(APIView):
    # todo: i dont think the user should provide any credentials....fetch them from the user object
    
    serializer = MpesaCheckoutSerializer

    def post(self, request):
        serializer = self.serializer(data=request.data)
        print(serializer.initial_data)
        if serializer.is_valid():
            print(serializer.data)
            res = gateway.stk_push_request(serializer.validated_data)


# mpesa callback view
class MpesaCallBack(APIView):
    serializer = MpesaCheckoutSerializer

    # check the user is authenticated
    def post(self, request):
        data = request.body
        return gateway.callback_handler(json.loads(data))