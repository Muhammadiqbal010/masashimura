from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0030_order_ready_refund_added_items'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='service_type',
            field=models.CharField(
                choices=[('dine_in', 'Makan di Tempat'), ('takeaway', 'Dibungkus')],
                default='dine_in',
                max_length=10,
            ),
        ),
    ]
