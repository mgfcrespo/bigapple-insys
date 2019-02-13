from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory, inlineformset_factory
from django.db.models import aggregates
from django.db import connection
from django.contrib import messages

from .models import Supplier, SupplierPO, SupplierPOItems, Inventory, Employee
from .models import MaterialRequisition, InventoryCount
from .forms import SupplierPOItemsForm, InventoryForm, SupplierPOForm, InventoryCountForm
from .forms import MaterialRequisitionForm
from sales.models import ClientItem
from datetime import datetime, date

from utilities import TimeSeriesForecasting
import pandas as pd
from pandas import DataFrame


# Create your views here.
# Inventory

def inventory_item_add(request):

    form = InventoryForm(request.POST)
    supplier = Supplier.objects.all()
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('inventory:inventory_item_list')

    context = {
        'supplier': supplier,
        'form': form,
        'title': 'Add Inventory Item',
        'actiontype': 'Submit'
    }

    return render(request, 'inventory/inventory_item_add.html', context)


def inventory_item_list(request):

    items = Inventory.objects.all()
    #FIXME: get quantities issued today
    issued_to_production = MaterialRequisition.objects.filter(datetime_issued = date.today())

    context = {
        'title': 'Inventory List',
        'items' : items,
        'issued_to_production' : issued_to_production,
        'now' : datetime.now()
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
        'actiontype' : "Submit"
    }
    return render(request, 'inventory/inventory_item_add.html', context)

def inventory_item_delete(request, id):
    items = Inventory.objects.get(id=id)
    items.delete()
    return HttpResponseRedirect('../../inventory-item-list')

# Inventory Count 
def inventory_count_form(request, id):
    data = Inventory.objects.get(id=id)
    form = InventoryCountForm(request.POST)

    if request.method == 'POST':
        employee_id = request.session['session_userid']
        current_employee = Employee.objects.get(id=employee_id)
        if form.is_valid():
            #i = data
            #item = i #item previously counted
            #print(item)
            #if item.exists():
              #counted = i.latest('time')#get latest
            new_form = form.save(commit=False)
            new_form.count_person = current_employee
            new_form.old_count = data.quantity
            new_form.inventory = data
            new_form.date_counted = date.today()
            new_form.save()
            form_id = new_form.pk
            #new_form = new_form.pk
            #form_instance = item #get current form

            #form_instance.old_count = i.new_count
            #form_instance.save()
            #new_form.save()
            #else:
            #form.save()
            #count = InventoryCount.objects.get(id=form_id)
            #count.inventory = data
            #count.old_count = data.quantity
            #count.new_count = request.POST.get('new_count')
            #count.count_person = current_employee
            #count.save()

        data.quantity = request.POST.get('new_count')
        data.save()

        return redirect('inventory:inventory_count_list', id = data.id)

    context = {
        'form' : form,
        'data': data,
        'title': 'Inventory Count',
        'actiontype': 'Submit'
        #'actiontype': 'Update'
    }

    return render(request, 'inventory/inventory_count_form.html', context)

def inventory_count_list(request, id):
    item = Inventory.objects.get(id=id)
    i = InventoryCount.objects.filter(inventory=item)

    context = {
        'i' : i,
        'item' : item
    }
    return render (request, 'inventory/inventory_count_list.html', context)

# Supplier Raw Material

'''
def supplier_rawmat_list(request):
    items = SupplierRawMaterials.objects.all()
    context = {
        'title': 'List of Supplier Raw Material',
        'items' : items
    }
'''

def supplier_details_list(request, id):
    items = Inventory.objects.filter(supplier = id)
    data = SupplierPO.objects.filter(id = id)
    title1 = 'Supplier Raw Material'
    title2 = 'Supplier Sales Invoice'
    context = {
       'title1': title1,
       'title2': title2,
        'items' : items,
        'data': data
    }
    return render (request, 'inventory/supplier_details_list.html', context)
'''
def supplier_rawmat_add(request):
    form = Inventory(request.POST)
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
                            'item': request.POST.get("item"),
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
        'actiontype': 'Submit',
        'title': title,
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
        'actiontype' : "Submit"
    }
    return render(request, 'inventory/supplier_rawmat_add.html', context)

def supplier_rawmat_delete(request, id):
    items = SupplierRawMaterials.objects.get(id=id)
    data = Supplier.objects.get(id = items.supplier.id)
    items.delete()
    return redirect('inventory:supplier_details_list', id = data.id)
'''
# Material Requisition
def materials_requisition_list(request):
    mr = MaterialRequisition.objects.all()

    for x in mr:
        if request.method == "POST":
            x.status = "Retrieved"
            x.save()
            i = Inventory.objects.get(item=x.item)  # get Inventory Items
            i.quantity -= x.quantity
            i.save()

            messages.success(request, 'Materials have been retrieved.')

    context = {
        'title' :'Material Requisition List',
        'mr' : mr
    }
    return render (request, 'inventory/materials_requisition_list.html', context)

def materials_requisition_details(request, id):
    mr = MaterialRequisition.objects.get(id=id) #get MR
    item = mr.client_item

    style = "ui teal message"

    context = {
        'mr' : mr,
        'title' : mr,
        'style' : style,
        'item' : item
    }
    return render(request, 'inventory/materials_requisition_details.html', context)

