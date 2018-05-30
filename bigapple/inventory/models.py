from django.db import models


# Create your models here.

class Supplier(models.Model):
    name = models.CharField('name', max_length=200)
    address = models.CharField('address', max_length=200)
    contact_number = models.CharField('contact_number', max_length=45)

class MaterialRequisition(models.Model):
    SHIFTS = (
        ('A', 'shift 1'),
        ('B', 'shift 2'),
        ('C', 'shift 3')
    )
    date_issued = models.DateField('date_issued')
    issued_to = models.CharField('issued_to', max_length=200)
    brand = models.CharField('brand', max_length=200)
    description = models.CharField('description', max_length=200)
    quantity = models.IntegerField('quantity')
    to_be_used_for = models.CharField('to_be_used_for', max_length=200)
    shift = models.CharField('shift', choices=SHIFTS, default='not specified')
    approval = models.BooleanField('approval', default=false)

class PurchaseRequisition(models.Model):
    #placed_by = models.ForeignKey(Accounts.name)
    #department = models.ForeignKey(Accounts.department)
    date_issued = models.DateField('date_issued')
    date_required = models.DateField('date_required')
    #supplier may not be specified on request-- supplier = models.ForeignKey(Supplier, on_delete = models.CASCADE)
    description = models.CharField('description', max_length=200)
    quantity = models.IntegerField('quantity')
    approval = models.BooleanField('approval', default=false)

class Inventory(models.Model):
    rm_type = models.CharField('rm_type', max_length=200)
    description = models.CharField('descrption', max_length=200)
    brand = models.CharField('brand', max_length=200)
    quantity = models.IntegerField('quantity')


