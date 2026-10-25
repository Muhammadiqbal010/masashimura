from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0032_order_pos_qris'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='midtrans_qr_ref',
            field=models.CharField(blank=True, default='', editable=False, max_length=60),
        ),
    ]
