from django.db import models

from accounts.models import Employee
from sales.models import Supplier, ClientItem


# Create your models here.

class Inventory(models.Model):
    ITEM_TYPES = (
        ('Raw Materials', 'Raw Materials'),
        ('Machine Parts', 'Machine Parts'),
        ('Ink', 'Ink'),
        ('Cylinder', 'Cylinder'),
        ('Others', 'Others')
    )

    RM_TYPES = (
        ('--', '----------------'),
        ('LDPE', 'Low-density polyethylene'),
        ('LLDPE', 'Linear low-density polyethylene'),
        ('HDPE', 'High-density polyethylene'),
        ('PP', 'Polypropylene'),
        ('PET', 'Polyethylene terephthalate'),
        ('Pelletized PE', 'Pelletized polyethylene '),
        ('Pelletized HD', 'Pelletized high-density polyethylene'),
    )

    item_type = models.CharField('item_type', choices=ITEM_TYPES, max_length=200, default='Not specified', null=True, blank=True)
    rm_type = models.CharField('rm_type', choices=RM_TYPES, max_length=200, default='Not specified', null=True,
                               blank=True)
    item = models.CharField(max_length=45)
    description = models.CharField(max_length=45, blank=True, null=True)
    quantity = models.IntegerField()
    price = models.FloatField()
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    class Meta:
        db_table = 'inventory_mgt_inventory'

    def __str__(self):
        return str(self.item)

class InventoryCount(models.Model):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    old_count = models.IntegerField(blank=True, null=True)
    new_count = models.IntegerField(blank=True, null=True)
    date_counted = models.DateField(blank=True, null=True)
    count_person = models.ForeignKey(Employee, on_delete=models.CASCADE)

    class Meta:
        db_table = 'inventory_mgt_inventorycount'

    def __str__(self):
        return str(self.inventory)

class SupplierPO(models.Model):
    total_amount = models.FloatField(null=True, blank=True)
    date_issued = models.DateField(auto_now_add=True)
    delivery_date = models.DateField()
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    class Meta:
        db_table = 'inventory_mgt_supplierpo'

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        supplier_po = '#%s' % (lead_zero)
        return supplier_po

    def save(self, *args, **kwargs):
        super(SupplierPO, self).save(*args, **kwargs)

class SupplierPOItems(models.Model):
    price = models.FloatField()
    quantity = models.FloatField()
    total_price = models.FloatField()
    supplier_po = models.ForeignKey(SupplierPO, on_delete=models.CASCADE)
    item = models.ForeignKey(Inventory, on_delete=models.CASCADE)

    class Meta:
        db_table = 'inventory_mgt_supplierpoitems'

    def calculate_total_price(self):
        item = self.item
        total = (item.price * self.quantity)
        return total

    def save(self, *args, **kwargs):
        item = self.item
        self.price = item.price
        self.total_price = self.calculate_total_price()
        super(SupplierPOItems, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.supplier_po) +' : ' + str(self.item)

class MaterialRequisition(models.Model):
    STATUS = (
        ('Retrieved', 'Retrieved'),
        ('Pending', 'Pending'),
    )

    datetime_issued = models.DateTimeField(auto_now_add=True)
    shift = models.IntegerField(null=True, blank=True)
    item = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    client_item = models.ForeignKey(ClientItem, on_delete=models.CASCADE)
    status = models.CharField(default='Pending', choices=STATUS, max_length=200, null=True, blank=True)

    class Meta:
        db_table = 'inventory_mgt_materialrequisition'

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        control_number = '#%s' % (lead_zero)
        return control_number