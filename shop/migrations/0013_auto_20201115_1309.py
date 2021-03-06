# Generated by Django 3.1.3 on 2020-11-15 18:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0012_auto_20201115_1043'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='description',
            field=models.TextField(blank=True, default='Description coming soon!', help_text='Describe the product, its history and why you were inspired to make it.'),
        ),
    ]
