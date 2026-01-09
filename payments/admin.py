from django.contrib import admin
from .models import PaymentTransaction, CallbackLog


class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "phone_number", "amount", "status", "mpesa_checkout_request_id", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("phone_number", "mpesa_checkout_request_id")
    readonly_fields = ("created_at", "updated_at")


class CallbackLogAdmin(admin.ModelAdmin):
    list_display = ("id", "checkout_request_id", "received_at", "processed")
    readonly_fields = ("id", "received_at", "payload")
    list_filter = ("processed",)
    search_fields = ("checkout_request_id",)


admin.site.register(PaymentTransaction, PaymentTransactionAdmin)
admin.site.register(CallbackLog, CallbackLogAdmin)
