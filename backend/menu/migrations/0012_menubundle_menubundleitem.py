import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0011_alter_menu_price'),
    ]

    operations = [
        migrations.CreateModel(
            name='MenuBundle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, default='')),
                ('price', models.DecimalField(decimal_places=0, help_text='Harga paket di POS. Harga web mengikuti aturan markup yang sama dengan menu.', max_digits=10, validators=[django.core.validators.MinValueValidator(1)])),
                ('is_available', models.BooleanField(default=True, help_text='Saklar manual tersedia/habis')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='MenuBundleItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ('bundle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='menu.menubundle')),
                ('menu', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bundle_items', to='menu.menu')),
            ],
            options={'ordering': ['id']},
        ),
        migrations.AddConstraint(
            model_name='menubundleitem',
            constraint=models.UniqueConstraint(fields=('bundle', 'menu'), name='uniq_bundle_menu'),
        ),
    ]
