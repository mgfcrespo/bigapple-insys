from django.db import models
from django.forms import ModelForm, BaseModelFormSet

from datetime import date, datetime

from django.urls import reverse
from accounts.models import Client
from decimal import Decimal
from django.db.models.aggregates import Sum
from django.db.models import aggregates
from django.db.models import Prefetch

from datetime import datetime, date
from datetime import timedelta

#TODO: Generate object at Client creation
class ClientConstant(models.Model):
    PAYMENT_TERMS = (
        ('30 Days', '30 Days'),
        ('45 Days', '45 Days'),
        ('60 Days', '60 Days'),
        ('90 Days', '90 Days')
    )

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    payment_terms = models.CharField('payment terms', choices=PAYMENT_TERMS, max_length=200, default="30 Days")
    discount = models.DecimalField('discount', decimal_places=2, max_digits=12, default=0)
    net_vat = models.DecimalField('net_vat', decimal_places=2, max_digits=12, default=.20)

    def __str__(self):
        return str(self.client)

#TODO: set prod_price to material cost
class Product(models.Model):
    RM_TYPES = (
        ('LLDPE', 'Linear low-density polyethylene'),
        ('LDPE', 'Low-density polyethylene'),
        ('HDPE', 'High-density polyethylene'),
        ('PP', 'Polypropylene'),
        ('PET', 'Polyethylene terephthalate')
    )
    
    material_type = models.CharField('rm_type', choices=RM_TYPES, max_length=200, null=True, blank=True)
    products = models.CharField('products', max_length=300)
    prod_price = models.DecimalField('prod_price', decimal_places=2, max_digits=12, default=0)
    constant = models.DecimalField('constant', decimal_places=2, max_digits=12, default=0)
    description = models.CharField('description', max_length=200)

    def __str__(self):
        return str(self.products)

    def save(self, *args, **kwargs):
        if self.products == "HDPE":
            self.constant = 31
        else:
            self.constant = 30
        super(Product, self).save(*args, **kwargs)

#TODO: Add Lamination as production cost
class ProductionCost(models.Model):
    cost_type = models.CharField('cost_type', max_length=200)
    cost = models.DecimalField('cost', decimal_places=2, max_digits=12, default=0)

    def __str__(self):
        return str(self.cost_type)

