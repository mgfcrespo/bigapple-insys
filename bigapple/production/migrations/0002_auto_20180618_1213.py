# Generated by Django 2.1a1 on 2018-06-18 04:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sales_mgt', '0002_auto_20180617_2246'),
        ('production_mgt', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MachineSchedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_task', models.CharField(blank=True, default='none', max_length=200, verbose_name='job_task')),
                ('shift', models.CharField(choices=[('1', 'shift 1'), ('2', 'shift 2'), ('3', 'shift 3')], default='not specified', max_length=200, verbose_name='shift')),
                ('working_date', models.DateField(auto_now_add=True, verbose_name='working_date')),
                ('operator', models.CharField(max_length=200, verbose_name='operator')),
                ('client_po', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='sales_mgt.ClientPO')),
                ('machine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='production_mgt.Machine')),
            ],
        ),
        migrations.AlterField(
            model_name='cuttingschedule',
            name='cutting_scrap',
            field=models.DecimalField(decimal_places=3, max_digits=12, verbose_name='cutting_scrap'),
        ),
        migrations.AlterField(
            model_name='cuttingschedule',
            name='date',
            field=models.DateField(auto_now_add=True, verbose_name='date'),
        ),
        migrations.AlterField(
            model_name='cuttingschedule',
            name='machine',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='production_mgt.Machine'),
        ),
        migrations.AlterField(
            model_name='cuttingschedule',
            name='number_rolls',
            field=models.DecimalField(decimal_places=3, max_digits=12, verbose_name='number_rolls'),
        ),
        migrations.AlterField(
            model_name='cuttingschedule',
            name='output_kilos',
            field=models.DecimalField(decimal_places=3, max_digits=12, verbose_name='output_kilos'),
        ),
        migrations.AlterField(
            model_name='cuttingschedule',
            name='quantity',
            field=models.DecimalField(decimal_places=3, max_digits=12, verbose_name='quantity'),
        ),
        migrations.AlterField(
            model_name='cuttingschedule',
            name='starting_scrap',
            field=models.DecimalField(decimal_places=3, max_digits=12, verbose_name='starting_scrap'),
        ),
        migrations.AlterField(
            model_name='cuttingschedule',
            name='time_in',
            field=models.TimeField(auto_now_add=True, verbose_name='time_in'),
        ),
        migrations.AlterField(
            model_name='cuttingschedule',
            name='time_out',
            field=models.TimeField(auto_now_add=True, verbose_name='time_out'),
        ),
        migrations.AlterField(
            model_name='extruderschedule',
            name='core_weight',
            field=models.DecimalField(decimal_places=3, max_digits=12, verbose_name='core_weight'),
        ),
        migrations.AlterField(
            model_name='extruderschedule',
            name='date',
            field=models.DateField(auto_now_add=True, verbose_name='date'),
        ),
        migrations.AlterField(
            model_name='extruderschedule',
            name='extruder_scrap',
            field=models.DecimalField(decimal_places=3, max_digits=12, verbose_name='extruder_scrap'),
        ),
        migrations.AlterField(
            model_name='extruderschedule',
            name='machine',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='production_mgt.Machine'),
        ),
        migrations.AlterField(
            model_name='extruderschedule',
            name='net_weight',
            field=models.DecimalField(decimal_places=3, max_digits=12, verbose_name='net_weight'),
        ),
        migrations.AlterField(
            model_name='extruderschedule',
            name='number_rolls',
            field=models.DecimalField(decimal_places=3, max_digits=12, verbose_name='number_rolls'),
        ),
        migrations.AlterField(
            model_name='extruderschedule',
            name='output_kilos',
            field=models.DecimalField(decimal_places=3, max_digits=12, verbose_name='output_kilos'),
        ),
        migrations.AlterField(
            model_name='extruderschedule',
            name='starting_scrap',
            field=models.DecimalField(decimal_places=3, max_digits=12, verbose_name='starting_scrap'),
        ),
        migrations.AlterField(
            model_name='extruderschedule',
            name='time_in',
            field=models.TimeField(auto_now_add=True, verbose_name='time_in'),
        ),
        migrations.AlterField(
            model_name='extruderschedule',
            name='time_out',
            field=models.TimeField(auto_now_add=True, verbose_name='time_out'),
        ),
        migrations.AlterField(
            model_name='extruderschedule',
            name='weight_rolls',
            field=models.DecimalField(decimal_places=3, max_digits=12, verbose_name='weight_rolls'),
        ),
        migrations.AlterField(
            model_name='printingschedule',
            name='machine',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='production_mgt.Machine'),
        ),
        migrations.AlterField(
            model_name='printingschedule',
            name='number_rolls',
            field=models.DecimalField(decimal_places=3, max_digits=12, verbose_name='number_rolls'),
        ),
        migrations.AlterField(
            model_name='printingschedule',
            name='output_kilos',
            field=models.DecimalField(decimal_places=3, max_digits=12, verbose_name='output_kilos'),
        ),
        migrations.AlterField(
            model_name='printingschedule',
            name='printing_scrap',
            field=models.DecimalField(decimal_places=3, max_digits=12, verbose_name='printing_scrap'),
        ),
        migrations.AlterField(
            model_name='printingschedule',
            name='repeat_order',
            field=models.BooleanField(default='true', verbose_name='repeat_order'),
        ),
        migrations.AlterField(
            model_name='printingschedule',
            name='starting_scrap',
            field=models.DecimalField(decimal_places=3, max_digits=12, verbose_name='starting_scrap'),
        ),
    ]
