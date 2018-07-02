from django.contrib import admin

# Register your models here.
from .models import Inventory, InventoryCountAsof, SupplierItems, MaterialRequisition

admin.site.register(SupplierItems)
admin.site.register(Inventory)
admin.site.register(InventoryCountAsof)
admin.site.register(MaterialRequisition)
