from django.db import models
from datetime import date
from accounts.models import Client


# Create your models here.

class ClientItem(models.Model):
    item_type = models.CharField('item_type', max_length=200)
    description = models.CharField('description', max_length=200)
    width = models.IntegerField('width')
    length = models.IntegerField('length')
    color = models.CharField('color', max_length=200)
    gusset = models.CharField('gusset', max_length=200)
    quantity = models.IntegerField('quantity')
    price = models.IntegerField('price')


    # sample_layout = models.CharField('sample_layout', max_length=200)

    def __str__(self):
        return self.item_type

#could be substitute for quotation request
class ClientPO(models.Model):
    date_issued = models.DateField('date_issued')
    date_required = models.DateField('date_required')
    terms = models.CharField('name', max_length=250)
    other_info = models.CharField('other_info', max_length=250)
    clients = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    client_items = models.ManyToManyField(ClientItem)
    total_amount = models.IntegerField('total_amount')
    '''
    def po_number(self):
        return 'PO%s' % (self.)
        
    def passes_MOQ(self)
    '''

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