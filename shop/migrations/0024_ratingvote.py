# Generated by Django 3.1.3 on 2020-11-16 01:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shop', '0023_answer_updated_by'),
    ]

    operations = [
        migrations.CreateModel(
            name='RatingVote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('score_type', models.SmallIntegerField(choices=[(-1, 'down_vote'), (1, 'up_vote')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('rating', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='shop.rating')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='votes', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]