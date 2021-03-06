# Generated by Django 3.1.3 on 2020-12-26 10:10

from django.db import migrations, models
import shop.models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0036_promotion_sale'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='description',
            field=models.CharField(blank=True, default='Description coming soon!', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='sale',
            name='profile_pic',
            field=models.ImageField(blank=True, default='sales/blank-sale.jpg', null=True, upload_to=shop.models.sale_directory_path),
        ),
        migrations.AddField(
            model_name='sale',
            name='terms',
            field=models.TextField(blank=True, default='Terms coming soon.', null=True),
        ),
    ]
