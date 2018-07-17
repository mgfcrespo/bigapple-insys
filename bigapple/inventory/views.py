from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory, inlineformset_factory
from django.db.models import aggregates

from .models import Supplier
from .models import SupplierPOItems, SupplierPO, SupplierPOTracking, MaterialRequisition, MaterialRequisitionItems
from .models import PurchaseRequisition, Inventory, InventoryCountAsof
from .forms import SupplierPOItemsForm, SupplierPOForm, MaterialRequisitionForm, InventoryForm, MaterialRequisitionItemsForm


# Create your views here.
# Inventory
def inventory_item_add(request):
    form = InventoryForm(request.POST)
    supplier = Supplier.objects.all()
    if request.method == 'POST':
        HttpResponse(print(form.errors))
        if form.is_valid():
            form.save()
            return redirect('inventory:inventory_item_list')

    context = {
        'supplier' : supplier,
        'form' : form,
        'title': 'Add Supplier Item',
        'actiontype': 'Submit'
    }

    return render(request, 'inventory/inventory_item_add.html', context)

def inventory_item_list(request):
    items = Inventory.objects.all()
    context = {
        'items' : items 
    }
    return render (request, 'inventory/inventory_item_list.html', context)

def inventory_item_edit(request, id):
    items = Inventory.objects.get(id=id)
    form = InventoryForm(request.POST or None, instance=items)

    if form.is_valid():
        form.save()
        return HttpResponseRedirect('../../inventory_item_list')
    
    context = {
        'form' : form,
        'items' : items,
        'title' : "Edit Supplier Item",
        'actiontype' : "Submit",
    }
    return render(request, 'inventory/inventory_item_add.html', context)

def inventory_item_delete(request, id):
    items = Inventory.objects.get(id=id)
    items.delete()
    return HttpResponseRedirect('../../inventory_item_list')

# Material Requisition
def materials_requisition_list(request):
    mr = MaterialRequisition.objects.all()
    context = {
        'mr' : mr 
    }
    return render (request, 'inventory/materials_requisition_list.html', context)

def materials_requisition_details(request, id):
    mr = MaterialRequisition.objects.get(id=id)
    mri = MaterialRequisitionItems.objects.filter(matreq=mr)
    context = {
        'mr' : mr,
        'title' : mr,
        'mri' : mri,
    }
    return render(request, 'inventory/materials_requisition_details.html', context)

# Mat req
def materials_requisition_form(request):
       #note:instance should be an object
    matreq_item_formset = inlineformset_factory(MaterialRequisition, MaterialRequisitionItems, form=MaterialRequisitionItemsForm, extra=1, can_delete=True)

    if request.method == "POST":
        form = MaterialRequisitionForm(request.POST)
        #Set ClientPO.client from session user
        #form.fields['client'].initial = Client.objects.get(id = request.session['session_userid'])
        message = ""
        print(form)
        if form.is_valid():
            #Save PO form then use newly saved ClientPO as instance for ClientPOItems
            new_form = form.save()
            new_form = new_form.pk
            form_instance = MaterialRequisition.objects.get(id=new_form)

            #Use PO form instance for PO items
            formset = matreq_item_formset(request.POST, instance=form_instance)
            print(formset)
            if formset.is_valid():
                for form in formset:
                    form.save()

                formset_items = Inventory.objects.filter(id = new_form)
                #formset_item_total = formset_items.aggregate(sum=aggregates.Sum('item_price'))['sum'] or 0

                totalled_matreq = MaterialRequisition.objects.get(id=new_form)
                #totalled_matreq.total_amount = formset_item_total
                totalled_matreq.save()
                message = "Material Requisition Submitted"

            else:
                message += "Formset error"

        else:
            message = "Form is not valid"


        #todo change index.html. page should be redirected after successful submission
        return render(request, 'index.html',
                              {'message': message}
                              )
    else:
        return render(request, 'inventory/materials_requisition_form.html',
                              {'formset':matreq_item_formset(),
                               'form': MaterialRequisitionForm}
                              )

# Supplier PO

def supplierPO_form(request):
    #note:instance should be an object
    supplierpo_item_formset = inlineformset_factory(SupplierPO, SupplierPOItems, form=SupplierPOItemsForm, extra=1, can_delete=True)

    if request.method == "POST":
        form = SupplierPOForm(request.POST)
        #Set ClientPO.client from session user
        #form.fields['client'].initial = Client.objects.get(id = request.session['session_userid'])
        message = ""
        print(form)
        if form.is_valid():
            #Save PO form then use newly saved ClientPO as instance for ClientPOItems
            new_form = form.save()
            new_form = new_form.pk
            form_instance = SupplierPO.objects.get(id=new_form)

            #Use PO form instance for PO items
            formset = supplierpo_item_formset(request.POST, instance=form_instance)
            print(formset)
            if formset.is_valid():
                for form in formset:
                    form.save()

                formset_items = Inventory.objects.filter(supplier_po_id = new_form)
                formset_item_total = formset_items.aggregate(sum=aggregates.Sum('item_price'))['sum'] or 0

                totalled_supplierpo = SupplierPO.objects.get(id=new_form)
                totalled_supplierpo.total_amount = formset_item_total
                totalled_supplierpo.save()
                message = "PO successfully created"

            else:
                message += "Formset error"

        else:
            message = "Form is not valid"


        #todo change index.html. page should be redirected after successful submission
        return render(request, 'index.html',
                              {'message': message}
                              )
    else:
        return render(request, 'inventory/supplierPO_form.html',
                              {'formset':supplierpo_item_formset(),
                               'form': SupplierPOForm}
                              )