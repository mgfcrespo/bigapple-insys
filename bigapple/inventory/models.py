from django.db import models
from django.db.models import Sum, Avg
from datetime import date, timezone
from accounts.models import Employee 
from sales.models import Supplier
from production.models import JobOrder


# Create your models here.

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

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='supplierrawmaterials_supplier')
    price = models.DecimalField('price', decimal_places=2, max_digits=50)
    rm_type = models.CharField('rm_type', choices=RM_TYPES, max_length=200, default='Not specified', null=True, blank=True)
    item_type = models.CharField('item_type', choices=ITEM_TYPES, max_length=200, default='Not specified', null=True,
                                 blank=True)
    item = models.CharField('item', max_length=200)

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

    item = models.CharField('item', max_length=200)
    item_type = models.CharField('item_type', choices=ITEM_TYPES, max_length=200, default='Not specified', null=True, blank=True)
    rm_type = models.CharField('rm_type', choices=RM_TYPES, max_length=200, default='Not specified', null=True,
                               blank=True)
    description = models.CharField('description', max_length=200, blank=True, null=True)
    quantity = models.IntegerField('quantity', default=0)

    def __str__(self):
        return str(self.item)

class InventoryCountAsof(models.Model):
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

    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='inventorycountasof_inventory')
    old_count = models.IntegerField('old_count', default=0)
    new_count = models.IntegerField('new_count', default=0)
    date_counted = models.DateField('date_counted', )
    time = models.TimeField('time', auto_now_add=True, blank=True)
    item_type = models.CharField('item_type', choices=ITEM_TYPES, max_length=200, default='Raw Material')
    rm_type = models.CharField('rm_type', choices=RM_TYPES, max_length=200, default='--', null=True, blank=True)
    item = models.CharField('item', max_length=200, default='Not Specified')


    def __str__(self):
        return str(self.supplier) +' : ' + str(self.item)


class SupplierPO(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='supplierpo_supplier')
    total_amount = models.DecimalField('total_amount', decimal_places = 2, max_digits=50, null=True, blank = True)
    date_issued = models.DateField('date_issued', auto_now_add=True)
    delivery_date = models.DateField('delivery_date')

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        supplier_po = '#%s' % (lead_zero)
        return supplier_po

class SupplierPOItems(models.Model):
    supplier_po = models.ForeignKey(SupplierPO, on_delete=models.CASCADE, related_name='supplierpoitems_supplier_po')
    item = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='supplierpoitems_item')
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
        return str(self.supplier_po) +' : ' + str(self.item)

class MaterialRequisition(models.Model):
    date_issued = models.DateField('date_issued', auto_now_add=True)
    approval = models.BooleanField('approval', default=False)
    status = models.CharField('status', default='waiting', max_length=200)
    jo = models.ForeignKey(JobOrder, on_delete=models.CASCADE, related_name='materialrequisition_jo')

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        control_number = '#%s' % (lead_zero)
        return control_number


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

'''