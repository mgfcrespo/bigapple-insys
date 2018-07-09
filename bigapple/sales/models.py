from django.db import models
from django.forms import ModelForm, BaseModelFormSet
from datetime import date
from django.urls import reverse
from accounts.models import Client
from decimal import Decimal
from datetime import date
from django.db.models.aggregates import Sum
from django.db.models import Prefetch
# Create your models here.

class Product(models.Model):
    products = models.CharField('products', max_length=200)
    prod_price = models.DecimalField('prod_price', decimal_places=3, max_digits=12, default=0)
    description = models.CharField('description', max_length=200)

    def __str__(self):
        return self.products + " : Php." + str(self.prod_price) + "/piece"



#could be substitute for quotation request
class ClientPO(models.Model):
    PAYMENT_TERMS = (
        ('15 Days', '15 Days'),
        ('30 Days', '30 Days'),
        ('60 Days', '60 Days'),
        ('90 Days', '90 Days')
    )

    STATUS =(
        ('waiting', 'waiting'),
        ('approved', 'approved'),
        ('under production', 'under production'),
        ('ready for delivery', 'ready for delivery'),
        ('disapproved', 'disapproved')

    )

    date_issued = models.DateTimeField('date_issued', auto_now_add=True, blank=True)
    date_required = models.DateField('date_required')
    payment_terms = models.CharField('payment terms',  choices=PAYMENT_TERMS, max_length=200, default="30")
    other_info = models.TextField('other_info', max_length=250)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    total_amount = models.DecimalField('total_amount', default=0, decimal_places=3, max_digits=12)
    status = models.CharField('status', choices=STATUS, default='waiting', max_length=200)

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        po_number = 'PO_%s' % (lead_zero)
        return po_number

    '''
    def calculate_leadtime(self):
        date_format = "%m/%d/%y"
        date1 = datetime.strptime(self.date_issued, date_format)
        date2 = datetime.strptime(self.date_required, date_format)
        return date2 - date1
    '''


class ClientItem(models.Model):

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

    products = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    laminate = models.BooleanField('laminate', default=True)
    width = models.DecimalField('width', decimal_places=3, max_digits=12)
    length = models.DecimalField('length', decimal_places=3, max_digits=12)
    color = models.CharField('color', choices=COLOR, max_length=200)
    gusset = models.DecimalField('gusset', decimal_places=3, max_digits=12)
    quantity = models.IntegerField('quantity')
    item_price = models.DecimalField('price', decimal_places=3, max_digits=12, default=0)
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE, null=True)
    # sample_layout = models.CharField('sample_layout', max_length=200)

    '''
    def get_absolute_url(self):
        return reverse('accounts:user-page-view')
    '''

    def __str__(self):
        return self.id


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
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    date_issued = models.DateField('date_issued', auto_now_add=True, blank=True)
    total_amount = models.DecimalField('total_amount', blank=True, decimal_places=3, max_digits=12)#before discount and net_vat
    discount = models.DecimalField('discount', decimal_places=3, max_digits=12, default=0)
    net_vat = models.DecimalField('net_vat', decimal_places=3, max_digits=12, default=0)
    amount_due = models.DecimalField('amount_due', blank=True, decimal_places=3, max_digits=12)#(self.total_amount * self.discount * self.net_vat)

    def __str__(self):
        return 'PO_%s' % (self.id)

    def calculate_amount_due(self):
        total = (self.total_amount * self.discount * self.net_vat)
        return total

    def save(self, *args, **kwargs):
        if self.discount == 0:
            self.discount = 1
        if self.net_vat == 0:
            self.net_vat = 1

        self.amount_due = self.calculate_amount_due()
        super(SalesInvoice, self).save(*args, **kwargs)

class ClientCreditStatus(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    status = models.BooleanField('laminate', default=False)
    outstanding_balance = models.DecimalField('outstanding_balance', decimal_places=3, max_digits=12) #accumulation of ClientPayment.balance

    def __str__(self):
        return self.id


    def calculate_outstanding_balance(self):
        client_payment = ClientPayment.objects.all()#edit this to filter by client
        total = client_payment.aggregate(Sum('balance'))
        return total

    def save(self, *args, **kwargs):
        self.outstanding_balance = self.calculate_outstanding_balance()
        super(ClientCreditStatus, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Client credit status"

class ClientPayment(models.Model):
    invoice_issued = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE)
    date_due = models.DateField('date_due', auto_now_add=True, blank=True)
    total_paid = models.DecimalField('total_paid', decimal_places=3, max_digits=12) #how much the user paid per invoice
    balance =  models.DecimalField('balance', decimal_places=3, max_digits=12) #total_paid - SalesInvoice.amount_due (can be negative)
    credit_status = models.ForeignKey(ClientCreditStatus, on_delete=models.CASCADE)

    def __str__(self):
        return self.id

    def calculate_balance(self):
        total = (self.total_paid - self.invoice_issued.amount_due)
        return total

    def save(self, *args, **kwargs):
        self.balance = self.calculate_balance()
        super(ClientPayment, self).save(*args, **kwargs)

class Supplier(models.Model):

    SUPPLIERTYPE = (
        ('Raw Material', 'Raw Material'),
        ('Machinery/Parts', 'Machinery/Parts'),
        ('Ink', 'Ink'),
        ('Others', 'Others'),
    )

    company_name = models.CharField('company_name', max_length=200)
    contact_person = models.CharField('contact_person', max_length=200)
    mobile_number = models.CharField('mobile_number', max_length=11)
    email_address = models.CharField('email_address', max_length=200)
    description = models.CharField('description', max_length=200, blank =True)
    supplier_type = models.CharField('suppier_type', max_length=200, default='not specified', choices=SUPPLIERTYPE)
    
    def __str__(self):
        return self.company_name
