# Generated by Django 5.0.1 on 2024-03-05 15:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_remove_specialoffer_product_specialoffer_category_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='SpecialOffer',
        ),
    ]
