import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mpesa_project.settings")

app = Celery("mpesa_project")

# Load settings from Django settings, using `CELERY_` namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from installed apps
app.autodiscover_tasks()

# Schedule reconciliation every 5 minutes
app.conf.beat_schedule = {
    "reconcile-transactions-every-5-min": {
        "task": "payments.tasks.reconcile_transactions",
        "schedule": crontab(minute="*/5"),
    },
}
