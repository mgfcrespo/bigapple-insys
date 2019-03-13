from django.db import models
from django.forms import ModelForm, BaseModelFormSet

from datetime import date, datetime

from django.urls import reverse
from traitlets import Float

from accounts.models import Client
from decimal import Decimal
from django.db.models.aggregates import Sum
from django.db.models import aggregates
from django.db.models import Prefetch
from production.models import JobOrder
# from django.apps import apps
# JobOrder = apps.get_model('production', 'JobOrder')

from datetime import datetime, date
from datetime import timedelta

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
    prod_price = models.FloatField()
    constant = models.FloatField()
    description = models.CharField('description', max_length=200)

    def __str__(self):
        return str(self.products)

    def save(self, *args, **kwargs):
        if self.products == "HDPE":
            self.constant = 31
        else:
            self.constant = 30
        super(Product, self).save(*args, **kwargs)

    class Meta:
        db_table = 'sales_mgt_product'


class ProductionCost(models.Model):
    id = models.IntegerField(primary_key=True)
    cost_type = models.CharField(max_length=45)
    cost = models.FloatField()

    def __str__(self):
        return str(self.cost_type)

    class Meta:
        db_table = 'sales_mgt_productioncost'


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

    laminate = models.IntegerField()
    printed = models.IntegerField()
    width = models.FloatField()
    length = models.FloatField()
    thickness = models.FloatField()
    quantity = models.IntegerField()
    item_price = models.FloatField()
    price_per_piece = models.FloatField()
    client_po = models.ForeignKey(JobOrder, on_delete=models.CASCADE)
    color = models.CharField('color', choices=COLOR, max_length=200, blank=False, default='Plain')
    gusset = models.CharField('gusset', choices=GUSSET, default='None', max_length=200)
    products = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        db_table = 'sales_mgt_clientitem'

    # sample_layout = models.CharField('sample_layout', max_length=200)

    def __str__(self):
        return str(self.id)

    def calculate_price_per_piece(self):
        # Set Production Costs
        electricity = ProductionCost.objects.get(cost_type='Electricity')
        mark_up = ProductionCost.objects.get(cost_type='Mark_up')
        ink = ProductionCost.objects.get(cost_type='Ink')
        cylinder = ProductionCost.objects.get(cost_type='Cylinder')
        art_labor = ProductionCost.objects.get(cost_type='Art_labor')
        art_work = ProductionCost.objects.get(cost_type='Artwork')
        lamination = ProductionCost.objects.get(cost_type='Lamination')

        # Set Constants based on Product picked by client
        material_weight = 0
        material_cost = 0
        if self.products == "HDPE":
            material_weight = 0.68
            material_cost = ProductionCost.objects.get(cost_type="HDPE_Materials")
        elif self.products == "LDPE":
            material_weight = 0.66
            material_cost = ProductionCost.objects.get(cost_type="LDPE_Materials")
        else:
            material_weight = 0.66
            material_cost = ProductionCost.objects.get(cost_type="PP_Materials")

        # Get the tens of order quantity (Sets quantity standard qty if order is below MOQ)
        order_qty = self.quantity / 1000
        if order_qty < 10:
            order_qty = 10

        # Set printing cost (if viable)
        printing_cost = 0
        lamination_cost = 0
        if self.printed == True:
            printing_cost += (art_work.cost) + \
                             (art_labor.cost / order_qty) + (cylinder.cost / order_qty) + (ink.cost / order_qty)
        else:
            printing_cost = 0

        if self.laminate == True:
            lamination_cost += lamination.cost / order_qty
        else:
            lamination_cost = 0

        price_per_piece = float(0.0)
        # Calculate total per item
        price_per_piece += ((self.length * self.width * self.thickness * material_weight) *
                            (material_cost.cost + mark_up.cost) +
                                (electricity.cost) + printing_cost + lamination_cost) / 1000

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

