from django.core.management.base import BaseCommand

from prediction.ml.train import train_and_select_best


class Command(BaseCommand):
    help = 'Latih model prediksi revenue (Linear Regression vs Random Forest) dan simpan yang terbaik.'

    def handle(self, *args, **options):
        result = train_and_select_best()

        if not result['success']:
            self.stderr.write(self.style.ERROR(result['reason']))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Training selesai. Model terpilih: {result['best_model']} "
            f"(dilatih dari {result['n_training_days']} hari data)"
        ))
        for name, metrics in result['metrics'].items():
            self.stdout.write(
                f"  - {name}: MAE=Rp{metrics['mae']:,.0f}  "
                f"RMSE=Rp{metrics['rmse']:,.0f}  MAPE={metrics['mape']:.1f}%"
            )
