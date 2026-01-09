"""
Implement M-Pesa STK Push initiation and webhook callback handling.
"""

import base64
import datetime
import json
import logging
from decimal import Decimal

import requests
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PaymentTransaction
from .tasks import process_stk_callback

logger = logging.getLogger(__name__)


def _mpesa_base_urls():
    """Return base URLs depending on MPESA_ENV (sandbox or production)."""
    if getattr(settings, "MPESA_ENV", "sandbox").lower() == "production":
        return {
            "oauth": "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
            "stk_push": "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        }
    # sandbox
    return {
        "oauth": "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
        "stk_push": "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
    }


def _get_access_token():
    """Obtain an OAuth access token from Safaricom/M-Pesa."""
    urls = _mpesa_base_urls()
    resp = requests.get(urls["oauth"], auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET), timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("access_token")


class STKPushView(APIView):
    """
    POST: { "phone_number": "2547XXXXXXXX", "amount": "100" }
    Initiates M-Pesa STK Push and creates/updates a PaymentTransaction.
    """

    def post(self, request):
        phone = request.data.get("phone_number")
        amount = request.data.get("amount")

        if not phone or amount is None:
            return Response({"detail": "phone_number and amount are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(str(amount))
        except Exception:
            return Response({"detail": "invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

        tx = PaymentTransaction.objects.create(phone_number=phone, amount=amount)

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode("utf-8")

        callback_url = getattr(settings, "MPESA_CALLBACK_URL", "")
        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),  # M-Pesa expects integer amounts
            "PartyA": phone,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": "Payment",
            "TransactionDesc": "Payment",
        }

        try:
            access_token = _get_access_token()
        except requests.RequestException as e:
            logger.exception("Failed to get access token: %s", e)
            return Response({"detail": "failed to obtain access token"}, status=status.HTTP_502_BAD_GATEWAY)

        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            urls = _mpesa_base_urls()
            resp = requests.post(urls["stk_push"], json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            response_data = resp.json()
        except requests.RequestException as e:
            logger.exception("STK push request failed: %s", e)
            tx.status = "FAILED"
            tx.save()
            return Response({"detail": "stk push failed"}, status=status.HTTP_502_BAD_GATEWAY)

        # update transaction if push accepted
        if response_data.get("ResponseCode") == "0":
            tx.mpesa_checkout_request_id = response_data.get("CheckoutRequestID")
            tx.status = "PENDING"
            tx.save()
        else:
            tx.status = "FAILED"
            tx.save()

        return Response(response_data, status=status.HTTP_200_OK)


RESULT_CODE_MAPPING = {
    0: "SUCCESS",
    1: "FAILED",
    2: "CANCELLED",
    1032: "TIMEOUT",
}


@method_decorator(csrf_exempt, name="dispatch")
class STKCallbackView(APIView):
    """
    M-Pesa webhook endpoint to receive STK callback.
    Expects raw JSON body as M-Pesa posts.
    This implementation is resilient: it never returns 4xx to M-Pesa and safely handles
    unexpected/malformed payloads. It logs useful warnings for later reconciliation.
    """
    authentication_classes = []  # callbacks come from M-Pesa; keep unauthenticated
    permission_classes = []

    def post(self, request):
        try:
            # 1. Parse payload safely
            data = json.loads(request.body.decode("utf-8"))
            callback = data.get("Body", {}).get("stkCallback", {})

            checkout_id = callback.get("CheckoutRequestID")
            result_code = callback.get("ResultCode")
            result_desc = callback.get("ResultDesc")
            callback_amount = None

            # Extract amount if available (from CallbackMetadata)
            items = callback.get("CallbackMetadata", {}).get("Item", [])
            for item in items:
                if item.get("Name") == "Amount":
                    try:
                        callback_amount = float(item.get("Value", 0))
                    except Exception:
                        callback_amount = None

            if not checkout_id:
                logger.warning("Callback ignored: no CheckoutRequestID")
                return Response({"status": "ignored"}, status=200)

            # 2. Retrieve transaction safely
            tx = PaymentTransaction.objects.filter(
                mpesa_checkout_request_id=checkout_id
            ).first()
            if not tx:
                logger.warning("Transaction not found for ID: %s", checkout_id)
                return Response({"status": "transaction not found"}, status=200)

            # 3. Idempotency / duplicate callback protection
            if tx.status in ["SUCCESS", "FAILED"]:
                logger.info(
                    "Duplicate callback received for %s. Current status: %s",
                    checkout_id, tx.status
                )
                return Response({"status": "already processed"}, status=200)

            # 4. Map result code
            try:
                result_code_int = int(result_code)
            except Exception:
                result_code_int = None

            status_str = RESULT_CODE_MAPPING.get(result_code_int, "FAILED")

            # 5. Amount verification
            if callback_amount is not None:
                try:
                    expected_amount = float(tx.amount)
                    if expected_amount != callback_amount:
                        logger.warning(
                            "Amount mismatch for %s: expected %.2f, callback %.2f",
                            checkout_id, expected_amount, callback_amount
                        )
                        tx.status = "FAILED"
                        tx.save()
                        return Response({"status": "error", "detail": "amount mismatch"}, status=200)
                except Exception:
                    logger.exception("Error verifying amount for %s", checkout_id)
                    tx.status = "FAILED"
                    tx.save()
                    return Response({"status": "error", "detail": "amount verification error"}, status=200)

            # 6. Update transaction
            tx.status = status_str
            tx.save()

            # Persist callback log if model exists
            try:
                from .models import CallbackLog
                CallbackLog.objects.create(
                    checkout_request_id=checkout_id,
                    payload=data,
                    processed=True,
                    processing_status=status_str,
                    details=result_desc or "",
                )
            except Exception:
                logger.exception("Failed to persist callback log for %s", checkout_id)

            logger.info(
                "Callback processed: %s -> %s, desc: %s",
                checkout_id, status_str, result_desc
            )

            # Enqueue asynchronous processing
            process_stk_callback.delay(data)

            return Response({"status": "processed"}, status=200)

        except Exception as e:
            logger.exception("Callback processing error: %s", e)
            # Try to persist failed callback for later inspection
            try:
                from .models import CallbackLog
                CallbackLog.objects.create(
                    checkout_request_id=(callback.get("CheckoutRequestID") if isinstance(callback, dict) else None),
                    payload=(data if 'data' in locals() else {}),
                    processed=False,
                    processing_status="error",
                    details=str(e),
                )
            except Exception:
                logger.exception("Failed to persist failed callback")

            return Response({"status": "error", "detail": str(e)}, status=200)


# Replay endpoint for manual reprocessing/reconciliation
class ReplayCallbackView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, checkout_id):
        tx = PaymentTransaction.objects.filter(
            mpesa_checkout_request_id=checkout_id
        ).first()

        if not tx:
            return Response({"error": "Transaction not found"}, status=404)

        payload = {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": checkout_id,
                    "ResultCode": 0
                }
            }
        }

        # enqueue background processing
        process_stk_callback.delay(payload)
        return Response({"status": "replayed"}, status=200)