class SalesInvoice(models.Model):
    STATUS = (
        ('Open', 'Open'),
        ('Closed', 'Closed'),
        ('Late', 'Late'),
        ('Cancelled', 'Cancelled'),
    )

    date_issued = models.DateField(null=True, blank=True)
    date_due = models.DateField(null=True, blank=True)
    total_amount = models.FloatField()
    total_amount_computed = models.FloatField(null=True, blank=True)
    amount_due = models.FloatField()
    total_paid = models.FloatField(null=True, blank=True)
    days_passed = models.IntegerField(null=True, blank=True)
    days_overdue = models.IntegerField(null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    client_po = models.ForeignKey(JobOrder, on_delete=models.CASCADE)
    status = models.CharField('status', choices=STATUS, max_length=200, default="Open")

    class Meta:
        db_table = 'sales_mgt_salesinvoice'

    def __str__(self):
        # lead_zero = str(self.client_po).zfill(5)
        # po_number = 'PO# %s' % (lead_zero)
        po_number = self.client_po
        return str(po_number)

    def calculate_total_amount_computed(self):
        if self.client.discount is None:
            total_net_vat = (self.total_amount * self.client.net_vat)/100
            total = float(self.total_amount + total_net_vat)
        else:
            total_discount = self.total_amount * (self.client.discount/100)
            total_net_vat = (self.total_amount * self.client.net_vat)/100
            total = float(self.total_amount + total_net_vat - total_discount)
        return total

    def calculate_days_passed(self):
        start_date = self.date_due
        end_date = date.today()
        days = (start_date - end_date).days
        return days

    def calculate_date_due(self):
        if self.client.payment_terms == "45 Days":
            add_days = 45
        elif self.client.payment_terms == "60 Days":
            add_days = 60
        elif self.client.payment_terms == "90 Days":
            add_days = 90
        else:
            add_days = 30

        d = timedelta(days=add_days)
        date_due = self.date_issued + d
        return date_due

    def calculate_days_overdue(self):
        sales_invoice = SalesInvoice.objects.filter(client=self.client)
        overdue_sales_invoice = []
        for x in sales_invoice:
            if x.status == "Late":
                overdue_sales_invoice.append(x)

        overdue_sales_invoice = sales_invoice.order_by('date_issued')
        object = overdue_sales_invoice.first()
        issued_date = object.date_issued

        if issued_date is not None:
            diff = date.today() - issued_date
            return diff.days
        else:
            return 0

    def save(self, *args, **kwargs):
        client = self.client
        self.payment_terms = client.payment_terms
        self.discount = client.discount
        self.net_vat = client.net_vat
        self.total_amount_computed = self.calculate_total_amount_computed()
        if self.date_issued is not None:
            self.date_due = self.calculate_date_due()
            self.days_passed = self.calculate_days_passed()
            self.days_overdue = self.calculate_days_overdue()
            if self.days_passed <= 0:
                self.status == 'Late'
        else:
            self.date_due = None
            self.days_passed = None
            self.days_overdue = None
            self.date_issued = None
        super(SalesInvoice, self).save(*args, **kwargs)


class ClientPayment(models.Model):
    payment = models.FloatField()
    payment_date = models.DateField()
    old_balance = models.FloatField(null=True, blank=True)
    new_balance = models.FloatField(null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE)

    class Meta:
        db_table = 'sales_mgt_clientpayment'

    def __str__(self):
        return str(self.id)

    def save(self):
        self.old_balance = self.invoice.amount_due
        self.new_balance = self.old_balance - self.payment
        super(ClientPayment, self).save()


class Supplier(models.Model):
    company_name = models.CharField(max_length=45)
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    mobile_number = models.CharField(max_length=45)
    email_address = models.CharField(max_length=45)
    description = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        db_table = 'sales_mgt_supplier'

    def contact_person(self):
        return self.last_name + ", " + str(self.first_name)

    def __str__(self):
        return self.company_name
