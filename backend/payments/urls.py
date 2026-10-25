from django.urls import path
from .views import (
    CreatePaymentView, MidtransWebhookView, PaymentStatusView,
    PosQrisCreateView, PosQrisStatusView, PosQrisCancelView,
)

urlpatterns = [
    path("create/<str:order_number>/", CreatePaymentView.as_view()),
    path("webhook/", MidtransWebhookView.as_view()),
    path("status/<str:order_number>/", PaymentStatusView.as_view()),
    path("pos/<str:order_number>/qris/", PosQrisCreateView.as_view()),
    path("pos/<str:order_number>/status/", PosQrisStatusView.as_view()),
    path("pos/<str:order_number>/cancel/", PosQrisCancelView.as_view()),
]