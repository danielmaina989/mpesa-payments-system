<!-- Badges -->
![CI](https://img.shields.io/badge/status-stable-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-4.2-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

# M-Pesa Payments & Reconciliation System

A **production-grade M-Pesa STK Push payment system** built with Django, Django REST Framework, Celery, and Redis.

This project demonstrates how to build **reliable, auditable, and scalable payment infrastructure** suitable for real businesses in Kenya and beyond.

---

## 🚀 Features

### Core Payment Flow
- STK Push initiation
- Secure webhook (callback) handling
- Transaction lifecycle management:

```
INITIATED → PENDING → SUCCESS / FAILED
```

- Idempotent callback processing (safe against duplicate M-Pesa retries)

### Reliability & Scale
- Asynchronous callback processing using Celery + Redis
- Background task retries with exponential backoff
- Graceful handling of malformed or unexpected webhook payloads

### Admin & Auditability
- Django Admin dashboard for transactions
- Transaction filtering by status, date, and phone number
- Full audit trail of payment state changes

### Developer Experience
- Environment-based configuration
- Decimal-safe money handling
- Clean separation of concerns (views, tasks, models)

---

## 🧠 Architecture Overview

```
┌──────────────┐
│   Client UI  │
└───────┬──────┘
        │
        ▼
  Django REST API
        │
        ▼
 M-Pesa STK Push
        │
        ▼
 Callback Endpoint
        │
        ▼
   Celery Queue
        │
        ▼
   Redis Broker
        │
        ▼
 PostgreSQL / DB
```

---

## 🔄 Payment Flow Explained

1. Client initiates payment via `/payments/stk-push/`
2. System sends STK Push request to M-Pesa
3. Transaction is saved as `PENDING`
4. M-Pesa sends callback to `/payments/callback/`
5. Callback is queued to Celery for async processing
6. Transaction is updated to `SUCCESS` or `FAILED`
7. Duplicate callbacks are safely ignored

---

## ⚠️ Failure Scenarios Handled

- Duplicate callbacks from M-Pesa
- Network retries and timeouts
- Missing or malformed callback payloads
- Worker restarts without data corruption

---

## 🔐 Security Considerations

- Credentials loaded from environment variables
- No secrets committed to version control
- CSRF exempt webhook endpoint (required for M-Pesa)
- Idempotent processing prevents double charging

---

## 🛠 Tech Stack

- Python 3.12
- Django
- Django REST Framework
- Celery
- Redis
- PostgreSQL (recommended for production)

---

## ⚙️ Setup Instructions

### 1️⃣ Clone Repository
```bash
git clone https://github.com/your-username/mpesa-payments-system.git
cd mpesa-payments-system
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv mpesa_env
source mpesa_env/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Environment Variables

Create `.env` file based on `.env.example`

```env
MPESA_CONSUMER_KEY=
MPESA_CONSUMER_SECRET=
MPESA_SHORTCODE=
MPESA_PASSKEY=
MPESA_CALLBACK_URL=
MPESA_ENV=sandbox

CELERY_BROKER_URL=redis://localhost:6379/0
```

### 5️⃣ Run Services

```bash
redis-server
python manage.py migrate
python manage.py runserver
celery -A mpesa_project worker -l info
```

---

## 📈 Roadmap

* [ ] Automated reconciliation engine
* [ ] CSV export for accountants
* [ ] Webhook replay endpoint
* [ ] Subscription billing support
* [ ] Metrics & reporting API

---

## 💼 Use Cases

* SME payment collection
* Subscription-based services
* Fintech MVPs
* Internal billing systems

---

## 📄 License

MIT License
