# Generated by Django 3.1.3 on 2020-11-15 23:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shop', '0022_auto_20201115_1834'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='updated_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='answers_updated', to='auth.user'),
            preserve_default=False,
        ),
    ]