#TODO: Rush order determinant, materials requirement determinant- basically FEASIBILITY DETERMINANT for pre-confirm
class ClientPO(models.Model):

    STATUS =(
        ('Waiting', 'Waiting'),
        ('Approved', 'Approved'),
        ('Under production', 'Under production'),
        ('Ready for delivery', 'Ready for delivery'),
        ('Cancelled', 'Cancelled'),
        ('Disapproved', 'Disapproved')
    )

    date_issued = models.DateField('date_issued', auto_now_add=True)
    date_required = models.DateField('date_required', blank=False)
    other_info = models.TextField('other_info', max_length=250, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    total_amount = models.DecimalField('total_amount', default=0, decimal_places=2, max_digits=12)
    status = models.CharField('status', choices=STATUS, default='Waiting', max_length=200)
    rush_order = models.BooleanField('rush_order', default=False)

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        po_number = 'PO #%s' % (lead_zero)
        return str(po_number)


    def calculate_leadtime(self):
        date1 = date.today()
        date2 = self.date_required
        days = (date2 - date1).days
        return days

    def rush_order_determinant(self):
        if self.calculate_leadtime() <= 12:
            self.rush_order = True
        else:
            self.rush_order = False

        return self.rush_order

    def save(self, *args, **kwargs):
        rush_order = self.rush_order_determinant()
        self.rush_order = rush_order
        super(ClientItem, self).save(*args, **kwargs)

class ClientItem(models.Model):
    COLOR = (
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
        ('None', 'None'),
        ('Side Seal', 'Side Seal'),
        ('Bottom Seal Double', 'Bottom Seal Double'),
        ('Big Bottom Seal', 'Big Bottom Seal'),
        ('Bottom Seal Single', 'Bottom Seal Single'),
    )

    products = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, default=1, related_name='products')
    laminate = models.BooleanField('laminate', default=True)
    printed = models.BooleanField('printed', default=True)
    color_quantity = models.IntegerField('color_quantity', blank=True, default=0, null=True)
    width = models.DecimalField('width', decimal_places=2, max_digits=12, blank=False)
    length = models.DecimalField('length', decimal_places=2, max_digits=12, blank=False)
    thickness = models.DecimalField('thickness', decimal_places=3, max_digits=12, blank=False)
    color = models.CharField('color', choices=COLOR, max_length=200, blank=False, default='Plain')
    gusset = models.CharField('gusset', choices=GUSSET, default='None', max_length=200)
    quantity = models.IntegerField('quantity', blank=False)
    item_price = models.DecimalField('item_price', decimal_places=2, max_digits=12, default=0)
    price_per_piece = models.DecimalField('price_per_piece', decimal_places=2, max_digits=12, default=0)
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE, null=True, related_name='client_po')

    # sample_layout = models.CharField('sample_layout', max_length=200)

    def __str__(self):
        return str(self.id)

    def calculate_price_per_piece(self):
        #Set Production Costs
        electricity = ProductionCost.objects.get(cost_type = 'Electricity')
        mark_up = ProductionCost.objects.get(cost_type='Mark_up')
        ink = ProductionCost.objects.get(cost_type='Ink')
        cylinder = ProductionCost.objects.get(cost_type='Cylinder')
        art_labor = ProductionCost.objects.get(cost_type='Art_labor')
        art_work = ProductionCost.objects.get(cost_type='Artwork')
        lamination = ProductionCost.objects.get(cost_type='Lamination')

        #Set Constants based on Product picked by client
        material_weight = 0
        material_cost = 0
        if self.products == "HDPE":
            material_weight = 68
            material_cost = ProductionCost.objects.get(cost_type="HDPE_Materials")
        elif self.products == "LDPE":
            material_weight = 66
            material_cost = ProductionCost.objects.get(cost_type="LDPE_Materials")
        else:
            material_weight = 66
            material_cost = ProductionCost.objects.get(cost_type="PP_Materials")

        #Get the tens of order quantity (Sets quantity standard qty if order is below MOQ)
        order_qty = self.quantity / 1000
        if order_qty < 10:
            order_qty = 10

        order_qty = Decimal(order_qty)
        #Set printing cost (if viable)
        printing_cost = 0
        lamination_cost = 0
        if self.printed == True:
            printing_cost += (art_work.cost * self.color_quantity) + \
                         (art_labor.cost/order_qty) + (cylinder.cost/order_qty) + (ink.cost/order_qty)

        if self.laminate == True:
            lamination_cost += lamination.cost/order_qty

        price_per_piece = Decimal('0.0')
        #Calculate total per item
        price_per_piece += (self.length * self.width * self.thickness * material_weight * \
                 (material_cost.cost + (material_cost.cost * mark_up.cost) + (material_cost.cost * electricity.cost)) \
                     + order_qty + printing_cost + lamination_cost)/1000

        return price_per_piece

    def save(self, *args, **kwargs):
        if self.products is not None:
            price_per_piece = self.calculate_price_per_piece()
            self.price_per_piece = price_per_piece
            self.item_price = price_per_piece * self.quantity
        else:
            self.item_price = Decimal(0.0)
            self.price_per_piece = Decimal(0.0)
        super(ClientItem, self).save(*args, **kwargs)

        '''
    def calculate_materials_requirement(self):
        
        '''