def materials_requisition_approval(request, id):
    if request.session['session_position'] == "General Manager":
        template = 'general_manager_page_ui.html'
    elif request.session['session_position'] == "Production Manager":
        template = 'production_manager_page_ui.html'
    else:
        template = 'line_leader_page_ui.html'

    mr = MaterialRequisition.objects.get(id=id) #get id of matreq
    count = 0
    if request.POST:
        i = Inventory.objects.get(item = mr.item)# get Inventory Items
        i.quantity -= mr.quantity
        i.save()

        mr.datetime_issued = datetime.now()
        mr.status = "Retrieved"
        mr.save()

        messages.success(request, 'Materials have been retrieved.')

    else:
        messages.warning(request, 'Insufficient Inventory!')
        return redirect('inventory:materials_requisition_details', id = mr.id)
    
    return redirect('inventory:materials_requisition_details', id = mr.id)
'''
def materials_requisition_form(request):
    # note:instance should be an object
    matreq_item_formset = inlineformset_factory(MaterialRequisition, MaterialRequisitionItems,
                                                  form=MaterialRequisitionForm, extra=1, can_delete=True)

    if request.method == "POST":
        form = MaterialRequisitionForm(request.POST)
        # Set ClientPO.client from session user
        # form.fields['client'].initial = Client.objects.get(id = request.session['session_userid'])
        message = ""
        print(form)
        if form.is_valid():
            # Save PO form then use newly saved ClientPO as instance for ClientPOItems
            new_form = form.save()
            new_form = new_form.pk
            form_instance = MaterialRequisitionForm.objects.get(id=new_form)

            # Use PO form instance for PO items
            formset = matreq_item_formset(request.POST, instance=form_instance)
            print(formset)
            if formset.is_valid():
                for form in formset:
                    form.save()

                formset_items = Inventory.objects.filter(id=new_form)
                # formset_item_total = formset_items.aggregate(sum=aggregates.Sum('item_price'))['sum'] or 0

                totalled_matreq = MaterialRequisitionForm.objects.get(id=new_form)
                # totalled_matreq.total_amount = formset_item_total
                totalled_matreq.save()
                message = "Material Requisition Submitted"

            else:
                message += "Formset error"

        else:
            message = "Form is not valid"

        # todo change index.html. page should be redirected after successful submission
        return redirect('inventory:materials_requisition_list')

    else:
        return render(request, 'inventory/materials_requisition_form.html',
                      {'formset': matreq_item_formset(),
                       'form': MaterialRequisitionForm}
                      )


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
        'pri' : pri
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
'''

# Supplier PO
def supplierPO_form(request):
    supplierpo_item_formset = inlineformset_factory(SupplierPO, SupplierPOItems, form=SupplierPOItemsForm, extra=1, can_delete=True)
    form = SupplierPOForm(request.POST)
    if request.method == "POST":
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

                formset_items = SupplierPOItems.objects.filter(supplier_po_id = new_form)
                #formset_items_rm = Inventory.objects.filter(id = id)
                #formset_items.price = formset_items_rm.price

                formset_item_total = formset_items.aggregate(sum=aggregates.Sum('total_price'))['sum'] or 0.00
                #totalled_supplierpo = SupplierPO.objects.get(id=new_form)
                form_instance.total_amount = formset_item_total
                form_instance.save()

                message = "PO successfully created"

            else:
                message += "Formset error"

        else:
            message = "Form is not valid"


        return render(request, 'inventory/supplierPO_form.html',
                              {'message': message, 'formset': supplierpo_item_formset,
                               'form': SupplierPOForm}
                              )
    else:
        return render(request, 'inventory/supplierPO_form.html',
                              {'formset': supplierpo_item_formset,
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
        'mr' : mr
    }
    return render (request, 'inventory/supplierPO_list.html', context)

def supplierPO_details(request, id):

    mr = SupplierPO.objects.get(id=id)
    mri = SupplierPOItems.objects.filter(supplier_po=mr)
    context = {
        'mr' : mr,
        'title' : mr,
        'mri' : mri
    }
    return render(request, 'inventory/supplierPO_details.html', context)

def load_items(request):
    supplier_po = request.GET.get('supplier_po')
    items = Inventory.objects.filter(supplier_id=id).order_by('item')
    return render(request, 'inventory/dropdown_supplier_item.html', {'supplier_po' : supplier_po, 'items': items})


def inventory_forecast(request):

    i = Inventory.objects.all().order_by('supplier')
    cursor = connection.cursor()
    #forecast_decomposition = []
    forecast_ses = []
    forecast_hwes = []
    forecast_moving_average = []
    forecast_arima = []


    for x in i :
        query = 'SELECT spo.date_issued, spoi.quantity FROM inventory_mgt_inventory i, inventory_mgt_supplierpo spo, ' \
                'inventory_mgt_supplierpoitems spoi where spoi.item_id = ' + str(x.id) + \
                ' and spoi.supplier_po_id = spo.id'

        cursor.execute(query)
        df = pd.read_sql(query, connection)
        # get_data = cursor.execute(query)
        # df = DataFrame(get_data.fetchall())
        # df.columns = get_data.keys()

        #forecast_decomposition.append(TimeSeriesForecasting.forecast_decomposition(df))
        forecast_ses.append(TimeSeriesForecasting.forecast_ses(df))
        forecast_hwes.append(TimeSeriesForecasting.forecast_hwes(df))
        forecast_moving_average.append(TimeSeriesForecasting.forecast_moving_average(df))
        forecast_arima.append(TimeSeriesForecasting.forecast_arima(df))

    context = {
        'i': i,
        #'forecast_decomposition': forecast_decomposition,
        'forecast_ses': forecast_ses,
        'forecast_hwes': forecast_hwes,
        'forecast_moving_average': forecast_moving_average,
        'forecast_arima': forecast_arima,
    }
    return render(request, 'inventory/inventory_forecast.html', context)
