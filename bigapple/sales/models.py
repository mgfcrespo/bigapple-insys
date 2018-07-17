from django.db import models
from django.forms import ModelForm, BaseModelFormSet

from datetime import date, datetime

from django.urls import reverse
from accounts.models import Client
from decimal import Decimal
from django.db.models.aggregates import Sum
from django.db.models import aggregates
from django.db.models import Prefetch

from datetime import datetime as dt
from datetime import date as d


# Create your models here.


class Product(models.Model):
    products = models.CharField('products', max_length=200)
    prod_price = models.DecimalField('prod_price', decimal_places=2, max_digits=12, default=0)
    description = models.CharField('description', max_length=200)

    def __str__(self):
        return str(self.products)

class PreProduct(models.Model):
    GUSSET = (
        ('Side Seal', 'Side Seal'),
        ('Bottom Seal Double', 'Bottom Seal Double'),
        ('Big Bottom Seal', 'Big Bottom Seal'),
        ('Bottom Seal Single', 'Bottom Seal Single'),
    )

    products = models.CharField('products', max_length=200)
    width = models.DecimalField('width', decimal_places=2, max_digits=12, blank=False)
    length = models.DecimalField('length', decimal_places=2, max_digits=12, blank=False)
    gusset = models.CharField('gusset', choices=GUSSET, default='Side Seal', max_length=200)
    prod_price = models.DecimalField('prod_price', decimal_places=3, max_digits=12, default=0)
    description = models.CharField('description', max_length=200)

#could be substitute for quotation request
class ClientPO(models.Model):
    STATUS =(
        ('waiting', 'waiting'),
        ('approved', 'approved'),
        ('under production', 'under production'),
        ('ready for delivery', 'ready for delivery'),
        ('disapproved', 'disapproved')

    )

    date_issued = models.DateTimeField('date_issued', auto_now_add=True)
    date_required = models.DateField('date_required', blank=False)
    other_info = models.TextField('other_info', max_length=250, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    total_amount = models.DecimalField('total_amount', default=0, decimal_places=3, max_digits=12)
    status = models.CharField('status', choices=STATUS, default='waiting', max_length=200)

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        po_number = 'PO%s' % (lead_zero)
        return  str(po_number)



    '''
    def calculate_leadtime(self):
        date_format = "%m/%d/%y"
        date1 = datetime.strptime(self.date_issued, date_format)
        date2 = datetime.strptime(self.date_required, date_format)
        return date2 - date1
    '''


class ClientItem(models.Model):
    RM_TYPES = (
        ('LDPE', 'Low-density polyethylene'),
        ('LLDPE', 'Linear low-density polyethylene'),
        ('HDPE', 'High-density polyethylene'),
        ('PP', 'Polypropylene'),
        ('PET', 'Polyethylene terephthalate')
    )

    COLOR =(
        ('Red', 'Red'),
        ('Blue', 'Blue'),
        ('Yellow', 'Yellow'),
        ('Orange', 'Orange'),
        ('Green', 'Green'),
        ('Violet', 'Violet'),
        ('Black', 'Black'),
        ('White', 'White'),
        ('Plain', 'Plain')
    )

    GUSSET = (
        ('Side Seal', 'Side Seal'),
        ('Bottom Seal Double', 'Bottom Seal Double'),
        ('Big Bottom Seal', 'Big Bottom Seal'),
        ('Bottom Seal Single', 'Bottom Seal Single'),
    )

    products = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    material_type = models.CharField('material_type', choices=RM_TYPES, max_length=200, blank=False, default='LDPE')
    laminate = models.BooleanField('laminate', default=True)
    width = models.DecimalField('width', decimal_places=2, max_digits=12, blank=False)
    length = models.DecimalField('length', decimal_places=2, max_digits=12, blank=False)
    color = models.CharField('color', choices=COLOR, max_length=200, blank=False, default='Plain')
    gusset = models.CharField('gusset', choices=GUSSET, default='Side Seal', max_length=200)
    quantity = models.IntegerField('quantity', blank=False)
    item_price = models.DecimalField('price', decimal_places=2, max_digits=12, default=0)
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE, null=True)
    # sample_layout = models.CharField('sample_layout', max_length=200)


    def __str__(self):
        return str(self.id)

    def calculate_item_total(self):
        total = Decimal('0.0')
        total += (self.products.prod_price * self.quantity)
        return total

    def save(self, *args, **kwargs):
        if self.products is not None:
            self.item_price = self.calculate_item_total()
        else:
            self.item_price = Decimal(0.0)
        super(ClientItem, self).save(*args, **kwargs)


# class CostingSheet(models.Model)

