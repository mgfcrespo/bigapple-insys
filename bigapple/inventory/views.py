from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory, inlineformset_factory
from django.db.models import aggregates

from .models import SupplierSalesInvoice
from .models import Supplier, SupplierPO, SupplierPOItems, Inventory, SupplierRawMaterials, InventoryCountAsof, Employee
from .models import MaterialRequisition, MaterialRequisitionItems, PurchaseRequisition, PurchaseRequisitionItems
from .forms import SupplierPOItemsForm, InventoryForm, SupplierPOForm, SupplierRawMaterialsForm, InventoryCountAsofForm
from .forms import MaterialRequisitionForm, MaterialRequisitionItemsForm, PurchaseRequisitionForm, PurchaseRequisitionItemsForm


# Create your views here.
# Inventory
def inventory_item_list(request):
    items = Inventory.objects.all()
    context = {
        'title': 'Inventory List',
        'items' : items 
    }
    return render (request, 'inventory/inventory_item_list.html', context)

def inventory_item_edit(request, id):
    items = Inventory.objects.get(id=id)
    form = InventoryForm(request.POST or None, instance=items)

    if form.is_valid():
        form.save()
        return HttpResponseRedirect('../../inventory-item-list')
    
    context = {
        'form' : form,
        'items' : items,
        'title' : "Edit Inventory Item",
        'actiontype' : "Submit",
    }
    return render(request, 'inventory/inventory_item_add.html', context)

def inventory_item_delete(request, id):
    items = Inventory.objects.get(id=id)
    items.delete()
    return HttpResponseRedirect('../../inventory-item-list')

# Inventory Count 
def inventory_count_form(request, id):
    data = Inventory.objects.get(id=id)
    form = InventoryCountAsofForm(request.POST)
    
    form.fields["inventory"].queryset = Inventory.objects.filter(id=data.id)
    form.fields["inventory"].initial = data.id
    
    if request.method == 'POST':
        
        #Get session user id
        # employee_id = request.session['session_userid']
        # current_employee = Employee.objects.get(id=employee_id)

        if form.is_valid():
            data.quantity = request.POST.get('new_count')
            #data.person = current_employee
            data.save()

            i = request.POST.get('inventory')
            item = InventoryCountAsof.objects.filter(inventory=i) #item previously counted
            print(item)
            if item.exists():
                counted = InventoryCountAsof.objects.filter(inventory=i).latest('time')#get latest

                new_form = form.save()
                new_form = new_form.pk
                form_instance = InventoryCountAsof.objects.get(id=new_form) #get current form

                form_instance.old_count = counted.new_count
                form_instance.save()
            else:   
                form.save()
        
        return redirect('inventory:inventory_count_list', id = data.id)
    
    form.fields["inventory"].queryset = Inventory.objects.filter(id=data.id)
    form.fields["inventory"].initial = data.id

    context = {
        'form' : form,
        'data': data,
        'title': 'Inventory Count',
        'actiontype': 'Update'
    }

    return render(request, 'inventory/inventory_count_form.html', context)

def inventory_count_list(request, id):
    i = Inventory.objects.get(id=id)

    items = InventoryCountAsof.objects.filter(inventory=id).order_by('-time')
    context = {
        'title': i.item,
        'items' : items 
    }
    return render (request, 'inventory/inventory_count_list.html', context)

# Supplier Raw Material

def supplier_details_list(request, id):
    items = SupplierRawMaterials.objects.filter(supplier = id)
    data = SupplierSalesInvoice.objects.filter(id = id)
    title1 = 'Supplier Raw Material'
    title2 = 'Supplier Sales Invoice'
    context = {
       'title1': title1,
       'title2': title2,
        'items' : items,
        'data': data
    }
    return render (request, 'inventory/supplier_details_list.html', context)

def supplier_rawmat_add(request):
    form = SupplierRawMaterialsForm(request.POST)
    title =  'Add Supplier Raw Material'

    if title == 'Add Supplier Raw Material':
        if request.method == 'POST':
            if form.is_valid():
                if request.POST.get("item_type") == "Raw Materials":
                    rm = Inventory.objects.filter(item = request.POST.get("rm_type"))
                    print(rm)
                    if rm.exists():
                        print("Item Exists")
                    else:
                        iform = InventoryForm({
                            'item': request.POST.get("rm_type"),
                            'item_type': request.POST.get("item_type")
                        })
                        print("Item saved")
                        iform.save()

                elif request.POST.get("item_type") != "Raw Materials":
                    i = Inventory.objects.filter(item = request.POST.get("item_name"), item_type =  request.POST.get("item_type"))
                    if i.exists():
                        print("Item Exists")
                    else:
                        iform = InventoryForm({
                            'item': request.POST.get("item_name"),
                            'item_type': request.POST.get("item_type"),
                        })
                        print("Item saved")
                        iform.save()
                else:
                    print("Others: Do nothing")

            form.save()
            return redirect('../inventory-item-list/')

    context = {
        'form' : form,
        'title': title,
        'actiontype': 'Submit'
    }

    return render(request, 'inventory/supplier_rawmat_add.html', context)

