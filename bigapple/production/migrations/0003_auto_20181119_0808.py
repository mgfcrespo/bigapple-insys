# Generated by Django 2.1.3 on 2018-11-19 08:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0002_auto_20181117_1424'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cuttingschedule',
            name='core_weight',
        ),
        migrations.RemoveField(
            model_name='cuttingschedule',
            name='weight_rolls',
        ),
    ]
