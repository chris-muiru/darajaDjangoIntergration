from rest_framework import serializers
from .models import Transactional


class MpesaCheckoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transactional
        fields = ["phone_num", "amount"]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transactional
        fields = '__all__'
