import cursor as cursor
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory, inlineformset_factory
from django.db.models import aggregates, Avg, Sum, Count
from django.db import connection
from django.contrib import messages

from django import forms
from .models import Supplier, SupplierPO, SupplierPOItems, Inventory, Employee
from .models import MaterialRequisition, InventoryCount
from .forms import SupplierPOItemsForm, InventoryForm, SupplierPOForm, InventoryCountForm
from .forms import MaterialRequisitionForm
from sales.models import ClientItem, Product
from datetime import datetime, date, timedelta
from production.models import JobOrder
import dateutil.relativedelta

from utilities import TimeSeriesForecasting
import pandas as pd
from pandas import DataFrame
import math
from django.db.models import Q


# Create your views here.
# Inventory

def eoq():
    # EOQ
    today = datetime.now()
    month = today - dateutil.relativedelta.relativedelta(months=3)
    month = month.month

    allItems = JobOrder.objects.filter(date_issued__month=month)
    ldpe_demand = 0
    ldpe_cost = Product.objects.filter(material_type='LDPE').aggregate(Avg('prod_price')).get('prod_price__avg',
                                                                                              0)

    lldpe_demand = 0
    lldpe_cost = Product.objects.filter(material_type='LLDPE').aggregate(Avg('prod_price')).get('prod_price__avg',
                                                                                                0)

    hdpe_demand = 0
    hdpe_cost = Product.objects.filter(material_type='HDPE').aggregate(Avg('prod_price')).get('prod_price__avg',
                                                                                              0)

    pp_demand = 0
    pp_cost = Product.objects.filter(material_type='PP').aggregate(Avg('prod_price')).get('prod_price__avg',
                                                                                          0)

    pet_demand = 0
    pet_cost = Product.objects.filter(material_type='PET').aggregate(Avg('prod_price')).get('prod_price__avg',
                                                                                            0)

    pe_demand = 0
    pe_cost = Product.objects.filter(material_type='Pelletized PE').aggregate(Avg('prod_price')).get('prod_price__avg',
                                                                                                     0)

    hd_demand = 0
    hd_cost = Product.objects.filter(material_type='Pelletized HD').aggregate(Avg('prod_price')).get('prod_price__avg',
                                                                                                     0)

    for x in allItems:
        i = ClientItem.objects.filter(client_po_id=x.id)
        for y in i:
            if y.products.material_type == 'LDPE':
                ldpe_demand += y.quantity / 1000
            elif y.products.material_type == 'LLDPE':
                lldpe_demand += y.quantity / 1000
            elif y.products.material_type == 'HDPE':
                hdpe_demand += y.quantity / 1000
            elif y.products.material_type == 'PP':
                pp_demand += y.quantity / 1000
            elif y.products.material_type == 'PET':
                pet_demand += y.quantity / 1000
            elif y.products.material_type == 'Pelletized PE':
                pe_demand += y.quantity / 1000
            elif y.products.material_type == 'Pelletized HD':
                hd_demand += y.quantity / 1000

    if not ldpe_demand:
        EOQ_ldpe = 1
    else:
        EOQ_ldpe = (math.sqrt(2 * ldpe_demand * ldpe_cost)) / 100

    if not lldpe_demand:
        EOQ_lldpe = 1
    else:
        EOQ_lldpe = (math.sqrt(2 * lldpe_demand * lldpe_cost)) / 100

    if not hdpe_demand:
        EOQ_hdpe = 1
    else:
        EOQ_hdpe = (math.sqrt(2 * hdpe_demand * hdpe_cost)) / 100

    if not pp_demand:
        EOQ_pp = 1
    else:
        EOQ_pp = (math.sqrt(2 * pp_demand * pp_cost)) / 100

    if not pet_demand:
        EOQ_pet = 1
    else:
        EOQ_pet = (math.sqrt(2 * pet_demand * pet_cost)) / 100

    if not pet_demand:
        EOQ_pe = 1
    else:
        EOQ_pe = (math.sqrt(2 * pet_demand * pe_cost)) / 100

    if not hd_demand:
        EOQ_hd = 1
    else:
        EOQ_hd = (math.sqrt(2 * hdpe_demand * hd_cost)) / 100

    EOQ_ldpe = int(ldpe_demand / EOQ_ldpe)
    EOQ_lldpe = int(lldpe_demand / EOQ_lldpe)
    EOQ_hdpe = int(hdpe_demand / EOQ_hdpe)
    EOQ_pe = int(pe_demand / EOQ_pe)
    EOQ_pet = int(pet_demand / EOQ_pet)
    EOQ_pp = int(pp_demand / EOQ_pp)
    EOQ_hd = int(hd_demand / EOQ_hd)

    return {'EOQ_ldpe' : EOQ_ldpe,
            'EOQ_lldpe': EOQ_lldpe,
            'EOQ_hdpe': EOQ_hdpe,
            'EOQ_pe': EOQ_pe,
            'EOQ_pet': EOQ_pet,
            'EOQ_pp': EOQ_pp,
            'EOQ_hd': EOQ_hd,
            }

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
    today = date.today()
    issued_to_production = []
    matreqs = MaterialRequisition.objects.filter(datetime_issued__startswith=today)
    for every in items:
        req_sum_item = 0
        for each in matreqs:
            if each.item == every:
                req_sum_item += each.quantity
        issued_to_production.append({'Item' : every,
                                     'QTY' : req_sum_item})

    spo_items = SupplierPOItems.objects.all()
    spo = []
    supplier_po = SupplierPO.objects.filter(date_issued=today)
    for each in spo_items:
        for every in supplier_po:
            if each.supplier_po_id == every.id:
                spo.append(each)

    a = InventoryCount.objects.all()
    counts = []
    for b in a:
        for c in supplier_po:
            if b.spo_count_id == c.id:
                counts.append(b)
    shift11 = datetime.now()
    shift12 = datetime.now()
    shift22 = datetime.now()
    shift32 = datetime.now() + timedelta(days=1)
    shift11 = shift11.replace(hour=6)
    shift12 = shift12.replace(hour=14)
    shift22 = shift22.replace(hour=22)
    shift32 = shift32.replace(hour=6)

    matreqs_1st_shift = MaterialRequisition.objects.filter(datetime_issued__range=[shift11, shift12])
    matreqs_2nd_shift = MaterialRequisition.objects.filter(datetime_issued__range=[shift12, shift22])
    matreqs_3rd_shift = MaterialRequisition.objects.filter(datetime_issued__range=[shift22, shift32])

    context = {
        'title': 'Inventory List',
        'items' : items,
        'issued_to_production' : issued_to_production,
        'now' : datetime.now(),
        'spo' : spo,
        'counts' : counts,
        'matreqs_1st_shift' : matreqs_1st_shift,
        'matreqs_2nd_shift' : matreqs_2nd_shift,
        'matreqs_3rd_shift' : matreqs_3rd_shift,
        'EOQ_ldpe' : eoq().get('EOQ_ldpe'),
        'EOQ_lldpe': eoq().get('EOQ_lldpe'),
        'EOQ_hdpe': eoq().get('EOQ_hdpe'),
        'EOQ_pe': eoq().get('EOQ_pe'),
        'EOQ_pet': eoq().get('EOQ_pet'),
        'EOQ_pp': eoq().get('EOQ_pp'),
        'EOQ_hd': eoq().get('EOQ_hd')
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
    return render(request, 'inventory/inventory_item_edit.html', context)

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
            new_form = form.save(commit=False)
            new_form.count_person = current_employee
            new_form.old_count = data.quantity
            new_form.inventory = data
            new_form.date_counted = date.today()
            new_form.save()
            form_id = new_form.pk

        data.quantity += int(request.POST.get('new_count'))
        data.save()

        return redirect('inventory:inventory_count_list', id = data.id)

    form.fields['spo_count'].queryset = SupplierPO.objects.filter(supplier_id=data.supplier_id)
    form.fields['client_po'].queryset = JobOrder.objects.all()

    context = {
        'form' : form,
        'data': data,
        'title': 'Procured Item Count',
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
    return render(request, 'inventory/inventory_count_list.html', context)

def supplier_details_list(request, id):
    items = Inventory.objects.filter(supplier_id = id)
    data = SupplierPO.objects.filter(supplier_id = id)

    context = {
        'items' : items,
        'data': data
    }
    return render (request, 'inventory/supplier_details_list.html', context)

# Material Requisition
def materials_requisition_list(request):
    mr = MaterialRequisition.objects.all()
    items = ClientItem.objects.all()

    for x in mr:
        if str(x.id) in request.POST:
            x.status = "Retrieved"
            x.save()
            i = Inventory.objects.get(id=x.item_id)
            print('MATREQ ')
            print(i)
            print('before retrieve')
            print(i.quantity)
            i.quantity -= x.quantity
            print('after retrieve')
            print(i.quantity)
            i.save()
            messages.success(request, 'Materials have been retrieved.')

    context = {
        'items' : items,
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

    quantity = 0
    delivery_date = None
    item = None
    supplier = None

    inventory = Inventory.objects.all()

    suggested = []
    ldpe = Inventory.objects.filter(rm_type='LDPE').aggregate(Sum('quantity'))['quantity__sum']
    lldpe = Inventory.objects.filter(rm_type='LLDPE').aggregate(Sum('quantity'))['quantity__sum']
    hdpe = Inventory.objects.filter(rm_type='HDPE').aggregate(Sum('quantity'))['quantity__sum']
    pe = Inventory.objects.filter(rm_type='Pelletized PE').aggregate(Sum('quantity'))['quantity__sum']
    pet = Inventory.objects.filter(rm_type='PET').aggregate(Sum('quantity'))['quantity__sum']
    pp = Inventory.objects.filter(rm_type='PP').aggregate(Sum('quantity'))['quantity__sum']
    hd = Inventory.objects.filter(rm_type='Pelletized HD').aggregate(Sum('quantity'))['quantity__sum']
    quantities = {'LDPE' : ldpe,
                  'LLDPE' : lldpe,
                  'HDPE' : hdpe,
                  'Pelletized PE' : pe,
                  'PET' : pet,
                  'PP' : pp,
                  'Pelletized HD' : hd,
                  }
    suggested.append(min(quantities, key=quantities.get))
    del quantities[min(quantities, key=quantities.get)]
    suggested.append(min(quantities, key=quantities.get))
    del quantities[min(quantities, key=quantities.get)]
    suggested.append(min(quantities, key=quantities.get))
    del quantities[min(quantities, key=quantities.get)]

    replenish = []
    replenish.extend(Inventory.objects.filter(rm_type=suggested[0]))
    replenish.extend(Inventory.objects.filter(rm_type=suggested[1]))
    replenish.extend(Inventory.objects.filter(rm_type=suggested[2]))

    if request.META['HTTP_REFERER'].startswith('http://127.0.0.1:8000/sales/'):
        print('sales:confirm_order/rush_order_assessment')
        quantity = request.session.get('matreq_quantity')
        delivery_date = datetime.now().date()
        if request.session.get('matreq_mat'):
            try:
                item = Inventory.objects.filter(rm_type=request.session.get('matreq_mat')).first()
                supplier = Supplier.objects.filter(id=item.supplier_id)
                item = item.id
            except Inventory.DoesNotExist:
                item = None
        elif request.session.get('matreq_ink'):
            try:
                item = Inventory.objects.get(item=request.session.get('matreq_ink'))
                supplier = Supplier.objects.filter(id=item.supplier_id)
                item = item.id
            except Inventory.DoesNotExist:
                item = None

    elif request.META['HTTP_REFERER'].startswith('http://127.0.0.1:8000/inventory/inventory-forecast-details/'):
        print('inventory:forecast')
        item = request.session.get('item')
        inv = Inventory.objects.get(id=item)
        supplier = Supplier.objects.filter(id=inv.supplier_id)
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

    else:
        delivery_date = datetime.now().date()
        supplier = Supplier.objects.all()


    formset = inlineformset_factory(SupplierPO, SupplierPOItems, form=SupplierPOItemsForm, extra=1, can_delete=True, fields=['quantity',
                                    'item'],
                                widgets={ 'quantity': forms.NumberInput(attrs={'value': quantity}),
                                             #FIXME Item queryset
                                             })

    form = SupplierPOForm(request.POST)

    if request.method == "POST":
        if form.is_valid():
            new_form = form.save()
            new_form = new_form.pk
            form_instance = SupplierPO.objects.get(id=new_form)
            formset = formset(request.POST, instance=form_instance)
            print(formset.errors)
            if formset.is_valid():
                print('formset valid')
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

    form.fields["supplier"].queryset = supplier
    form.fields["delivery_date"] = forms.DateField(label='delivery_date',
                                                   widget=forms.DateInput(attrs={'value': delivery_date}))
    form.fields["client_po"].queryset = JobOrder.objects.filter(~Q(status='Ready for delivery') & ~Q(status='Delivered'))
    # for each in formset:
    #    each.fields["quantity"] = forms.FloatField(label='quantity',
    #                                               widget=forms.NumberInput(attrs={'value': quantity}))
    #    each.fields["item"].queryset =  Inventory.objects.filter(id=item)

    return render(request, 'inventory/supplierPO_form.html', {'form': SupplierPOForm, 'formset' : formset, 'replenish' : replenish,
                                                              'EOQ_ldpe' : eoq().get('EOQ_ldpe'),
                                                              'EOQ_lldpe': eoq().get('EOQ_lldpe'),
                                                              'EOQ_hdpe': eoq().get('EOQ_hdpe'),
                                                              'EOQ_pe': eoq().get('EOQ_pe'),
                                                              'EOQ_pet': eoq().get('EOQ_pet'),
                                                              'EOQ_pp': eoq().get('EOQ_pp'),
                                                              'EOQ_hd': eoq().get('EOQ_hd')
                                                                            })

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
    received = InventoryCount.objects.all()
    context = {
        'title' :'Supplier PO List',
        'mr' : mr,
        'received' : received
    }
    return render (request, 'inventory/supplierPO_list.html', context)

def supplierPO_details(request, id):

    mr = SupplierPO.objects.get(id=id)
    mri = SupplierPOItems.objects.filter(supplier_po=mr)
    received = InventoryCount.objects.all()

    context = {
        'mr' : mr,
        'title' : mr,
        'mri' : mri,
        'received' : received
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
    forecast_ses = []
    forecast_hwes = []
    forecast_moving_average = []
    forecast_arima = []
    ink = str("'"+item.item+"'")

    if item.item_type == 'Raw Materials':
        product = Product.objects.get(material_type=item.rm_type)
        query = 'SELECT po.date_issued, poi.quantity DIV 1000 AS "quantity" FROM production_mgt_joborder po, sales_mgt_clientitem poi WHERE ' \
                ' poi.products_id = ' + str(product.id)
    elif item.item_type == 'Ink':
        query = 'SELECT po.date_issued, `poi`.`quantity` DIV 2500 AS "quantity" FROM  production_mgt_joborder po, sales_mgt_clientitem poi WHERE ' \
                ' `poi`.`color` = '+str(ink)
    else:
        query = 'SELECT spo.date_issued, spoi.quantity FROM inventory_mgt_supplierpo spo, ' \
                'inventory_mgt_supplierpoitems spoi where spoi.item_id = ' + str(pk) + 'and spoi.supplier_po_id = spo.id'

    cursor.execute(query)
    df = pd.read_sql(query, connection)

    a = TimeSeriesForecasting.forecast_ses(df)
    a[1] = int(float(a[1]))
    forecast_ses.extend(a)
    b = TimeSeriesForecasting.forecast_hwes(df)
    b[1] = int(float(b[1]))
    forecast_hwes.extend(b)
    c = TimeSeriesForecasting.forecast_moving_average(df)
    c[1] = int(float(c[1]))
    forecast_moving_average.extend(c)

    request.session['forecast_ses'] = forecast_ses
    request.session['forecast_hwes'] = forecast_hwes
    request.session['forecast_moving_average'] = forecast_moving_average
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
    else:
        request.session['forecast'] = None


    context = {
        'item': item,
        'forecast_ses': forecast_ses,
        'forecast_hwes': forecast_hwes,
        'forecast_moving_average': forecast_moving_average,
        'forecast_arima': forecast_arima,
    }
    return render(request, 'inventory/inventory_forecast_details.html', context)
