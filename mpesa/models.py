from django.db import models
import uuid

STATUS = ((0, "Pending"), (1, 'Complete'), (2, "Failed"))


class Transactional(models.Model):
    transaction_num = models.CharField(default=uuid.uuid4,
                                       max_length=50,
                                       unique=True)
    phone_num = models.CharField(null=False, blank=False)
    checkout_request_id = models.CharField(max_length=200)
    account_reference = models.CharField(max_length=40, blank=True)
    transaction_desc = models.TextField()
    mpesa_receipt_num = models.CharField()
    created_on = models.DateField(auto_now_add=True)
    party_A = models.CharField()
    party_B = models.CharField()
    amount = models.CharField(max_length=10)
    payment_status = models.CharField(max_length=15, choices=STATUS, default=1)

    ip = models.CharField(max_length=200, blank=True, null=True)

    def __unicode__(self):
        return f"{self.transaction_num}"
