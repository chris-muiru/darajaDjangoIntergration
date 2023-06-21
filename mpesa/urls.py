from django.urls import path
from .views import MpesaCheckout, MpesaCallBack

urlpatterns = [
    path("checkout/", MpesaCheckout.as_view(), name="mpesa-checkout"),
    path("callback/", MpesaCallBack.as_view(), name="mpesa-callback")
]
