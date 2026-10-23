from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0029_orderdeletionlog_loyalty_points_refunded'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='ready_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='unavailable_items',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='order',
            name='refund_due',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='order',
            name='refunded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='refunded_by',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='added_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='added_qty',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='order_late_minutes',
            field=models.PositiveSmallIntegerField(
                default=20,
                help_text='Menit sejak order masuk sampai dianggap telat kalau belum siap diambil',
            ),
        ),
    ]
