from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .ml.predict import ModelNotTrainedError, forecast
from .ml.train import train_and_select_best


class RevenuePredictionView(APIView):
    """
    GET /api/prediction/revenue/?days=30
    Balikin prediksi revenue harian untuk N hari ke depan + total estimasi,
    plus info model apa yang dipakai dan seberapa akurat dia pas dievaluasi.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            n_days = int(request.query_params.get('days', 30))
        except (TypeError, ValueError):
            n_days = 30
        n_days = max(1, min(n_days, 90))  # guard biar gak diminta forecast setahun

        try:
            history_days = int(request.query_params.get('history_days', 30))
        except (TypeError, ValueError):
            history_days = 30
        history_days = max(1, min(history_days, 180))

        try:
            result = forecast(n_days=n_days, history_days=history_days)
        except ModelNotTrainedError as e:
            return Response({'error': str(e), 'model_trained': False}, status=409)

        return Response(result)


class TrainRevenuePredictionView(APIView):
    """
    POST /api/prediction/revenue/train/
    Trigger (re)training manual dari dashboard — misal habis ada banyak
    order baru dan mau update modelnya tanpa nunggu jadwal otomatis.
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        result = train_and_select_best()
        if not result['success']:
            return Response({'error': result['reason']}, status=422)
        return Response(result)
