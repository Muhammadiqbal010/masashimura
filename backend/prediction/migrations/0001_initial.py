from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='PredictionModelState',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(default='revenue', max_length=50, unique=True)),
                ('metadata', models.JSONField(default=dict)),
                ('model_blob', models.BinaryField(blank=True, null=True)),
                ('trained_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Prediction Model State',
                'verbose_name_plural': 'Prediction Model States',
            },
        ),
    ]