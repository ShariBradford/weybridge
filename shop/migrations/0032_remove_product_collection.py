# Generated by Django 3.1.3 on 2020-12-14 23:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0031_product_collection'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='collection',
        ),
    ]
