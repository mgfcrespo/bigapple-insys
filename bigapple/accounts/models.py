from django.db import models
from datetime import date


# Create your models here.

class Account(models.Model):
    username = models.CharField('username', max_length=200)
    password = models.CharField('password', max_length=200)


class Address(models.Model):
    address = models.CharField('address', max_length=200)


class ContactNumber(models.Model):
    contact_numbers = models.CharField('contact_numbers', max_length=200)


class Email(models.Model):
    emails = models.CharField('emails', max_length=200)


class Employee(models.Model):
    POSITION = (
        ('GM', 'General Manager'),
        ('SC', 'Sales Coordinator'),
        ('SA', 'Sales Agent'),
        ('CC', 'Credits and Collection Personnel'),
        ('SV', 'Supervisor'),
        ('LL', 'Line Leader'),
        ('PM', 'Production Manager'),
        ('C', 'Cutting'),
        ('P', 'Printing'),
        ('E', 'Extruder'),
        ('D', 'Delivery'),
        ('W', 'Warehouse'),
        ('U', 'Utility'),
        ('M', 'Maintenance')
        ('PM', 'Production Manager')

    )

    # age = models.IntegerField('age')
    first_name = models.CharField('first_name', max_length=200)
    last_name = models.CharField('last_name', max_length=200)
    birth_date = models.DateField('birth_date')
    address = models.ForeignKey(Address, on_delete = models.CASCADE)
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    contact_number = models.ForeignKey(ContactNumber, on_delete=models.CASCADE)
    sss = models.CharField('sss', max_length=200, blank =True)
    philhealth = models.CharField('philhealth', max_length=200, blank =True)
    pagibig = models.CharField('pagibig', max_length=200, blank =True)
    tin = models.CharField('tin', max_length=200, blank=True)
    position = models.CharField('position', choices=POSITION, max_length=200, default='not specified')
    accounts = models.OneToOneField(Account, on_delete=models.CASCADE, null=True)

    @property
    def full_name(self):
        "Returns the person's full name."
        return '%s %s' % (self.first_name, self.last_name)

    @property
    def age(self):
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

'''
    @property
    def is_production_worker(self):
        return if (position == )
'''


class Client(models.Model):
    first_name = models.CharField('first_name', max_length=200, default='not_specified')
    last_name = models.CharField('last_name', max_length=200, default='not_specified')
    company = models.CharField('company', max_length=200)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    contact_number = models.ForeignKey(ContactNumber, on_delete=models.CASCADE)
    tin = models.CharField('tin', max_length=200, blank=True)
    accounts = models.OneToOneField(Account, on_delete=models.CASCADE)


    @property
    def full_name(self):
        "Returns the person's full name."
        return '%s %s' % (self.first_name, self.last_name)

class ClientOrders(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    order_id = models.CharField('order_id', min_length=10)




