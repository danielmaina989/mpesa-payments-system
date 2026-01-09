from django.db import models
import uuid

# Create your models here.

class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ("INITIATED", "Initiated"),
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=12)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="INITIATED")
    mpesa_checkout_request_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PaymentTransaction {self.id} - {self.status} - {self.phone_number}"

    class Meta:
        ordering = ["-created_at"]


class CallbackLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    received_at = models.DateTimeField(auto_now_add=True)
    checkout_request_id = models.CharField(max_length=50, blank=True, null=True)
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    processing_status = models.CharField(max_length=32, blank=True, null=True)
    details = models.TextField(blank=True)

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"CallbackLog {self.id} - {self.checkout_request_id} - processed={self.processed}"
