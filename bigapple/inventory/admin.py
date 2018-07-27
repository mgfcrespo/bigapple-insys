from django.contrib import admin

# Register your models here.
from .models import Inventory, InventoryCountAsof, SupplierPOItems, SupplierPO, SupplierRawMaterials
from .models import MaterialRequisition, MaterialRequisitionItems, PurchaseRequisition, PurchaseRequisitionItems

admin.site.register(SupplierPO)
admin.site.register(SupplierPOItems)
admin.site.register(Inventory)
admin.site.register(InventoryCountAsof)
admin.site.register(MaterialRequisition)
admin.site.register(MaterialRequisitionItems)
admin.site.register(PurchaseRequisition)
admin.site.register(PurchaseRequisitionItems)
admin.site.register(SupplierRawMaterials)
