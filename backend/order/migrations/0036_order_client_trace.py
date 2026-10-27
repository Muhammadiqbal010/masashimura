# Jejak asal pemesan web (IP + lokasi perkiraan + perangkat) untuk melacak scam.
# Dua kolom baru yang boleh kosong, jadi aman dijalankan sebelum kode baru di-deploy
# (kode lama tetap jalan dengan kolom ini).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0035_orderevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='client_ip',
            field=models.GenericIPAddressField(blank=True, db_index=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='client_info',
            field=models.JSONField(blank=True, default=dict, editable=False),
        ),
    ]
