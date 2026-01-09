"""
URL configuration for mpesa_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

from payments.views import admin_retry_callback


def index(request):
    return HttpResponse("<h1>M-Pesa Payments API</h1><p>Use /payments/stk-push/ to initiate STK push or /admin/ to access admin.</p>")


urlpatterns = [
    path('', index, name='index'),
    # Admin retry hook for manual retry button (must come before the admin site include)
    path('admin/payments/paymenttransaction/<uuid:transaction_id>/retry/', admin_retry_callback, name='admin_retry_callback'),
    path('admin/', admin.site.urls),
    path('payments/', include('payments.urls')),
]