class SalesInvoice(models.Model):
    PAYMENT_TERMS = (
        ('30 Days', '30 Days'),
        ('45 Days', '45 Days'),
        ('60 Days', '60 Days'),
        ('90 Days', '90 Days')
    )

    STATUS = (
        ('Open', 'Open'),
        ('Closed', 'Closed'),
        ('Late', 'Late'),
        ('Cancelled', 'Cancelled'),
    )

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='client')
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE, related_name='client_po')
    date_issued = models.DateField('date_issued', auto_now_add=True, blank=True)
    date_due = models.DateField('date_due', auto_now_add=True, blank=True)
    total_amount = models.DecimalField('total_amount', blank=True, decimal_places=2,
                                       max_digits=12)  # before discount and net_vat
    total_amount_computed = models.DecimalField('total_amount_computed', blank=True, decimal_places=2,
                                                max_digits=12)  # after discount and net_vat
    discount = models.DecimalField('discount', decimal_places=2, max_digits=12, default=0)
    net_vat = models.DecimalField('net_vat', decimal_places=2, max_digits=12, default=0)
    amount_due = models.DecimalField('amount_due', blank=True, decimal_places=2,
                                     max_digits=12)  # (self.total_amount * self.discount * self.net_vat)
    status = models.CharField('status', choices=STATUS, max_length=200, default="Open")
    payment_terms = models.CharField('payment terms', choices=PAYMENT_TERMS, max_length=200, default="30 Days")
    days_passed = models.IntegerField('days_passed', default=0)
    total_paid = models.DecimalField('total_paid', blank=True, decimal_places=3, max_digits=12, default=0)

    def __str__(self):
        # lead_zero = str(self.client_po).zfill(5)
        # po_number = 'PO# %s' % (lead_zero)
        po_number = self.client_po
        return str(po_number)


    def calculate_total_amount_computed(self):
        total_discount = self.total_amount * self.discount
        total_net_vat =  self.total_amount * self.net_vat
        total = self.total_amount + total_net_vat - total_discount
        return total

    def calculate_days_passed(self):
        start_date = self.date_due
        end_date = date.today()
        days = start_date - end_date
        return days

    def calculate_date_due(self):
        if self.payment_terms == "45 Days":
            add_days = 45
        elif self.payment_terms == "60 Days":
            add_days = 60
        elif self.payment_terms == "90 Days":
            add_days = 90
        else:
            add_days = 30

        date_due = self.date_issued + timedelta(days=add_days)
        return date_due

    def save(self, *args, **kwargs):
        client_constants = ClientConstant.objects.get(client=self.client)
        self.payment_terms = client_constants.payment_terms
        self.discount = client_constants.discount
        self.net_vat = client_constants.net_vat
        self.total_amount_computed = self.calculate_total_amount_computed()
        self.date_due = self.calculate_date_due()
        self.days_passed = self.calculate_days_passed()


        super(SalesInvoice, self).save(*args, **kwargs)


class ClientCreditStatus(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    status = models.BooleanField('status', default=False)
    outstanding_balance = models.DecimalField('outstanding_balance', decimal_places=2, max_digits=12,
                                              default=Decimal(0))  # accumulation of ClientPayment.balance
    overdue_balance = models.DecimalField('overdue_balance', decimal_places=2, max_digits=12,
                                          default=Decimal(0))  # sum of payments not made within payment terms
    remarks = models.CharField('remarks', max_length=500)

    def __str__(self):
        return str('Credit Status: %s' % (self.client))

    # TODO: get days overdue OF ANY SI NA OVERDUE
    def calculate_days_overdue(self):
        sales_invoice = SalesInvoice.objects.filter(client = self.client)
        overdue_sales_invoice = sales_invoice.get(SalesInvoice.status == 'Late')

        issued_date = overdue_sales_invoice.date_issued

        return (issued_date - date.today()).days

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
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, related_name='client')
    invoice_issued = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE, null=True, related_name='invoice_issued')
    payment = models.DecimalField('payment', decimal_places=2, max_digits=12,
                                  default=Decimal(0))  # how much the user paid per invoice
    payment_date = models.DateField('payment_date', blank=True)
    credit_status = models.ForeignKey(ClientCreditStatus, on_delete=models.CASCADE, null=True, related_name='credit_status')
    old_balance = models.DecimalField('old_balance', decimal_places=2, max_digits=12, default=Decimal(0))
    new_balance = models.DecimalField('new_balance', decimal_places=2, max_digits=12, default=Decimal(0))

    def __str__(self):
        return str(self.id)


class PO_Status_History(models.Model):
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    date_changed = models.DateTimeField('date_changed', auto_now_add=True, blank=True)


class Supplier(models.Model):
    company_name = models.CharField('company_name', max_length=200)
    first_name = models.CharField('first_name', max_length=200)
    last_name = models.CharField('last_name', max_length=200)
    mobile_number = models.CharField('mobile_number', max_length=11)
    email_address = models.CharField('email_address', max_length=200)
    description = models.CharField('description', max_length=200, blank=True)

    def contact_person(self):
        return self.last_name + ", " + str(self.first_name)

    def __str__(self):
        return self.company_name
