from django.db import models
from datetime import date
from accounts.models import Employee
from sales.models import Supplier

# Create your models here.

# class Supplier(models.Model):
#     name = models.CharField('name', max_length=200)
#     address = models.CharField('address', max_length=200)
#     contact_number = models.CharField('contact_number', max_length=45)


class SupplierItems(models.Model):
    ITEM_TYPES = (
        ('RM', 'Raw Materials'),
        ('MP', 'Machine Parts'),
        ('INK', 'Ink'),
        ('OT', 'Others')
    )
    item_name = models.CharField('item_name', max_length=200)
    item_type = models.CharField('item_type', choices=ITEM_TYPES, max_length=200, default='not specified')
    price = models.IntegerField('price')
    description = models.CharField('description', max_length=200)
    supplier = models.CharField('supplier', max_length=200)

    class Meta:
        verbose_name_plural = "Supplier items"

    def __str__(self):
        return self.item_name


class SupplierPO(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    quantity = models.IntegerField('quantity')
    delivery_date = models.DateField('delivery_date')

class SupplierPOTracking(models.Model):
    supplier_po = models.ForeignKey(SupplierPO, on_delete=models.CASCADE)
    retrieved = models.BooleanField('retrieved', default=False)
    date_retrieved = models.DateField('date_retrieved', blank=True, default='not yet retrieved')

class MaterialRequisition(models.Model):
    SHIFTS = (
        ('1', 'shift 1'),
        ('2', 'shift 2'),
        ('3', 'shift 3')
    )
    date_issued = models.DateField('date_issued', default=date.today())
    issued_to = models.CharField('issued_to', max_length=200)
    brand = models.CharField('brand', max_length=200)
    description = models.CharField('description', max_length=200)
    quantity = models.IntegerField('quantity')
    to_be_used_for = models.CharField('to_be_used_for', max_length=200)
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    approval = models.BooleanField('approval', default=False)

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        control_number = '#%s' % (lead_zero)
        return control_number


class PurchaseRequisition(models.Model):
    placed_by = models.ForeignKey(Employee, on_delete = models.CASCADE, null=True)
    date_issued = models.DateField('date_issued')
    date_required = models.DateField('date_required')
    # supplier may not be specified on request-- supplier = models.ForeignKey(Supplier, on_delete = models.CASCADE)
    description = models.CharField('description', max_length=200)
    quantity = models.IntegerField('quantity')
    approval = models.BooleanField('approval', default=False)
    

class Inventory(models.Model):
    RM_TYPES = (
        ('LDPE', 'Low-density polyethylene'),
        ('LLDPE', 'Linear low-density polyethylene'),
        ('HDPE', 'High-density polyethylene'),
        ('PP', 'Polypropylene'),
        ('PET', 'Polyethylene terephthalate')
    )
    rm_name = models.CharField('rm_name', max_length=200, default='not specified')
    rm_type = models.CharField('rm_type', choices=RM_TYPES, max_length=200, default='not specified')
    quantity = models.IntegerField('quantity')


    def __str__(self):
        return self.rm_name 

class InventoryCountAsof(models.Model):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    old_count = models.IntegerField('old_count', default=0)
    new_count = models.IntegerField('new_count', default=0)
    date_counted = models.DateField('date_counted', )


class CurrentRMinProduction(models.Model):
    raw_material = models.ForeignKey(Inventory, on_delete = models.CASCADE, null=True)