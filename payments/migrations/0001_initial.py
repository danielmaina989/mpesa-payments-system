from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('phone_number', models.CharField(max_length=12)),
                ('amount', models.DecimalField(max_digits=10, decimal_places=2)),
                ('status', models.CharField(max_length=10, choices=[('INITIATED', 'Initiated'), ('PENDING', 'Pending'), ('SUCCESS', 'Success'), ('FAILED', 'Failed')], default='INITIATED')),
                ('mpesa_checkout_request_id', models.CharField(max_length=50, blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]

