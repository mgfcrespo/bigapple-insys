from django.contrib import admin

# Register your models here.
from .models import Inventory, SupplierPOItems, SupplierPO
from .models import MaterialRequisition

admin.site.register(SupplierPO)
admin.site.register(SupplierPOItems)
admin.site.register(Inventory)
admin.site.register(MaterialRequisition)