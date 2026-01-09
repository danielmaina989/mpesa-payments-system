from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CallbackLog',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('received_at', models.DateTimeField(auto_now_add=True)),
                ('checkout_request_id', models.CharField(max_length=50, blank=True, null=True)),
                ('payload', models.JSONField()),
                ('processed', models.BooleanField(default=False)),
                ('processing_status', models.CharField(max_length=32, blank=True, null=True)),
                ('details', models.TextField(blank=True)),
            ],
            options={'ordering': ['-received_at']},
        ),
    ]

