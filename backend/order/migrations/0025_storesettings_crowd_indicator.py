from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0024_orderitem_selected_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='storesettings',
            name='crowd_indicator_enabled',
            field=models.BooleanField(
                default=True,
                help_text='False = badge keramaian tidak ditampilkan ke pelanggan',
            ),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='crowd_manual_level',
            field=models.CharField(
                blank=True, default='', max_length=10,
                choices=[('santai', 'Santai'), ('sedang', 'Sedang'), ('ramai', 'Ramai')],
                help_text='Kosong = mode otomatis',
            ),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='crowd_manual_until',
            field=models.DateTimeField(
                blank=True, null=True,
                help_text='Level manual berlaku sampai waktu ini',
            ),
        ),
    ]