class SalesInvoice(models.Model):
    PAYMENT_TERMS = (
        ('15 Days', '15 Days'),
        ('30 Days', '30 Days'),
        ('60 Days', '60 Days'),
        ('90 Days', '90 Days')
    )

    STATUS = (
        ('Open', 'Open'),
        ('Closed', 'Closed'),
        ('Late', 'Late'),
        ('Cancelled', 'Cancelled'),
    )

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    date_issued = models.DateTimeField('date_issued', auto_now_add=True, blank=True)
    total_amount = models.DecimalField('total_amount', blank=True, decimal_places=2, max_digits=12)#before discount and net_vat
    total_amount_computed = models.DecimalField('total_amount_computed', blank=True, decimal_places=2, max_digits=12)#after discount and net_vat
    discount = models.DecimalField('discount', decimal_places=2, max_digits=12, default=0)
    net_vat = models.DecimalField('net_vat', decimal_places=2, max_digits=12, default=0)
    amount_due = models.DecimalField('amount_due', blank=True, decimal_places=2, max_digits=12)#(self.total_amount * self.discount * self.net_vat)
    status =  models.CharField('status',  choices=STATUS, max_length=200, default="Open")
    payment_terms = models.CharField('payment terms',  choices=PAYMENT_TERMS, max_length=200, default="30 Days")
    days_passed = models.IntegerField('days_passed', default=0)
    total_paid = models.DecimalField('total_paid', blank=True, decimal_places=3, max_digits=12, default = 0)

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        po_number = 'PO%s' % (lead_zero)
        return  po_number

    def calculate_total_amount_computed(self):
        if self.discount == 0:
            discount = 1
        else:
            discount = self.discount
        if self.net_vat == 0:
            net_vat = 1
        else:
            net_vat = self.net_vat

        total = (self.total_amount * discount * net_vat)
        return total

    #TODO this function does not let the entire object be recorded, let alone actually compute  delta.days
    def calculate_days_passed(self):
        delta = dt.now().date() - self.date_issued
        return delta.days


    def save(self, *args, **kwargs):
        self.total_amount_computed = self.calculate_total_amount_computed()
        #self.days_passed= self.calculate_days_passed()
        super(SalesInvoice, self).save(*args, **kwargs)

class ClientCreditStatus(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE)
    status = models.BooleanField('status', default=False)
    outstanding_balance = models.DecimalField('outstanding_balance', decimal_places=2, max_digits=12, default=Decimal(0)) #accumulation of ClientPayment.balance
    overdue_balance = models.DecimalField('overdue_balance', decimal_places=2, max_digits=12, default=Decimal(0))# sum of payments not made within payment terms
    def __str__(self):
        return str('Credit Status: %s' % (self.client))

    '''
    def calculate_payments_sum(self):
        client_payment = ClientPayment.objects.filter(client_id = self.client)#filter by current client
        if not client_payment:
            total = 0
        else:
            total = client_payment.aggregate(sum=aggregates.Sum('balance'))['sum'] or 0
        return total

    
    def calculate_invoice_sum(self):
        client_invoice = SalesInvoice.objects.filter(cancelled = 0, client_id = self.client)
        total = client_invoice.aggregate(sum=aggregates.Sum('total_amount'))['sum'] or 0
        return total
       

    def save(self, *args, **kwargs):
        self.outstanding_balance = self.calculate_invoice_sum() - self.calculate_payments_sum()
        super(ClientCreditStatus, self).save(*args, **kwargs)
 '''

    class Meta:
        verbose_name_plural = "Client credit status"

class ClientPayment(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    invoice_issued = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE, null=True)
    payment = models.DecimalField('payment', decimal_places=2, max_digits=12, default=Decimal(0)) #how much the user paid per invoice
    payment_date = models.DateField('payment_date', blank=True)
    credit_status = models.ForeignKey(ClientCreditStatus, on_delete=models.CASCADE, null=True)
    old_balance = models.DecimalField('old_balance', decimal_places=2, max_digits=12, default=Decimal(0))
    new_balance = models.DecimalField('new_balance', decimal_places=2, max_digits=12, default=Decimal(0))

    def __str__(self):
        return str(self.id)


class PO_Status_History(models.Model):
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    date_changed =  models.DateTimeField('date_changed', auto_now_add=True, blank=True)


class Supplier(models.Model):
    company_name = models.CharField('company_name', max_length=200)
    first_name = models.CharField('first_name', max_length=200)
    last_name = models.CharField('last_name', max_length=200)
    mobile_number = models.CharField('mobile_number', max_length=11)
    email_address = models.CharField('email_address', max_length=200)
    description = models.CharField('description', max_length=200, blank =True)
    
    def contact_person(self):
        return self.last_name + ", " + str(self.first_name)

    def __str__(self):
        return self.company_name
