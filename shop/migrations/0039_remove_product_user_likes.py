# Generated by Django 3.1.3 on 2020-12-29 06:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0038_userprofile_favorites'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='user_likes',
        ),
    ]