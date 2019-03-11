import cursor as cursor
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory, inlineformset_factory
from django.db.models import aggregates
from django.db import connection
from django.contrib import messages

from django import forms
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
    today = date.today()
    issued_to_production = MaterialRequisition.objects.filter(datetime_issued__startswith=today)
    print('issued to production: ')
    print(issued_to_production)
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

        data.quantity += int(request.POST.get('new_count'))
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

# Material Requisition
def materials_requisition_list(request):
    mr = MaterialRequisition.objects.all()

    for x in mr:
        if str(x.id) in request.POST:
            x.status = "Retrieved"
            x.save()
            i = Inventory.objects.get(item=x.item)
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

# Supplier PO
def supplierPO_form(request):
    formset = inlineformset_factory(SupplierPO, SupplierPOItems, form=SupplierPOItemsForm, extra=1, can_delete=True)
    form = SupplierPOForm(request.POST)
    quantity = 0
    delivery_date = None
    item = None

    if request.META['HTTP_REFERER'].startswith('http://127.0.0.1:8000/sales/'):
        print('sales:confirm_order')
        quantity = request.session['matreq_quantity']
        delivery_date = datetime.now().date()
        if request.session['matreq_mat'] is not None:
            item = Inventory.objects.filter(rm_type=request.session['matreq_mat']).first()
            supplier = item.supplier
            item = item.id
        elif request.session['matreq_ink'] is not None:
            item = Inventory.objects.filter(item=request.session['matreq_ink'])
            supplier = item.supplier
            item = item.id

    elif request.META['HTTP_REFERER'].startswith('http://127.0.0.1:8000/inventory/'):
        print('inventory:forecast')
        item = request.session['item']
        inv = Inventory.objects.get(id=item)
        supplier = inv.supplier
        if request.session['forecast'] == 'SES':
            quantity = request.session['forecast_ses'][1]
            date = request.session['forecast_ses'][0]
            delivery_date = date[:10]
        elif request.session['forecast'] == 'HWES':
            quantity = request.session['forecast_hwes'][1]
            date = request.session['forecast_hwes'][0]
            delivery_date = date[:10]
        elif request.session['forecast'] == 'MOVING':
            quantity = request.session['forecast_moving_average'][1]
            date = request.session['forecast_moving_average'][0]
            delivery_date = date[:10]
        elif request.session['forecast'] == 'ARIMA':
            quantity = request.session['forecast_arima'][1]
            date = request.session['forecast_arima'][0]
            delivery_date = date[:10]


    if request.method == "POST":
        if form.is_valid():
            new_form = form.save()
            new_form = new_form.pk
            form_instance = SupplierPO.objects.get(id=new_form)

            formset = formset(request.POST, instance=form_instance)
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

        return redirect('inventory:supplierPO_list')

    form.fields["supplier"].queryset = Supplier.objects.filter(id=supplier.id)
    form.fields["delivery_date"] = forms.DateField(label='delivery_date', widget=forms.DateInput(attrs={'value': delivery_date}))
    #FIXME Add quantity and item placeholders
    #for form in formset.form:
    #    form.fields["quantity"] = forms.FloatField(label='quantity',
    #                                               widget=forms.NumberInput(attrs={'value': quantity}))
    #    form.fields["item"].queryset = Inventory.objects.filter(id=item)


    return render(request, 'inventory/supplierPO_form.html',
                  {'formset': formset,
                   'form': form}
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
    i = Inventory.objects.all()
    context ={
        'i' : i
    }
    return render(request, 'inventory/inventory_forecast.html', context)

def inventory_forecast_details(request, pk):

    item = Inventory.objects.get(id=pk)
    cursor = connection.cursor()
    #forecast_decomposition = []
    forecast_ses = []
    forecast_hwes = []
    forecast_moving_average = []
    forecast_arima = []

    query = 'SELECT spo.date_issued, spoi.quantity FROM inventory_mgt_inventory i, inventory_mgt_supplierpo spo, ' \
            'inventory_mgt_supplierpoitems spoi where spoi.item_id = '+str(pk)+'  and spoi.supplier_po_id = spo.id'

    cursor.execute(query)
    df = pd.read_sql(query, connection)
        # get_data = cursor.execute(query)
        # df = DataFrame(get_data.fetchall())
        # df.columns = get_data.keys()
        #forecast_decomposition.append(TimeSeriesForecasting.forecast_decomposition(df))

    a = TimeSeriesForecasting.forecast_ses(df)
    a[1] = int(float(a[1]))
    forecast_ses.extend(a)
    b = TimeSeriesForecasting.forecast_hwes(df)
    b[1] = int(float(b[1]))
    forecast_hwes.extend(b)
    c = TimeSeriesForecasting.forecast_moving_average(df)
    c[1] = int(float(c[1]))
    forecast_moving_average.extend(c)
    #d = TimeSeriesForecasting.forecast_arima(df)
    #d[1] = int(float(d[1]))
    #forecast_arima.extend(d)

    request.session['forecast_ses'] = forecast_ses
    request.session['forecast_hwes'] = forecast_hwes
    request.session['forecast_moving_average'] = forecast_moving_average
    request.session['forecast_arima'] = forecast_arima
    request.session['item'] = item.id

    if 'ses_order' in request.GET:
        request.session['forecast'] = 'SES'
        return redirect('inventory:supplierPO_form')
    elif 'hwes_order' in request.GET:
        request.session['forecast'] = 'HWES'
        return redirect('inventory:supplierPO_form')
    elif 'moving_average_order' in request.GET:
        request.session['forecast'] = 'MOVING'
        return redirect('inventory:supplierPO_form')
    elif 'arima_order' in request.GET:
        request.session['forecast'] = 'ARIMA'
        return redirect('inventory:supplierPO_form')
    else:
        request.session['forecast'] = None


    context = {
        'item': item,
        #'forecast_decomposition': forecast_decomposition,
        'forecast_ses': forecast_ses,
        'forecast_hwes': forecast_hwes,
        'forecast_moving_average': forecast_moving_average,
        'forecast_arima': forecast_arima,
    }
    return render(request, 'inventory/inventory_forecast_details.html', context)
