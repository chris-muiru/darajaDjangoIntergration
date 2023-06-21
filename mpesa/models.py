from django.db import models
import uuid

STATUS = ((0, "Pending"), (1, "Complete"), (2, "Failed"))


class Transactional(models.Model):
    # transaction_num = models.CharField(default=uuid.uuid4, max_length=50, unique=True)
    merchant_request_id = models.CharField(max_length=200)
    checkout_request_id = models.CharField(max_length=200)
    response_code = models.CharField(max_length=2)
    mpesa_receipt_num = models.CharField(max_length=200)
    amount = models.CharField(max_length=20)
    phone_num = models.CharField(max_length=200)
    payment_status = models.CharField(max_length=15, choices=STATUS, default=1)
    ip_addr = models.CharField(max_length=200, blank=True, null=True)
    transaction_response_code = models.CharField(max_length=200)
    transaction_date = models.DateTimeField(auto_now_add=True)
    result_desc = models.CharField(max_length=200)

    # def __unicode__(self):
    #     return f"{self.transaction_num}"
