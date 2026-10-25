from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0031_order_service_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='midtrans_qr_url',
            field=models.TextField(blank=True, default='', editable=False),
        ),
        migrations.AddField(
            model_name='order',
            name='midtrans_qr_expires_at',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
    ]
