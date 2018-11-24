# Generated by Django 2.1.2 on 2018-11-21 11:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AgentClientRel',
            fields=[
                ('index', models.IntegerField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'accounts_mgt_agentclientrel',
            },
        ),
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=45)),
                ('last_name', models.CharField(max_length=45)),
                ('company', models.CharField(max_length=45)),
                ('address', models.CharField(max_length=45)),
                ('email', models.CharField(max_length=45)),
                ('contact_number', models.CharField(max_length=45)),
                ('tin', models.CharField(max_length=45)),
                ('payment_terms', models.CharField(max_length=45)),
                ('discount', models.FloatField(blank=True, null=True)),
                ('net_vat', models.FloatField()),
                ('credit_status', models.IntegerField()),
                ('outstanding_balance', models.FloatField()),
                ('overdue_balance', models.FloatField()),
                ('remarks', models.CharField(blank=True, max_length=45, null=True)),
                ('accounts', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'accounts_mgt_client',
            },
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=45)),
                ('last_name', models.CharField(max_length=45)),
                ('address', models.CharField(max_length=45)),
                ('email', models.CharField(max_length=45)),
                ('contact_number', models.CharField(max_length=45)),
                ('sss', models.CharField(max_length=45)),
                ('philhealth', models.CharField(max_length=45)),
                ('pagibig', models.CharField(max_length=45)),
                ('tin', models.CharField(max_length=45)),
                ('position', models.CharField(choices=[('General Manager', 'General Manager'), ('Sales Coordinator', 'Sales Coordinator'), ('Sales Agent', 'Sales Agent'), ('Credits and Collection Personnel', 'Credits and Collection Personnel'), ('Supervisor', 'Supervisor'), ('Line Leader', 'Line Leader'), ('Production Manager', 'Production Manager'), ('Cutting', 'Cutting'), ('Printing', 'Printing'), ('Extruder', 'Extruder'), ('Delivery', 'Delivery'), ('Warehouse', 'Warehouse'), ('Utility', 'Utility'), ('Maintenance', 'Maintenance')], default='not specified', max_length=200, verbose_name='position')),
                ('accounts', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'accounts_mgt_employee',
            },
        ),
        migrations.AddField(
            model_name='client',
            name='sales_agent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Employee'),
        ),
        migrations.AddField(
            model_name='agentclientrel',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Client'),
        ),
        migrations.AddField(
            model_name='agentclientrel',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Employee'),
        ),
    ]
