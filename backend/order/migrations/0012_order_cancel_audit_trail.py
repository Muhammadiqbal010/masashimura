from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0011_order_promo_order_promo_discount_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='cancel_reason',
            field=models.CharField(
                blank=True,
                choices=[
                    ('wrong_input', 'Salah input'),
                    ('customer_cancel', 'Pelanggan batal'),
                    ('out_of_stock', 'Stok habis'),
                    ('other', 'Lainnya'),
                ],
                help_text='Alasan order dibatalkan',
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='cancel_note',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Catatan tambahan opsional saat membatalkan order',
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='cancelled_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='cancelled_by',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Nama kasir/admin yang membatalkan order',
                max_length=100,
            ),
        ),
    ]