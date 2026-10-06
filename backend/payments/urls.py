from django.urls import path
from .views import CreatePaymentView, MidtransWebhookView, PaymentStatusView

urlpatterns = [
    path("create/<str:order_number>/", CreatePaymentView.as_view()),
    path("webhook/", MidtransWebhookView.as_view()),
    path("status/<str:order_number>/", PaymentStatusView.as_view()),
]