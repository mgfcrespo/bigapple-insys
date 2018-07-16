from django.db import models
from django.db.models import Sum, Avg
from datetime import date
from accounts.models import Employee
from sales.models import Supplier

# Create your models here.

# class Supplier(models.Model):
#     name = models.CharField('name', max_length=200)
#     address = models.CharField('address', max_length=200)
#     contact_number = models.CharField('contact_number', max_length=45)

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
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    item_name = models.CharField('item_name', max_length=200, default='not specified')
    item_type = models.CharField('item_type', choices=ITEM_TYPES, max_length=200, default='not specified')
    rm_type = models.CharField('rm_type', choices=RM_TYPES, max_length=200, default='not specified', null=True, blank=True)
    description = models.CharField('description', max_length=200)
    price = models.DecimalField('price', decimal_places=2, max_digits=50)
    quantity = models.IntegerField('quantity')

    def itemtype(self): 
        return self.item_type +' : ' + str(self.rm_type)

    def __str__(self):
        return self.item_name 


class SupplierPO(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    total_amount = models.IntegerField('total_amount')
    date_issued = models.DateField('date_issued', auto_now_add=True)
    delivery_date = models.DateField('delivery_date')
    
    def calculate_total_amount(self): 
        items = SupplierPOItems.objects.all()
        total = items.objects.filter(self.SupplierPO==items.supplier_po).aggregate(Sum('total_price'))
        return total

    def save(self, *args, **kwargs):
        self.total_amount = self.calculate_total_amount()
        super(SupplierPO, self).save(*args, **kwargs)

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        supplier_po = '#%s' % (lead_zero)
        return supplier_po

class SupplierPOItems(models.Model):
    supplier_po = models.ForeignKey(SupplierPO, on_delete=models.CASCADE)
    item_name = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    price = models.IntegerField('price')
    quantity = models.IntegerField('quantity')
    total_price = models.IntegerField('total_price')
    
    class Meta:
        verbose_name_plural = "Supplier po items"

    def calculate_total_price(self): 
        total = (self.price * self.quantity)
        return total

    def save(self, *args, **kwargs):
        self.total_price = self.calculate_total_price()
        super(SupplierPOItems, self).save(*args, **kwargs)

    def __str__(self):
        return self.supplier_po + str(self.item_name)


class SupplierPOTracking(models.Model):
    supplier_po = models.ForeignKey(SupplierPO, on_delete=models.CASCADE)
    retrieved = models.BooleanField('retrieved', default=False)
    date_retrieved = models.DateField('date_retrieved', blank=True, default='not yet retrieved')

class MaterialRequisition(models.Model):
    SHIFTS = (
        ('Shift 1', 'shift 1'),
        ('Shift 2', 'shift 2'),
        ('Shift 3', 'shift 3')
    )
    date_issued = models.DateField('date_issued', auto_now_add=True)
    issued_to = models.CharField('issued_to', max_length=200, null=True)
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    approval = models.BooleanField('approval', default=False)

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        control_number = '#%s' % (lead_zero)
        return control_number


class MaterialRequisitionItems(models.Model):
    matreq = models.ForeignKey(MaterialRequisition, on_delete=models.CASCADE)
    brand = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    quantity = models.IntegerField('quantity')
    to_be_used_for = models.CharField('to_be_used_for', max_length=200)

class PurchaseRequisition(models.Model):
    placed_by = models.ForeignKey(Employee, on_delete = models.CASCADE, null=True)
    date_issued = models.DateField('date_issued', auto_now_add=True)
    date_required = models.DateField('date_required')
    # supplier may not be specified on request-- supplier = models.ForeignKey(Supplier, on_delete = models.CASCADE)
    description = models.CharField('description', max_length=200)
    quantity = models.IntegerField('quantity')
    approval = models.BooleanField('approval', default=False)
    

class InventoryCountAsof(models.Model):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    old_count = models.IntegerField('old_count', default=0)
    new_count = models.IntegerField('new_count', default=0)
    date_counted = models.DateField('date_counted', )


# class CurrentRMinProduction(models.Model):
#     raw_material = models.ForeignKey(Inventory, on_delete = models.CASCADE, null=True)