from django.contrib import admin

from .models import Supplier, Product, ClientPO, ClientItem, ClientCreditStatus, SalesInvoice, ClientConstant, ProductionCost
from production.models import JobOrder, CuttingSchedule, PrintingSchedule, ExtruderSchedule, Machine
# Register your models here.

admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(ClientPO)
admin.site.register(ClientItem)
admin.site.register(ClientCreditStatus)
admin.site.register(SalesInvoice)
admin.site.register(ClientConstant)
admin.site.register(ProductionCost)

#production
admin.site.register(Machine)
admin.site.register(JobOrder)
admin.site.register(CuttingSchedule)
admin.site.register(PrintingSchedule)
admin.site.register(ExtruderSchedule)