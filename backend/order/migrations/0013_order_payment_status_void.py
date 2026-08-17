from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0012_order_cancel_audit_trail'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_status',
            field=models.CharField(
                choices=[
                    ('unpaid', 'Unpaid'),
                    ('paid', 'Paid'),
                    ('pending', 'Pending'),
                    ('void', 'Batal'),
                ],
                default='unpaid',
                max_length=10,
            ),
        ),
    ]