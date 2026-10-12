from django.core.management.base import BaseCommand

from prediction.ml.train import train_and_select_best


class Command(BaseCommand):
    help = 'Evaluasi baseline vs Random Forest, pilih yang terbaik, dan simpan hasilnya ke database.'

    def handle(self, *args, **options):
        result = train_and_select_best()

        if not result['success']:
            self.stderr.write(self.style.ERROR(result['reason']))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Training selesai. Model terpilih: {result['best_model']} "
            f"(dilatih dari {result['n_training_days']} hari data)"
        ))
        self.stdout.write(f"  Alasan: {result['selection_reason']}")
        for name, metrics in result['metrics'].items():
            mape = f"{metrics['mape']:.1f}%" if metrics.get('mape') is not None else '-'
            self.stdout.write(
                f"  - {name}: MAE=Rp{metrics['mae']:,.0f}  "
                f"RMSE=Rp{metrics['rmse']:,.0f}  MAPE={mape}"
            )

        if result.get('persisted', True):
            self.stdout.write(self.style.SUCCESS('Hasil tersimpan ke database.'))
        else:
            self.stderr.write(self.style.ERROR(result.get('persist_error') or 'Hasil tidak tersimpan.'))