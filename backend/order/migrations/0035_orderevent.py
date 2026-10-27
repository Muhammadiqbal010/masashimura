import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0034_order_awaiting_confirmation'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('accepted', 'Diterima'), ('paid', 'Dilunasi'), ('cancelled', 'Dibatalkan'), ('auto_cancelled', 'Dibatalkan otomatis'), ('ready', 'Siap diambil'), ('unready', 'Tanda siap dicabut'), ('reminded', 'Pengingat dikirim'), ('refunded', 'Refund diserahkan')], max_length=20)),
                ('actor', models.CharField(blank=True, default='', max_length=100)),
                ('channel', models.CharField(choices=[('staff', 'Aplikasi admin'), ('telegram', 'Telegram'), ('system', 'Sistem')], default='staff', max_length=10)),
                ('note', models.CharField(blank=True, default='', max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='order.order')),
            ],
            options={
                'ordering': ['created_at', 'id'],
                'indexes': [
                    models.Index(fields=['order', 'action'], name='orderevent_order_action_idx'),
                    models.Index(fields=['created_at'], name='orderevent_created_idx'),
                ],
            },
        ),
    ]
