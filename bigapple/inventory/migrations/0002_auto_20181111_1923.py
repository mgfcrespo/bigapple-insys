# Generated by Django 2.1.2 on 2018-11-11 11:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='supplier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales.Supplier'),
        ),
        migrations.AlterField(
            model_name='materialrequisition',
            name='client_item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales.ClientItem'),
        ),
        migrations.AlterField(
            model_name='supplierpo',
            name='supplier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales.Supplier'),
        ),
        migrations.AlterField(
            model_name='supplierpoitems',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.Inventory'),
        ),
        migrations.AlterField(
            model_name='supplierpoitems',
            name='supplier_po',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.SupplierPO'),
        ),
    ]
