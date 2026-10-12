from django.db import models


class PredictionModelState(models.Model):
    """
    State model prediksi revenue (satu baris per `name`).

    Disimpan di database, BUKAN file, karena filesystem serverless (Vercel)
    read-only: file hasil training tidak akan pernah tersimpan di sana.
    - metadata   : hasil evaluasi, metode terpilih, fitur, dll (JSON)
    - model_blob : model scikit-learn hasil joblib.dump (kosong kalau baseline menang)
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True, default='revenue')
    metadata = models.JSONField(default=dict)
    model_blob = models.BinaryField(null=True, blank=True)
    trained_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Prediction Model State'
        verbose_name_plural = 'Prediction Model States'

    def __str__(self):
        return f'{self.name} ({self.metadata.get("best_model", "-")})'