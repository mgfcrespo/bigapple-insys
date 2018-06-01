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
        ('PM', 'Production Manager')
    )

    # age = models.IntegerField('age')
    first_name = models.CharField('first_name', max_length=200)
    last_name = models.CharField('last_name', max_length=200)
    middle_initial = models.CharField('middle_initial', max_length=5)
    birth_date = models.DateField('birth_date')
    address = models.ForeignKey(Address, on_delete = models.CASCADE)
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    contact_number = models.ForeignKey(ContactNumber, on_delete=models.CASCADE)
    position = models.CharField('position', choices=POSITION, max_length=200, default='not specified')
    accounts = models.OneToOneField(Account, on_delete=models.CASCADE)

    @property
    def full_name(self):
        "Returns the person's full name."
        return '%s %s %s' % (self.first_name, self.middle_initial, self.last_name)

    @property
    def age(self):
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

class Client(models.Model):
    contact_name = models.CharField('contact_name', max_length=200)
    company = models.CharField('company', max_length=200)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    contact_number = models.ForeignKey(ContactNumber, on_delete=models.CASCADE)
    accounts = models.OneToOneField(Account, on_delete=models.CASCADE)

class ClientOrders(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    order_id = models.CharField('order_id', min_length=10)



