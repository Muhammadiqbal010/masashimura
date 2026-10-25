from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0012_menubundle_menubundleitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='menu',
            name='created_at',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
    ]
