from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0026_storesettings_monthly_revenue_target'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='bundle_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
