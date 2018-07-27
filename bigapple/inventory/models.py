from django.db import models
from django.db.models import Sum, Avg
from datetime import date, timezone
from accounts.models import Employee
from sales.models import Supplier

# Create your models here.

# class Supplier(models.Model):
#     name = models.CharField('name', max_length=200)
#     address = models.CharField('address', max_length=200)
#     contact_number = models.CharField('contact_number', max_length=45)

class SupplierRawMaterials(models.Model):
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
    price = models.DecimalField('price', decimal_places=2, max_digits=50)
    rm_type = models.CharField('rm_type', choices=RM_TYPES, max_length=200, default='not specified', null=True,
                               blank=True)


class Inventory(models.Model):
    item = models.CharField('item', max_length=200)
    item_type = models.CharField('item_type', max_length=200)
    description = models.CharField('description', max_length=200, blank=True, null=True)
    quantity = models.IntegerField('quantity', default=0)

    def __str__(self):
        return str(self.item)

class InventoryCountAsof(models.Model):
    RM_TYPES = (
        ('--', '----------------'),
        ('LDPE', 'Low-density polyethylene'),
        ('LLDPE', 'Linear low-density polyethylene'),
        ('HDPE', 'High-density polyethylene'),
        ('PP', 'Polypropylene'),
        ('PET', 'Polyethylene terephthalate')
    )

    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    old_count = models.IntegerField('old_count', default=0)
    new_count = models.IntegerField('new_count', default=0)
    date_counted = models.DateField('date_counted', )
    time = models.TimeField('time', auto_now_add=True, blank=True)
    #item_type = models.CharField('item_type', choices=ITEM_TYPES, max_length=200, default='Raw Material')
    rm_type = models.CharField('rm_type', choices=RM_TYPES, max_length=200, default='--', null=True, blank=True)
    item_name = models.CharField('item_name', max_length=200, default='Not Specified')


    def __str__(self):
        return str(self.supplier) +' : ' + str(self.item_name)




class SupplierPO(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    total_amount = models.DecimalField('total_amount', decimal_places = 2, max_digits=50, null=True, blank = True)
    date_issued = models.DateField('date_issued', auto_now_add=True)
    delivery_date = models.DateField('delivery_date')

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        supplier_po = '#%s' % (lead_zero)
        return supplier_po

class SupplierPOItems(models.Model):
    supplier_po = models.ForeignKey(SupplierPO, on_delete=models.CASCADE)
    item_name = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    price = models.DecimalField('price', decimal_places = 2, max_digits=50,)
    quantity = models.IntegerField('quantity')
    total_price = models.DecimalField('total_price', decimal_places = 2, max_digits=50,)
    
    class Meta:
        verbose_name_plural = "Supplier po items"

    def calculate_total_price(self): 
        total = (self.price * self.quantity)
        return total

    def save(self, *args, **kwargs):
        self.total_price = self.calculate_total_price()
        super(SupplierPOItems, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.supplier_po) +' : ' + str(self.item_name)

#TODO
class SupplierPOTracking(models.Model):
    supplier_po = models.ForeignKey(SupplierPO, on_delete=models.CASCADE)
    retrieved = models.BooleanField('retrieved', default=False)
    date_retrieved = models.DateField('date_retrieved', blank=True, default='not yet retrieved')

    def __str__(self):
        return self.supplier_po

class MaterialRequisition(models.Model):
    SHIFTS = (
        ('Shift 1', 'shift 1'),
        ('Shift 2', 'shift 2'),
        ('Shift 3', 'shift 3')
    )

    date_issued = models.DateField('date_issued', auto_now_add=True)
    issued_to = models.ForeignKey(Employee, on_delete = models.CASCADE, null=True)
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    approval = models.BooleanField('approval', default=False)
    status = models.CharField('status', default='waiting', max_length=200)

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        control_number = '#%s' % (lead_zero)
        return control_number


class MaterialRequisitionItems(models.Model):
    matreq = models.ForeignKey(MaterialRequisition, on_delete=models.CASCADE)
    brand = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    quantity = models.IntegerField('quantity')
    to_be_used_for = models.CharField('to_be_used_for', max_length=200)

    def __str__(self):
        return str(self.matreq) +' : ' + str(self.brand)

class PurchaseRequisition(models.Model):
    placed_by = models.ForeignKey(Employee, on_delete = models.CASCADE, null=True)
    date_issued = models.DateField('date_issued', auto_now_add=True)
    date_required = models.DateField('date_required')
    approval = models.BooleanField('approval', default=False)
    status = models.CharField('status', default='waiting', max_length=200)

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        control_number = '#%s' % (lead_zero)
        return control_number
    
class PurchaseRequisitionItems(models.Model):
    purchreq = models.ForeignKey(PurchaseRequisition, on_delete=models.CASCADE)
    item = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    quantity = models.IntegerField('quantity')

    def __str__(self):
        return str(self.purchreq) + ' : ' + str(self.item)

'''
class InventoryCountAsof(models.Model):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    person = models.ForeignKey(Employee, on_delete=models.CASCADE, default = 1)
    old_count = models.IntegerField('old_count', default=0)
    new_count = models.IntegerField('new_count', default=0)
    date_counted = models.DateField('date_counted', auto_now_add=True)
    time = models.TimeField('time', auto_now_add=True, blank=True)

    def __str__(self):
        return str(self.id) +' : '+str(self.inventory) +' : ' + str(self.date_counted)
'''
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