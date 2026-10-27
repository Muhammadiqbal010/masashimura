# Daftar blokir anti-scam (tabel baru) + dua jenis event baru di riwayat order.
# Aman dijalankan sebelum kode baru di-deploy: hanya menambah tabel dan mengubah pilihan (choices) kolom.

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0036_order_client_trace'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlockedContact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('phone', 'Nomor WA'), ('ip', 'IP')], max_length=5)),
                ('value', models.CharField(db_index=True, max_length=64)),
                ('is_active', models.BooleanField(default=True)),
                ('reason', models.CharField(blank=True, default='', max_length=255)),
                ('blocked_by', models.CharField(blank=True, default='', max_length=100)),
                ('order_number', models.CharField(blank=True, default='', max_length=40)),
                ('blocked_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('unblocked_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-blocked_at'],
                'unique_together': {('kind', 'value')},
            },
        ),
        migrations.AlterField(
            model_name='orderevent',
            name='action',
            field=models.CharField(choices=[('accepted', 'Diterima'), ('paid', 'Dilunasi'), ('cancelled', 'Dibatalkan'), ('auto_cancelled', 'Dibatalkan otomatis'), ('ready', 'Siap diambil'), ('unready', 'Tanda siap dicabut'), ('reminded', 'Pengingat dikirim'), ('refunded', 'Refund diserahkan'), ('blocked', 'Nomor diblokir'), ('unblocked', 'Blokir dibuka')], max_length=20),
        ),
    ]
