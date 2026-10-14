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


class RevenuePredictionSnapshot(models.Model):
    """
    Prediksi omzet harian yang SUDAH PERNAH ditampilkan, disimpan supaya nanti
    bisa dibandingkan dengan omzet sebenarnya (Prediksi vs Realisasi).

    Tidak ada cron di backend serverless, jadi snapshot disimpan setiap kali
    prediksi dihitung (dashboard dibuka, atau briefing harian dimuat).
    Satu baris per (target_date, made_on): dibuka berkali-kali di hari yang sama
    hanya menimpa baris hari itu. Hari libur rutin tidak disimpan (nilainya pasti 0).
    """
    id = models.BigAutoField(primary_key=True)
    target_date = models.DateField(db_index=True, help_text='Tanggal yang diprediksi')
    made_on = models.DateField(help_text='Tanggal (WIB) prediksi ini dibuat')
    predicted_revenue = models.FloatField()
    lower_bound = models.FloatField(default=0)
    upper_bound = models.FloatField(default=0)
    method = models.CharField(max_length=20, blank=True, default='')
    confidence = models.CharField(max_length=10, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Revenue Prediction Snapshot'
        verbose_name_plural = 'Revenue Prediction Snapshots'
        ordering = ['target_date', '-made_on']
        constraints = [
            models.UniqueConstraint(fields=['target_date', 'made_on'], name='uniq_snapshot_target_made_on'),
        ]

    def __str__(self):
        return f'{self.target_date} (dibuat {self.made_on}): {self.predicted_revenue:,.0f}'
