from django.contrib import admin

from .models import Client, Account, Address, Email, ContactNumber, Employee
# Register your models here.

admin.site.register(Client)
admin.site.register(Account)
admin.site.register(Address)
admin.site.register(Email)
admin.site.register(ContactNumber)
admin.site.register(Employee)