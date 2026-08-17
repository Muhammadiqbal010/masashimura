from django.urls import path

from .views import RevenuePredictionView, TrainRevenuePredictionView

urlpatterns = [
    path('prediction/revenue/', RevenuePredictionView.as_view(), name='revenue-prediction'),
    path('prediction/revenue/train/', TrainRevenuePredictionView.as_view(), name='revenue-prediction-train'),
]