def supplier_rawmat_edit(request, id):
    items = SupplierRawMaterials.objects.get(id=id)
    form = SupplierRawMaterialsForm(request.POST or None, instance=items)
    data = Supplier.objects.get(id = items.supplier.id)
    if form.is_valid():
        form.save()
        return redirect('inventory:supplier_details_list', id = data.id)
    
    context = {
        'form' : form,
        'items' : items,
        'title' : "Edit Supplier Raw Material",
        'actiontype' : "Submit",
    }
    return render(request, 'inventory/supplier_rawmat_add.html', context)

def supplier_rawmat_delete(request, id):
    items = SupplierRawMaterials.objects.get(id=id)
    data = Supplier.objects.get(id = items.supplier.id)
    items.delete()
    return redirect('inventory:supplier_details_list', id = data.id)

# Material Requisition
def materials_requisition_list(request):
    mr = MaterialRequisition.objects.all()
    context = {
        'title' :'Material Requisition List',
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
    mr = MaterialRequisition.objects.get(id=id) #get id of matreq
    mri = MaterialRequisitionItems.objects.filter(matreq=mr) #get all items in matreq

    #def clean(self):
    if request.POST:
        if 'approve' in request.POST:
            for mri in mri:
                items = Inventory.objects.get(id=mri.brand.id) #get items in inventory that is in matreq
                if Inventory.objects.filter(id=mri.brand.id).exists():
                    if Inventory.objects.filter(quantity__gte=mri.quantity):
                        items.quantity = (items.quantity-mri.quantity)
                        mr.approval = True
                        mr.status = "approved"
                        mr.save()
                        items.save()
                        return redirect('inventory:materials_requisition_list')
                    else:
                        # TODO
                        # should render error message
                        messages = "Insufficient Inventory Quantity!"
                        return redirect('inventory:materials_requisition_details', id = mr.id)
                else:
                    message = 'Insufficient Inventory Quantity'
                    return redirect('inventory:materials_requisition_details', id = mr.id)
        

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


        form.fields["issued_to"].queryset = Employee.objects.filter(position__in=['General Manager', 'Sales Coordinator', 'Supervisor',
        'Line Leader', 'Production Manager', 'Cutting', 'Printing', 'Extruder', 'Delivery', 'Warehouse', 'Utility', 
        'Maintenance'])

        return redirect('inventory:materials_requisition_list')
    
    else:
        return render(request, 'inventory/materials_requisition_form.html',
                              {'formset':matreq_item_formset(),
                               'form': MaterialRequisitionForm}
                              )
    return redirect('inventory:materials_requisition_list')

#Purchase Requisition
def purchase_requisition_list(request):
    pr = PurchaseRequisition.objects.all()
    context = {
        'title' :'Purchase Requisition List',
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
        return redirect('inventory:purchase_requisition_list')

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

                formset_items = SupplierPOItems.objects.filter(id = new_form)
                formset_items_rm = SupplierRawMaterials.objects.filter(id = id)
                formset_items.price = formset_items_rm.price 

                formset_item_total = formset_items.aggregate(sum=aggregates.Sum('total_price'))['sum'] or 0

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

def supplierPO_form_test(request):
    supplierpo_item_formset = inlineformset_factory(SupplierPO, SupplierPOItems, form=SupplierPOItemsForm, extra=1, can_delete=True)
    # data = JobOrder.objects.get(id=id)
    # form = PrintingScheduleForm(request.POST or None)
    # print(form.errors)
    # if request.method == 'POST':
    #   if form.is_valid():
    #     form.save()
    #     return redirect('production:job_order_details', id = data.id)
    
    # context = {
    #   'data': data,
    #   'title' : data.job_order,
    #   'form': form,
    # }
    
    return render (request, 'inventory/supplierPO_form.html',
                              {'formset':supplierpo_item_formset(),
                               'form': SupplierPOForm}
                              )

def supplierPO_list(request):
    mr = SupplierPO.objects.all()
    context = {
        'title' :'Supplier PO List',
        'mr' : mr,
    }
    return render (request, 'inventory/supplierPO_list.html', context)

def supplierPO_details(request, id):
    mr = SupplierPO.objects.get(id=id)
    mri = SupplierPOItems.objects.filter(supplier_po=mr)
    context = {
        'mr' : mr,
        'title' : mr,
        'mri' : mri,
    }
    return render(request, 'inventory/supplierPO_details.html', context)

def load_items(request):
    supplier_po = request.GET.get('supplier_po')
    items = Inventory.objects.filter(supplier_id=id).order_by('item_name')
    return render(request, 'inventory/dropdown_supplier_item.html', {'items': items})