from django.contrib import admin

# Register your models here.
from .models import Inventory, InventoryCountAsof, SupplierItems

admin.site.register(SupplierItems)
admin.site.register(Inventory)
admin.site.register(InventoryCountAsof)
