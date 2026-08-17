import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0013_order_payment_status_void'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                blank=True,
                choices=[
                    ('cash', 'Cash'),
                    ('qris', 'QRIS'),
                    ('qris_manual', 'QRIS Manual'),
                    ('gateway', 'Payment Gateway'),
                    ('mixed', 'Campuran (Split Bayar)'),
                ],
                max_length=15,
                null=True,
            ),
        ),
        migrations.CreateModel(
            name='OrderPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method', models.CharField(
                    choices=[
                        ('cash', 'Cash'),
                        ('qris', 'QRIS'),
                        ('qris_manual', 'QRIS Manual'),
                        ('gateway', 'Payment Gateway'),
                        ('mixed', 'Campuran (Split Bayar)'),
                    ],
                    max_length=15,
                )),
                ('amount', models.DecimalField(decimal_places=0, max_digits=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='order.order')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]