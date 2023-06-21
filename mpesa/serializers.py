from rest_framework import serializers
from .models import Transactional


class MpesaCheckoutSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transactional
        fields = ("phoneNo", "amount", "accountReference", "transactionDesc")


class TransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transactional
        fields = '__all__'