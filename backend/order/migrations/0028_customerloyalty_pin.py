from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0027_orderitem_bundle_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='customerloyalty',
            name='pin_hash',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AddField(
            model_name='customerloyalty',
            name='pin_set_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customerloyalty',
            name='pin_failed_attempts',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='customerloyalty',
            name='pin_locked_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
