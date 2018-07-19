from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory, inlineformset_factory
from django.db.models import aggregates

from .models import Supplier, SupplierPO, SupplierPOItems, Inventory
from .models import MaterialRequisition, MaterialRequisitionItems, PurchaseRequisition, PurchaseRequisitionItems
from .forms import SupplierPOItemsForm, InventoryForm, SupplierPOForm
from .forms import MaterialRequisitionForm, MaterialRequisitionItemsForm, PurchaseRequisitionForm, PurchaseRequisitionItemsForm


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

def materials_requisition_approval(request, id):
    mr = MaterialRequisition.objects.get(id=id)
    
    #def clean(self):
    if request.POST:
        if 'approve' in request.POST:
            mr.approval = True
            mr.status = "approved"
            mr.save()
            return redirect('inventory:materials_requisition_list')
        
        elif 'decline' in request.POST:
            mr.approval = False
            mr.status = "declined"
            mr.save()
            return redirect('inventory:materials_requisition_list')
			
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

							  #Purchase Requisition
def purchase_requisition_list(request):
    pr = PurchaseRequisition.objects.all()
    context = {
        'pr' : pr 
    }
    return render (request, 'inventory/purchase_requisition_list.html', context)

def purchase_requisition_details(request, id):
    pr = PurchaseRequisition.objects.get(id=id)
    pri = PurchaseRequisitionItems.objects.filter(purchreq=pr)
    context = {
        'pr' : pr,
        'title' : pr,
        'pri' : pri,
    }
    return render(request, 'inventory/purchase_requisition_details.html', context)

def purchase_requisition_approval(request, id):
    pr = PurchaseRequisition.objects.get(id=id)
    
    #def clean(self):
    if request.POST:
        if 'approve' in request.POST:
            pr.approval = True
            pr.status = "approved"
            pr.save()
            return redirect('inventory:purchase_requisition_list')
        
        elif 'decline' in request.POST:
            pr.approval = False
            pr.status = "declined"
            pr.save()
            return redirect('inventory:purchase_requisition_list')
	
def purchase_requisition_form(request):
    #note:instance should be an object
    purchreq_item_formset = inlineformset_factory(PurchaseRequisition, PurchaseRequisitionItems, form=PurchaseRequisitionItemsForm, extra=1, can_delete=True)

    if request.method == "POST":
        form = PurchaseRequisitionForm(request.POST)
        #Set ClientPO.client from session user
        #form.fields['client'].initial = Client.objects.get(id = request.session['session_userid'])
        message = ""
        print(form)
        if form.is_valid():
            #Save PO form then use newly saved ClientPO as instance for ClientPOItems
            new_form = form.save()
            new_form = new_form.pk
            form_instance = PurchaseRequisition.objects.get(id=new_form)

            #Use PO form instance for PO items
            formset = purchreq_item_formset(request.POST, instance=form_instance)
            print(formset)
            if formset.is_valid():
                for form in formset:
                    form.save()

                formset_items = Inventory.objects.filter(id = new_form)
                #formset_item_total = formset_items.aggregate(sum=aggregates.Sum('item_price'))['sum'] or 0

                totalled_purchreq = PurchaseRequisition.objects.get(id=new_form)
                #totalled_matreq.total_amount = formset_item_total
                totalled_purchreq.save()
                message = "Purchase Requisition Submitted"

            else:
                message += "Formset error"

        else:
            message = "Form is not valid"


        #todo change index.html. page should be redirected after successful submission
        return render(request, 'index.html',
                              {'message': message}
                              )
    else:
        return render(request, 'inventory/purchase_requisition_form.html',
                              {'formset':purchreq_item_formset(),
                               'form': PurchaseRequisitionForm}
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