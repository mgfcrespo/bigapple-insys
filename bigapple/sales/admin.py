from django.contrib import admin

from .models import Supplier, Product, ClientItem, SalesInvoice, ProductionCost
# Register your models here.

admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(ClientItem)
admin.site.register(SalesInvoice)
admin.site.register(ProductionCost)
