from django.urls import path

from .views import STKPushView, STKCallbackView, ReplayCallbackView

urlpatterns = [
    path('stk-push/', STKPushView.as_view(), name='stk_push'),
    path('callback/', STKCallbackView.as_view(), name='stk_callback'),
    path('callback/replay/<str:checkout_id>/', ReplayCallbackView.as_view(), name='stk_callback_replay'),
]
