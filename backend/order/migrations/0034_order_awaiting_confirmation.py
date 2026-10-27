from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0033_order_midtrans_qr_ref'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='awaiting_confirmation',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='order',
            name='accepted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
