# Generated by Django 3.1.3 on 2020-12-26 08:23

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0033_product_collection'),
    ]

    operations = [
        migrations.AddField(
            model_name='promotion',
            name='name',
            field=models.CharField(default='Sale', max_length=255),
        ),
        migrations.AlterField(
            model_name='collection',
            name='description',
            field=models.TextField(blank=True, default='Description coming soon!', null=True),
        ),
        migrations.AlterField(
            model_name='productphoto',
            name='is_default',
            field=models.BooleanField(default=False, verbose_name='Default?'),
        ),
        migrations.AlterField(
            model_name='rating',
            name='number_of_stars',
            field=models.IntegerField(choices=[(1, 'It was awful!'), (2, 'Not so great.'), (3, 'Just Ok.'), (4, 'I liked it!'), (5, 'Pretty freakin awesome!')], validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='Rating'),
        ),
    ]
