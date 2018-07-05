# Generated by Django 2.0.6 on 2018-07-03 10:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales_mgt', '0008_auto_20180703_1610'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientitem',
            name='color',
            field=models.CharField(choices=[('Red', 'Red'), ('Blue', 'Blue'), ('Yellow', 'Yellow'), ('Orange', 'Orange'), ('Green', 'Green'), ('Violet', 'Violet'), ('Black', 'Black'), ('White', 'White'), ('Plain', 'Plain')], max_length=200, verbose_name='color'),
        ),
        migrations.AlterField(
            model_name='clientpo',
            name='payment_terms',
            field=models.CharField(choices=[('15 Days', '15 Days'), ('30 Days', '30 Days'), ('60 Days', '60 Days'), ('90 Days', '90 Days')], default='30', max_length=200, verbose_name='payment terms'),
        ),
        migrations.AlterField(
            model_name='clientpo',
            name='status',
            field=models.CharField(choices=[('waiting', 'waiting'), ('approved', 'approved'), ('uunder production', 'under production'), ('ready for delivery', 'ready for delivery'), ('disapproved', 'disapproved')], default='waiting', max_length=200, verbose_name='status'),
        ),
    ]
