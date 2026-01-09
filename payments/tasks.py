import csv
import json
import logging
from celery import shared_task
from django.utils import timezone
from pathlib import Path

from .models import PaymentTransaction

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={"max_retries": 5})
def process_stk_callback(self, payload):
    """Process an STK callback in the background.

    payload: the raw JSON payload as parsed dict
    """
    callback = payload.get("Body", {}).get("stkCallback", {})
    checkout_id = callback.get("CheckoutRequestID")
    result_code = callback.get("ResultCode")

    if not checkout_id:
        logger.warning("Callback ignored: missing CheckoutRequestID")
        return

    tx = PaymentTransaction.objects.filter(
        mpesa_checkout_request_id=checkout_id
    ).first()

    if not tx:
        logger.warning("Transaction not found: %s", checkout_id)
        return

    # Idempotency
    if tx.status in ["SUCCESS", "FAILED"]:
        logger.info("Duplicate callback ignored: %s", checkout_id)
        return

    try:
        result_code_int = int(result_code)
    except Exception:
        result_code_int = None

    tx.status = "SUCCESS" if result_code_int == 0 else "FAILED"
    # optional audit field can be set here if present
    try:
        if hasattr(tx, "last_event"):
            tx.last_event = f"Processed via Celery: {tx.status}"
    except Exception:
        logger.exception("Failed to set last_event for %s", checkout_id)

    tx.save()

    logger.info("Transaction %s processed → %s", checkout_id, tx.status)


@shared_task
def reconcile_transactions():
    """
    Periodic reconciliation task:
    - Finds PENDING transactions older than X minutes
    - Logs issues
    - Exports a CSV for accounting
    """
    pending_tx = PaymentTransaction.objects.filter(status="PENDING")

    if not pending_tx.exists():
        logger.info("No pending transactions for reconciliation.")
        return

    logger.info("Reconciling %d pending transactions...", pending_tx.count())

    for tx in pending_tx:
        age_minutes = (timezone.now() - tx.created_at).total_seconds() / 60
        if age_minutes > 10:
            logger.warning(
                "Transaction %s has been PENDING for %.1f minutes.", tx.id, age_minutes
            )

    csv_path = Path("reconciliation_report.csv")
    with open(csv_path, "w", newline="") as csvfile:
        fieldnames = ["id", "phone_number", "amount", "status", "mpesa_checkout_request_id", "created_at", "updated_at"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for tx in pending_tx:
            writer.writerow({
                "id": tx.id,
                "phone_number": tx.phone_number,
                "amount": tx.amount,
                "status": tx.status,
                "mpesa_checkout_request_id": tx.mpesa_checkout_request_id,
                "created_at": tx.created_at,
                "updated_at": tx.updated_at,
            })

    logger.info("Reconciliation report written to %s", csv_path)
