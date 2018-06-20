from django.db import models
from django.forms import ModelForm
from datetime import date
from django.urls import reverse
from accounts.models import Client

# Create your models here.

class Product(models.Model):
    product = models.CharField('product', max_length=200)
    description = models.CharField('description', max_length=200)

    def __str__(self):
        return self.products

class ClientItem(models.Model):
    clients = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)  # to allow suggestions
    products = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    note = models.CharField('note', max_length=200, default='')
    width = models.DecimalField('width', decimal_places=3, max_digits=12)
    length = models.DecimalField('length', decimal_places=3, max_digits=12)
    color = models.CharField('color', max_length=200)
    gusset = models.DecimalField('gusset', decimal_places=3, max_digits=12)
    quantity = models.IntegerField('quantity')
    price = models.DecimalField('price', decimal_places=3, max_digits=12)
    client_po = models.ManyToManyField(ClientPO)

    # sample_layout = models.CharField('sample_layout', max_length=200)

    def get_absolute_url(self):
        return reverse()

    def __str__(self):
        return self.item_type

#could be substitute for quotation request
class ClientPO(models.Model):
    date_issued = models.DateField('date_issued')
    date_required = models.DateField('date_required')
    terms = models.CharField('name', max_length=250)
    other_info = models.CharField('other_info', max_length=250)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    client_items = models.ManyToManyField(ClientItem)
    total_amount = models.DecimalField('total_amount', default=0, decimal_places=3, max_digits=12)
    laminate = models.BooleanField('laminate', default=0)
    confirmed = models.BooleanField('confirmed', default=0)

    def po_number(self):
        return 'PO%s' % (self.id)

    def __str__(self):
        return self.po_number()

    '''
    

    def passes_MOQ(self)

    def get_absolute_url(self):
        return reverse('sales')
    '''

# class CostingSheet(models.Model)

class ClientCreditStatus(models.Model):
    class Meta:
        verbose_name_plural = "Client credit status"
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    credit_status = models.BooleanField('credit_status', default=True)

class Supplier(models.Model):
    DEPARTMENT = (
        ('AF', 'Accounting and Finance'),
        ('HR', 'Human Resource'),
        ('IT', 'Information Technology'),
        ('M', 'Marketing'),
        ('P', 'Purchasing'),
        ('RD', 'Research and Development'),
        ('S', 'Sales'),
        ('O', 'Others'),

    )

    SUPPLIERTYPE = (
        ('RM', 'Raw Material'),
        ('MP', 'Machinery/Parts'),
        ('I', 'Ink'),
        ('O', 'Others'),

    )

    company_name = models.CharField('company_name', max_length=200)
    contact_person = models.CharField('contact_person', max_length=200)
    mobile_number = models.CharField('mobile_number', max_length=11)
    email_address = models.CharField('email_address', max_length=200)
    description = models.CharField('description', max_length=200, blank =True)
    supplier_type = models.CharField('suppier_type', choices=SUPPLIERTYPE, max_length=200, default='not specified')
    department = models.CharField('department', choices=DEPARTMENT, max_length=200, default='not specified')

    def __str__(self):
        return self.company_name    
