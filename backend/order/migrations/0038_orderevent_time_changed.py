# Jenis event baru "time_changed" (tanggal/jam order diubah dari Active Orders).
# Aman dijalankan sebelum kode baru di-deploy: hanya mengubah pilihan (choices) kolom.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0037_blockedcontact'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderevent',
            name='action',
            field=models.CharField(choices=[('accepted', 'Diterima'), ('paid', 'Dilunasi'), ('cancelled', 'Dibatalkan'), ('auto_cancelled', 'Dibatalkan otomatis'), ('ready', 'Siap diambil'), ('unready', 'Tanda siap dicabut'), ('reminded', 'Pengingat dikirim'), ('refunded', 'Refund diserahkan'), ('blocked', 'Nomor diblokir'), ('unblocked', 'Blokir dibuka'), ('time_changed', 'Waktu order diubah')], max_length=20),
        ),
    ]
