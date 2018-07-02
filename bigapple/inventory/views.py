from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .models import Supplier
from .models import SupplierItems, SupplierPO, SupplierPOTracking, MaterialRequisition
from .models import PurchaseRequisition, Inventory, InventoryCountAsof
from .forms import SupplierItemsForm


# Create your views here.
def supplier_rm_add(request):
    form = SupplierItemsForm(request.POST)
    supplier = Supplier.objects.all()
    if request.method == 'POST':
        HttpResponse(print(form.errors))
        if form.is_valid():
            form.save()
            return redirect('sales:supplier_item_list')

    context = {
        'supplier' : supplier,
        'form' : form,
        'title': 'Add Supplier Raw Material',
        'actiontype': 'Submit'
    }

    return render(request, 'inventory/supplier_rm_add.html', context)

def supplier_item_list(request):
    items = SupplierItems.objects.all()
    context = {
        'items' : items 
    }
    return render (request, 'inventory/supplier_item_list.html', context)

def supplier_item_edit(request, id):
    items = SupplierItems.objects.get(id=id)
    form = SupplierItemsForm(request.POST or None, instance=items)

    if form.is_valid():
        form.save()
        return redirect('inventory/supplier_item_list.html')
    
    context = {
        'form' : form,
        'items' : items,
        'title' : "Edit Supplier",
        'actiontype' : "Submit",
    }
    return render(request, 'inventory/supplier_rm_add.html', context)

def supplier_item_delete(request, id):
    items = SupplierItems.objects.get(id=id)
    items.delete()
    return HttpResponseRedirect('../supplier_item_list')