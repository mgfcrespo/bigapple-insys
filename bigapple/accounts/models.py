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

    # age = models.IntegerField('age')
    first_name = models.CharField('first_name', max_length=200)
    last_name = models.CharField('last_name', max_length=200)
    birth_date = models.DateField('birth_date')
    address = models.CharField('address', max_length=200, blank =True)
    email = models.CharField('email', max_length=200, blank =True)
    contact_number = models.CharField('contact_number', max_length=200, blank =True)
    sss = models.CharField('sss', max_length=200, blank =True)
    philhealth = models.CharField('philhealth', max_length=200, blank =True)
    pagibig = models.CharField('pagibig', max_length=200, blank =True)
    tin = models.CharField('tin', max_length=200, blank=True)
    position = models.CharField('position', choices=POSITION, max_length=200, default='not specified')
    accounts = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank = True)

    @property
    def full_name(self):
        "Returns the person's full name."
        return '%s %s' % (self.first_name, self.last_name)

    @property
    def age(self):
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

    def __str__(self):
        return self.full_name
'''
    @property
    def is_production_worker(self):
        return if (position == )
'''


class Client(models.Model):
    first_name = models.CharField('first_name', max_length=200, default='')
    last_name = models.CharField('last_name', max_length=200, default='')
    company = models.CharField('company', max_length=200)
    address = models.CharField('address', max_length=200, blank =True)
    email = models.CharField('email', max_length=200, blank =True)
    contact_number = models.CharField('contact_number', max_length=200, blank =True)
    tin = models.CharField('tin', max_length=200, blank=True)
    accounts = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    sales_agent = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True)

    @property
    def full_name(self):
        "Returns the person's full name."
        return '%s %s' % (self.first_name, self.last_name)

    def __str__(self):
        return self.full_name


