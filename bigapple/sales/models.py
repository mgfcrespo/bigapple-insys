from django.db import models
from django.forms import ModelForm, BaseModelFormSet
from datetime import date
from django.urls import reverse
from accounts.models import Client
from decimal import Decimal

# Create your models here.

class Product(models.Model):
    products = models.CharField('products', max_length=200)
    prod_price = models.DecimalField('prod_price', decimal_places=3, max_digits=12, default=0)
    description = models.CharField('description', max_length=200)

    def __str__(self):
        return self.products

#could be substitute for quotation request
class ClientPO(models.Model):
    date_issued = models.DateTimeField('date_issued', auto_now_add=True, blank=True)
    date_required = models.DateTimeField('date_required')
    terms = models.CharField('name', max_length=250)
    other_info = models.CharField('other_info', max_length=250)
    clients = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    #client_items = models.ManyToManyField(ClientItem)
    total_amount = models.DecimalField('total_amount', default=0, decimal_places=3, max_digits=12)

    def po_number(self):
        return 'PO%s' % (self.id)

    def __str__(self):
        return self.po_number()

    '''
    def passes_MOQ(self)

    def get_absolute_url(self):
        return reverse('sales')
    '''


class ClientItem(models.Model):
    clients = models.ForeignKey(Client, on_delete=models.CASCADE, null=True) #to allow item suggestions suggestions
    products = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    note = models.CharField('note', max_length=200, default ='')
    width = models.DecimalField('width', decimal_places=3, max_digits=12)
    length = models.DecimalField('length', decimal_places=3, max_digits=12)
    color = models.CharField('color', max_length=200)
    gusset = models.DecimalField('gusset', decimal_places=3, max_digits=12)
    quantity = models.IntegerField('quantity')
    item_price = models.DecimalField('price', decimal_places=3, max_digits=12, default=0)
    client_po = models.ManyToManyField(ClientPO)

    # sample_layout = models.CharField('sample_layout', max_length=200)

    def get_absolute_url(self):
        return reverse('accounts:user-page-view')

    def __str__(self):
        return self.item_type

    def calculate_item_total(self):
        total = Decimal('0.0')
        total += (self.products.prod_price * self.quantity)
        return total

    def save(self, *args, **kwargs):
        self.item_price = self.calculate_item_total()
        super(ClientItem, self).save(*args, **kwargs)

'''
class Quotation(models.Model):
    client_po = models.OnetoOne(CustomerPO)
    approval = models.BooleanField('approval', default=False)
    #bom = models.ForeignKey()

class OrderSheet(models.Model):
    client_po = models.OnetoOneField(ClientPO, on_delete=models.CASCADE, null=True)
    #schedule of production?
    production_is_done = model.BooleanField('production_is_done', default=False)
'''

# class CostingSheet(models.Model)

class ClientCreditStatus(models.Model):
    clients = models.ForeignKey(Client, on_delete=models.CASCADE)
    credit_status = models.BooleanField('credit_status', default=True)
