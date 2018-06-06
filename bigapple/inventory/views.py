from django.http import HttpResponse
from django.shortcuts import render

from .models import Supplier
from .models import SupplierItems
from .models import SupplierPO
from .models import SupplierPOTracking
from .models import MaterialRequisition
from .models import PurchaseRequisition
from .models import Inventory
from .models import InventoryCountAsof

# Create your views here.
def inventory_details(request):
    context = {
        'title': 'Inventory Content'
    }

    return render(request, 'inventory/inventory_details.html', context)
