# Generated by Django 2.1.2 on 2018-11-09 07:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CuttingSchedule',
            fields=[
                ('index', models.IntegerField(primary_key=True, serialize=False)),
                ('shift', models.IntegerField()),
                ('datetime_in', models.DateTimeField()),
                ('datetime_out', models.DateTimeField()),
                ('weight_rolls', models.FloatField()),
                ('core_weight', models.FloatField()),
                ('output_kilos', models.FloatField()),
                ('number_rolls', models.FloatField()),
                ('starting_scrap', models.FloatField()),
                ('cutting_scrap', models.FloatField()),
                ('remarks', models.CharField(blank=True, max_length=45, null=True)),
                ('quantity', models.IntegerField()),
                ('line', models.IntegerField()),
            ],
            options={
                'db_table': 'production_mgt_cuttingschedule',
            },
        ),
        migrations.CreateModel(
            name='ExtruderSchedule',
            fields=[
                ('index', models.IntegerField(primary_key=True, serialize=False)),
                ('shift', models.IntegerField()),
                ('datetime_in', models.DateTimeField()),
                ('datetime_out', models.DateTimeField()),
                ('weight_rolls', models.FloatField()),
                ('core_weight', models.FloatField()),
                ('output_kilos', models.FloatField()),
                ('number_rolls', models.FloatField()),
                ('starting_scrap', models.FloatField()),
                ('extruder_scrap', models.FloatField()),
                ('remarks', models.CharField(blank=True, max_length=45, null=True)),
            ],
            options={
                'db_table': 'production_mgt_extruderschedule',
            },
        ),
        migrations.CreateModel(
            name='JobOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('Waiting', 'Waiting'), ('On Queue', 'On Queue'), ('Under Cutting', 'Under Cutting'), ('Under Extrusion', 'Under Extrusion'), ('Under Printing', 'Under Printing'), ('Under Packaging', 'Under Packaging'), ('Ready for delivery', 'Ready for delivery'), ('Delivered', 'Delivered'), ('Cancelled', 'Cancelled')], default='Waiting', max_length=200, verbose_name='status')),
                ('remarks', models.CharField(blank=True, max_length=45, null=True)),
                ('is_laminate', models.IntegerField()),
                ('rush_order', models.IntegerField()),
                ('date_issued', models.DateTimeField()),
                ('date_required', models.DateTimeField()),
                ('client', models.CharField(max_length=45)),
                ('total_amount', models.FloatField()),
            ],
            options={
                'db_table': 'production_mgt_joborder',
            },
        ),
        migrations.CreateModel(
            name='LaminatingSchedule',
            fields=[
                ('index', models.IntegerField(primary_key=True, serialize=False)),
                ('shift', models.IntegerField()),
                ('datetime_in', models.DateTimeField()),
                ('datetime_out', models.DateTimeField()),
                ('starting_scrap', models.FloatField()),
                ('laminating_scrap', models.FloatField()),
                ('remarks', models.CharField(blank=True, max_length=45, null=True)),
                ('quantity', models.IntegerField(blank=True, null=True)),
                ('job_order', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='production.JobOrder')),
            ],
            options={
                'db_table': 'production_mgt_laminatingschedule',
            },
        ),
        migrations.CreateModel(
            name='Machine',
            fields=[
                ('machine_type', models.CharField(choices=[('Cutting', 'Cutting'), ('Printing', 'Printing'), ('Extruder', 'Extruder')], default='not specified', max_length=200, verbose_name='machine_type')),
                ('machine_id', models.IntegerField(primary_key=True, serialize=False)),
                ('state', models.CharField(max_length=45)),
            ],
            options={
                'db_table': 'production_mgt_machine',
            },
        ),
        migrations.CreateModel(
            name='PrintingSchedule',
            fields=[
                ('index', models.IntegerField(primary_key=True, serialize=False)),
                ('shift', models.IntegerField()),
                ('datetime_in', models.DateTimeField()),
                ('datetime_out', models.DateTimeField()),
                ('weight_rolls', models.FloatField()),
                ('core_weight', models.FloatField()),
                ('output_kilos', models.FloatField()),
                ('number_rolls', models.FloatField()),
                ('starting_scrap', models.FloatField()),
                ('printing_scrap', models.FloatField()),
                ('remarks', models.CharField(blank=True, max_length=45, null=True)),
                ('job_order', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='production.JobOrder')),
                ('machine', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='production.Machine')),
                ('operator', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='accounts.Employee')),
            ],
            options={
                'db_table': 'production_mgt_printingschedule',
            },
        ),
        migrations.AddField(
            model_name='laminatingschedule',
            name='machine',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='production.Machine'),
        ),
        migrations.AddField(
            model_name='laminatingschedule',
            name='operator',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='accounts.Employee'),
        ),
        migrations.AddField(
            model_name='extruderschedule',
            name='job_order',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='production.JobOrder'),
        ),
        migrations.AddField(
            model_name='extruderschedule',
            name='machine',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='production.Machine'),
        ),
        migrations.AddField(
            model_name='extruderschedule',
            name='operator',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='accounts.Employee'),
        ),
        migrations.AddField(
            model_name='cuttingschedule',
            name='job_order',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='production.JobOrder'),
        ),
        migrations.AddField(
            model_name='cuttingschedule',
            name='machine',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='production.Machine'),
        ),
        migrations.AddField(
            model_name='cuttingschedule',
            name='operator',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, to='accounts.Employee'),
        ),
    ]
