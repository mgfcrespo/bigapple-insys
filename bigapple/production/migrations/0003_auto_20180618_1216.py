# Generated by Django 2.1a1 on 2018-06-18 04:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('production_mgt', '0002_auto_20180618_1213'),
    ]

    operations = [
        migrations.AlterField(
            model_name='printingschedule',
            name='repeat_order',
            field=models.BooleanField(default='True', verbose_name='repeat_order'),
        ),
    ]
