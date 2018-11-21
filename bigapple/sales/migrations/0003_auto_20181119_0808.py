# Generated by Django 2.1.3 on 2018-11-19 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0002_auto_20181117_1424'),
    ]

    operations = [
        migrations.AddField(
            model_name='salesinvoice',
            name='days_passed',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='salesinvoice',
            name='date_due',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='salesinvoice',
            name='date_issued',
            field=models.DateField(blank=True, null=True),
        ),
    ]
