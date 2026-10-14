from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0028_customerloyalty_pin'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdeletionlog',
            name='loyalty_points_refunded',
            field=models.IntegerField(
                default=0,
                help_text='Poin tukar reward yang DIKEMBALIKAN ke customer karena order ini dihapus (poin yang dulu terpotong saat order dibuat)',
            ),
        ),
    ]