# Generated by Django 3.1.3 on 2020-11-03 22:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0003_auto_20201102_2110'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='inventory_stock',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='productphoto',
            name='is_default',
            field=models.BooleanField(default=False),
        ),
    ]
