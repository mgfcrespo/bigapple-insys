# Generated by Django 2.0.6 on 2018-07-23 09:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sales_mgt', '0042_auto_20180718_1353'),
        ('accounts_mgt', '0004_auto_20180703_1849'),
        ('production_mgt', '0013_auto_20180723_1747'),
    ]

    operations = [
        migrations.CreateModel(
            name='MachineSchedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_task', models.CharField(blank=True, default='none', max_length=200, verbose_name='job_task')),
                ('shift', models.CharField(choices=[('Shift 1', 'shift 1'), ('Shift 2', 'shift 2'), ('Shift 3', 'shift 3')], default='not specified', max_length=200, verbose_name='shift')),
                ('working_date', models.DateField(auto_now_add=True, verbose_name='working_date')),
                ('client_po', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='sales_mgt.ClientPO')),
                ('machine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='production_mgt.Machine')),
            ],
        ),
        migrations.CreateModel(
            name='WorkerSchedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shift', models.CharField(choices=[('Shift 1', 'shift 1'), ('Shift 2', 'shift 2'), ('Shift 3', 'shift 3')], default='not specified', max_length=200, verbose_name='shift')),
                ('working_date', models.DateTimeField(auto_now_add=True, verbose_name='working_date')),
                ('machine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='production_mgt.Machine')),
                ('worker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts_mgt.Employee')),
            ],
        ),
    ]
