import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0016_loyaltysettings_rupiah_per_point'),
    ]

    operations = [
        # ── Bersihin sistem diskon tier lama dari LoyaltySettings ──
        migrations.RemoveField(
            model_name='loyaltysettings',
            name='min_orders',
        ),
        migrations.RemoveField(
            model_name='loyaltysettings',
            name='min_spending',
        ),
        migrations.RemoveField(
            model_name='loyaltysettings',
            name='period_days',
        ),
        migrations.RemoveField(
            model_name='loyaltysettings',
            name='discount_percentage',
        ),
        migrations.AddField(
            model_name='loyaltysettings',
            name='points_expiry_months',
            field=models.PositiveSmallIntegerField(
                choices=[
                    (0, 'Nonaktif (poin tidak pernah hangus)'),
                    (3, '3 bulan'),
                    (6, '6 bulan'),
                    (12, '12 bulan'),
                ],
                default=0,
                help_text='Poin hangus kalau customer ngga order selama sekian bulan. 0 = nonaktif.',
            ),
        ),

        # ── Bersihin override diskon manual per-customer ──
        migrations.RemoveField(
            model_name='customerloyalty',
            name='special_discount_percentage',
        ),
        migrations.AddField(
            model_name='customerloyalty',
            name='last_order_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customerloyalty',
            name='total_orders',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Statistik lifetime, TIDAK ikut hangus (beda dari poin).',
            ),
        ),

        # ── Log audit adjust poin (manual admin & hangus otomatis) ──
        migrations.CreateModel(
            name='PointAdjustment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(help_text='Positif = nambah poin, negatif = mengurangi/menghanguskan poin')),
                ('reason', models.CharField(
                    choices=[('manual', 'Adjust Manual Admin'), ('expired', 'Hangus Otomatis')],
                    default='manual',
                    max_length=20,
                )),
                ('note', models.CharField(blank=True, default='', max_length=255)),
                ('admin_name', models.CharField(
                    blank=True, default='', max_length=100,
                    help_text="Nama admin yang melakukan adjust, atau 'system' kalau otomatis",
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='adjustments', to='order.customerloyalty')),
            ],
            options={
                'verbose_name': 'Point Adjustment',
                'verbose_name_plural': 'Point Adjustments',
                'ordering': ['-created_at'],
            },
        ),
    ]