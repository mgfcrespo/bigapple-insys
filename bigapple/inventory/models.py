from django.db import models
from django.db.models import Sum, Avg
from datetime import date, timezone
from accounts.models import Employee 
from sales.models import Supplier, ClientItem

from django.apps import apps

#ClientItem = apps.get_model('sales', 'ClientItem')
#Supplier = apps.get_model('sales', 'Supplier')


# Create your models here.

class Inventory(models.Model):
    ITEM_TYPES = (
        ('Raw Materials', 'Raw Materials'),
        ('Machine Parts', 'Machine Parts'),
        ('Ink', 'Ink'),
        ('Others', 'Others')
    )

    RM_TYPES = (
        ('--', '----------------'),
        ('LDPE', 'Low-density polyethylene'),
        ('LLDPE', 'Linear low-density polyethylene'),
        ('HDPE', 'High-density polyethylene'),
        ('PP', 'Polypropylene'),
        ('PET', 'Polyethylene terephthalate')
    )

    item_type = models.CharField('item_type', choices=ITEM_TYPES, max_length=200, default='Not specified', null=True, blank=True)
    rm_type = models.CharField('rm_type', choices=RM_TYPES, max_length=200, default='Not specified', null=True,
                               blank=True)
    id = models.IntegerField(primary_key=True)
    item = models.CharField(max_length=45)
    description = models.CharField(max_length=45, blank=True, null=True)
    quantity = models.IntegerField()
    price = models.FloatField()
    old_count = models.IntegerField(blank=True, null=True)
    new_count = models.IntegerField(blank=True, null=True)
    date_counted = models.DateField(blank=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    class Meta:

        db_table = 'inventory_mgt_inventory'

    def __str__(self):
        return str(self.item)

class SupplierPO(models.Model):
    id = models.IntegerField(primary_key=True)
    total_amount = models.FloatField()
    date_issued = models.DateField()
    delivery_date = models.DateField()
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    class Meta:

        db_table = 'inventory_mgt_supplierpo'

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        supplier_po = '#%s' % (lead_zero)
        return supplier_po

class SupplierPOItems(models.Model):
    id = models.IntegerField(primary_key=True)
    price = models.FloatField()
    quantity = models.FloatField()
    total_price = models.FloatField()
    supplier_po = models.ForeignKey(SupplierPO, on_delete=models.CASCADE)
    item = models.ForeignKey(Inventory, on_delete=models.CASCADE)

    class Meta:

        db_table = 'inventory_mgt_supplierpoitems'

    def calculate_total_price(self): 
        total = (self.price * self.quantity)
        return total

    def save(self, *args, **kwargs):
        self.total_price = self.calculate_total_price()
        super(SupplierPOItems, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.supplier_po) +' : ' + str(self.item)

class MaterialRequisition(models.Model):
    id = models.IntegerField(primary_key=True)
    datetime_issued = models.DateTimeField()
    item = models.CharField(max_length=45)
    quantity = models.IntegerField()
    client_item = models.ForeignKey(ClientItem, on_delete=models.CASCADE)

    class Meta:

        db_table = 'inventory_mgt_materialrequisition'

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        control_number = '#%s' % (lead_zero)
        return control_number

'''
class MaterialRequisitionItems(models.Model):
    matreq = models.ForeignKey(MaterialRequisition, on_delete=models.CASCADE, related_name='materialrequisitionitems_matreq')
    item = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='materialrequisitionitems_item')
    quantity = models.IntegerField('quantity', default=0)

    def __str__(self):
        return str(self.matreq) +' : ' + str(self.id)

class PurchaseRequisition(models.Model):
    placed_by = models.ForeignKey(Employee, on_delete = models.CASCADE, null=True, related_name='purchaserequisition_placed_by')
    date_issued = models.DateField('date_issued', auto_now_add=True)
    date_required = models.DateField('date_required')
    approval = models.BooleanField('approval', default=False)
    status = models.CharField('status', default='waiting', max_length=200)

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        control_number = '#%s' % (lead_zero)
        return control_number
    
class PurchaseRequisitionItems(models.Model):
    purchreq = models.ForeignKey(PurchaseRequisition, on_delete=models.CASCADE, related_name='purchaserequisitionitems_purchreq')
    item = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='purchaserequisitionitems_item')
    quantity = models.IntegerField('quantity')

    def __str__(self):
        return str(self.purchreq) + ' : ' + str(self.item)


#TODO
class SupplierSalesInvoice(models.Model):
    supplier_po = models.ForeignKey(SupplierPO, on_delete=models.CASCADE)
    supplier_po_items = models.ForeignKey(SupplierPOItems, on_delete=models.CASCADE)
    date = models.DateField('date', auto_now_add=True)
    vat = models.DecimalField('vat', decimal_places=2, max_digits=50)
    total_amount = models.IntegerField('total_amount')

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        control_number = '#%s' % (lead_zero)
        return control_number

# class CurrentRMinProduction(models.Model):
#     raw_material = models.ForeignKey(Inventory, on_delete = models.CASCADE, null=True)

'''