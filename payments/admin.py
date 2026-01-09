from django.contrib import admin
from django.utils.html import format_html

from .models import PaymentTransaction, CallbackLog
from .tasks import process_stk_callback


class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "phone_number", "amount", "status", "mpesa_checkout_request_id", "created_at", "retry_button")
    list_filter = ("status", "created_at")
    search_fields = ("phone_number", "mpesa_checkout_request_id")
    readonly_fields = ("created_at", "updated_at")

    def retry_button(self, obj):
        if obj.status == "PENDING":
            return format_html(
                '<a class="button" href="/admin/payments/paymenttransaction/{}/retry/">Retry</a>',
                obj.id,
            )
        return "-"
    retry_button.short_description = "Retry"
    retry_button.allow_tags = True


class CallbackLogAdmin(admin.ModelAdmin):
    list_display = ("id", "checkout_request_id", "received_at", "processed")
    readonly_fields = ("id", "received_at", "payload")
    list_filter = ("processed",)
    search_fields = ("checkout_request_id",)


admin.site.register(PaymentTransaction, PaymentTransactionAdmin)
admin.site.register(CallbackLog, CallbackLogAdmin)
