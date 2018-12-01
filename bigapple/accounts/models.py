from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.conf import settings


# Create your models here.

class Employee(models.Model):
    POSITION = (
        ('General Manager', 'General Manager'),
        ('Sales Coordinator', 'Sales Coordinator'),
        ('Sales Agent', 'Sales Agent'),
        ('Credits and Collection Personnel', 'Credits and Collection Personnel'),
        ('Supervisor', 'Supervisor'),
        ('Line Leader', 'Line Leader'),
        ('Production Manager', 'Production Manager'),
        ('Cutting', 'Cutting'),
        ('Printing', 'Printing'),
        ('Extruder', 'Extruder'),
        ('Delivery', 'Delivery'),
        ('Warehouse', 'Warehouse'),
        ('Utility', 'Utility'),
        ('Maintenance', 'Maintenance'),

    )

    id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    address = models.CharField(max_length=45)
    email = models.CharField(max_length=45)
    contact_number = models.CharField(max_length=45)
    sss = models.CharField(max_length=45)
    philhealth = models.CharField(max_length=45)
    pagibig = models.CharField(max_length=45)
    tin = models.CharField(max_length=45)
    position = models.CharField('position', choices=POSITION, max_length=200, default='not specified')
    accounts = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank = True)


    class Meta:
        db_table = 'accounts_mgt_employee'

    @property
    def full_name(self):
        "Returns the person's full name."
        return '%s %s' % (self.first_name, self.last_name)

    def __str__(self):
        return self.full_name

'''
    @property
    def is_production_worker(self):
        return if (position == 
'''

class Client(models.Model):
    id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    company = models.CharField(max_length=45)
    address = models.CharField(max_length=45)
    email = models.CharField(max_length=45)
    contact_number = models.CharField(max_length=45)
    tin = models.CharField(max_length=45)
    sales_agent = models.ForeignKey(Employee, on_delete=models.CASCADE)
    payment_terms = models.CharField(max_length=45)
    discount = models.FloatField(blank=True, null=True)
    net_vat = models.FloatField()
    credit_status = models.IntegerField()
    outstanding_balance = models.FloatField()
    overdue_balance = models.FloatField()
    remarks = models.CharField(max_length=45, blank=True, null=True)
    accounts = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = 'accounts_mgt_client'

    @property
    def full_name(self):
        "Returns the person's full name."
        return '%s %s' % (self.first_name, self.last_name)

    def __str__(self):
        return self.full_name

class AgentClientRel(models.Model):
    index = models.IntegerField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    class Meta:
        db_table = 'accounts_mgt_agentclientrel'


