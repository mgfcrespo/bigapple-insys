from datetime import datetime, date, timedelta

from django.db import connection
from django.db.models import aggregates, Sum, Count
from django.forms import inlineformset_factory
from django.shortcuts import redirect
from django.shortcuts import render, HttpResponseRedirect, HttpResponse, Http404
from pandas import DataFrame

from accounts.models import Employee
from inventory.forms import MaterialRequisitionForm, SupplierPOForm, SupplierPOItemsForm
from inventory.models import Inventory, Supplier, MaterialRequisition, SupplierPO, SupplierPOItems
from production.forms import ClientPOForm
from production.models import JobOrder
from utilities import TimeSeriesForecasting, final_gantt
from .forms import ClientPOFormItems
from .forms import SupplierForm, ClientPaymentForm, EmployeeForm, ClientForm
from .models import ClientItem, Client, SalesInvoice, ClientPayment, ProductionCost, Product

import pandas as pd
from django.db.models import Q


#Forecasting imports
#import numpy as np
#from math import sqrt
#import pandas as pd
#import pandas._libs.tslibs.timedeltas
#import matplotlib.pyplot as plt
#from sklearn.metrics import mean_squared_error
#from matplotlib.pylab import rcParams
#rcParams['figure.figsize'] = 15, 6


# Create your views here.
# CRUD SUPPLIER
def supplier_add(request):
    form = SupplierForm(request.POST)
    if request.method == 'POST':
        HttpResponse(print(form.errors))
        if form.is_valid():
            form.save()
            return redirect('sales:supplier_list')

    context = {
        'form' : form,
        'title' : "Add Supplier",
        'actiontype' : "Submit",
    }
    return render(request, 'sales/supplier_add.html', context)

def supplier_list(request):
    supplier = Supplier.objects.all()
    context = {
        'title': 'Supplier List',
        'supplier' : supplier 
    }
    return render (request, 'sales/supplier_list.html', context)

def supplier_edit(request, id):
    supplier = Supplier.objects.get(id=id)
    form = SupplierForm(request.POST or None, instance=supplier)

    if form.is_valid():
        form.save()
        return redirect('sales:supplier_list')
    
    context = {
        'form' : form,
        'supplier' : supplier,
        'title' : "Edit Supplier",
        'actiontype' : "Submit",
    }
    return render(request, 'sales/supplier_add.html', context)

def supplier_delete(request, id):
    supplier = Supplier.objects.get(id=id)
    supplier.delete()
    return redirect('sales:supplier_list')
    
# CRUD PO
'''
def add_clientPO(request):
        query = ClientPO.objects.all()
        context = {
            'title': "New Purchase Order",
            'actiontype': "Add",
            'query': query,
        }

        if request.method == 'POST':
            date_issued = request.POST['date_issued']
            date_required = request.POST['date_required']
            terms = request.POST['terms']
            other_info = request.POST['other_info']
            client = request.POST[Client] #modify, get Client.name
            client_items = request.POST.getlist('client_items') #modify, make loop for item list
            total_amount = request.POST['total_amount'] #system should calculate; NOT AN INPUT
            laminate = request.POST['laminate']
            confirmed = request.POST['confirmed']

            result = ClientPO(date_issued=date_issued, date_required=date_required, terms=terms, other_info=other_info, client=client, client_items=client_items
                              total_amount=total_amount, laminate=laminate, confirmed=confirmed)
            result.save()
            return HttpResponseRedirect('../clientPO_list')

        else:
            return render(request, 'sales/clientPO_form.html', context)
'''

def edit_clientPO(request, id):
        client_po = JobOrder.objects.get(id=id)

        context = {
            'title': "Edit Purchase Order",
            'actiontype': "Submit",
            'client_po': client_po,
        }

        return render(request, 'sales/edit_clientPO.html/', context)

def delete_clientPO(request, id):
        client_po = JobOrder.objects.get(id=id)
        client_po.delete()
        return HttpResponseRedirect('../clientPO_list')

# PO List/Detail view + PO Confirm

def po_list_view(request):
    user = request.user
    id = user.id
    client = Client.objects.filter(accounts_id = id)
    employee = Employee.objects.filter(accounts_id = id)
    x = ''
    if client:
        client_po = JobOrder.objects.filter(client = Client.objects.get(accounts_id = id))
        x = 'Client'
    elif employee:
        x = 'Employee'
        if Employee.objects.get(accounts_id = id).position == "Sales Coordinator" or "General Manager":
            client_po = JobOrder.objects.all()
        #TODO: Sales Agent access level
        elif employee.position == "Sales Agent":
            customer = Client.objects.filter(sales_agent = employee)
            po = JobOrder.objects.all()
            client_po = []
            #for each in customer:
             #   for every in po:
              #      if every.client == each:
               #         client_po.append(every)

    context = {
        'title' : "Client Purchase Orders",
        'client_po' : client_po,
        'x' : x
    }

    return render(request, 'sales/clientPO_list.html', context)

def po_detail_view(request, pk):
    client_po = JobOrder.objects.get(pk=pk)

    context = {'client_po': client_po,
               'pk' : pk}

    return render(request, 'sales/clientPO_detail.html', context)


def confirm_client_po(request, pk):
    clientpo = JobOrder.objects.get(pk=pk)
    client = clientpo.client
    items = ClientItem.objects.filter(client_po = clientpo)
    supplierpo_item_formset = None

    # credit status
    if client.overdue_balance > 0:
        client.credit_status = 1
        credit_status = True
    else:
        client.credit_status = 0
        credit_status = False

    #matreq determinant
    products = []
    material = []
    cylinder_count = 0
    color = ''

    matreq = False
    for each in items:
        products.append(each.products)
        material.append(each.products.material_type)
        for x in material:
            inventory = Inventory.objects.filter(rm_type=x)
            if inventory.exists():
                for y in inventory:
                    if y.quantity > each.quantity/1000:
                        matreq = True
                    else:
                        matreq = False
                        break
                        break
            else:
                inventory = None
                matreq = False
                break
                break
        if each.printed == 1:
            cylinder_count = int(each.quantity/10000)
            ink = Inventory.objects.filter(Q(item_type='Ink') & Q(item=each.color))
            if ink.exists():
                color = str(each.color)
                color_count = int(each.quantity/2500)
                matreq = True
            else:
                matreq = False
                break
                break

    #matreq form
    if request.method == "POST":
        supplier = Supplier.objects.get(id=2)
        delivery_date = date.today() + timedelta(days=7)
        item = Inventory.objects.get(item='Generic Cylinder')
        supplierpo_item_formset = inlineformset_factory(SupplierPO, SupplierPOItems, form=SupplierPOItemsForm, extra=1,
                                                        can_delete=True)
        form = SupplierPO(supplier=supplier, delivery_date=delivery_date, date_issued=date.today())
        form.save()
        form_item = SupplierPOItems(supplier_po = form, item=item, quantity=cylinder_count)
        form_item.save()
        form.total_amount = form_item.total_price
        form.save()

        if matreq:
            clientpo.status = "On Queue"
            clientpo.save()

            for every in items:
                for x in material:
                    form1 = MaterialRequisitionForm(request.POST)
                    if form1.is_valid():
                        new_form = form1.save(commit=False)
                        new_form.client_item = every
                        new_form.item = Inventory.objects.filter(rm_type=x).first()
                        new_form.quantity = every.quantity/1000 #TODO: Ensure quantity (raw mat to product ratio)
                        new_form.save()

                        #matreq = MaterialRequisition.objects.get(id = new_form.pk)
                        #matreq.client_item = every
                        #matreq.item = Inventory.objects.filter(rm_type=x).first()
                        #matreq.save()

                    print(form)

            if each.printed == 1:
                form2 = MaterialRequisitionForm(request.POST)
                if form2.is_valid():
                        ink_form = form2.save(commit=False)
                        ink_form.client_item = every
                        ink_form.item = Inventory.objects.get(item=color)
                        ink_form.quantity = color_count
                        ink_form.save()

            return redirect('sales:po-list-view')


    context = {
        'clientpo': clientpo,
        'pk' : pk,
        'client' : client,
        'matreq' : matreq,
        'credit_status' : credit_status,
        'formset': supplierpo_item_formset,
    }

    return render(request, 'sales/clientPO_confirm.html', context)

#Invoice List/Detail View
def invoice_list_view(request):

    invoice = SalesInvoice.objects.filter(date_issued__isnull=False)

    if request.session['session_position'] == "Sales Coordinator":
        template = 'sales_coordinator_page.html'
    elif request.session['session_position'] == "Sales Agent":
        template = 'sales_agent_page.html'
    elif request.session['session_position'] == "Credits and Collection Personnel":
        template = 'credit_and_collection_personnel_page.html'
    elif request.session['session_position'] == "General Manager":
        template = 'general_manager_page.html'
    elif request.session['session_position'] == 'Client':
        invoice = SalesInvoice.objects.filter(Q(date_issued__isnull=False) & Q(client_id=request.session['session_userid']))
        template = 'client_page.html'


    else:
        template = 'error.html'

    context = {
     'invoice': invoice,
     'template': template
        }

    return render(request, 'sales/sales_invoice_list.html', context)

def invoice_detail_view(request, pk):

    sales_invoice = SalesInvoice.objects.get(pk=pk)
    #form = ClientPaymentForm()
    payments = ClientPayment.objects.filter(invoice_id=sales_invoice.id)

    try:
        client = Client.objects.get(id=sales_invoice.client_id)
        client.save()
        sales_invoice.save()

        #form = add_payment(request, pk)

        client = Client.objects.get(id=sales_invoice.client_id)
        form = ClientPaymentForm(request.POST)

        if request.method == "POST":
            if form.is_valid():
                form = form.save(commit=False)
                form.client = client
                form.invoice = sales_invoice
                form.old_balance = sales_invoice.amount_due
                form.new_balance = form.old_balance - form.payment
                form.save()

                sales_invoice.total_paid += form.payment
                sales_invoice.amount_due -= form.payment
                client.outstanding_balance -= form.payment

            sales_invoice.save()
            client.save()

        if sales_invoice.amount_due <= 0.0 and sales_invoice.status != "Cancelled":
            sales_invoice.status = "Closed"
            sales_invoice.save()
        else:
            sales_invoice.status = "Open"
            sales_invoice.save()

            sales_invoice.save()

        payments = ClientPayment.objects.filter(invoice=sales_invoice)

        context = {'salesinvoice': sales_invoice,
                   'form' : form,
                   'payments' : payments,
                   'pk' : pk}

    except SalesInvoice.DoesNotExist:
        raise Http404("Sales Invoice does not exist")

    return render(request, 'sales/sales_invoice_details.html', context)


def add_payment(request, pk):
    sales_invoice = SalesInvoice.objects.get(pk=pk)
    client = Client.objects.get(id=sales_invoice.client_id)
    form = ClientPaymentForm(request.POST)

    if request.method == "POST":
        if form.is_valid():
            form = form.save(commit=False)
            form.client = client
            form.invoice = sales_invoice
            form.old_balance = sales_invoice.amount_due
            form.new_balance = form.old_balance - form.payment
            form.save()

            sales_invoice.total_paid += form.payment
            sales_invoice.amount_due -= form.payment
            client.outstanding_balance -= form.payment

        sales_invoice.save()
        client.save()

    return form

def payment_list_view(request):
    user = request.user
    id = user.id
    client = Client.objects.get(accounts_id=id)

    client = client
    sales_invoice = SalesInvoice.objects.filter(client=client)
    client_payment = ClientPayment.objects.filter(client = client)

    context = {
        'client' : client,
        'client_payment' : client_payment,
        'sales_invoice' : sales_invoice
    }

    return render(request, 'sales/client_payment_list.html', context)

def payment_detail_view(request, pk):
    sales_invoice = SalesInvoice.objects.get(pk=pk)
    sales_invoice_po = sales_invoice.client_po

    if sales_invoice.amount_due <= 0 and sales_invoice.status != "Cancelled":
        sales_invoice.status = "Closed"
    else:
        sales_invoice.status = "Open"


    sales_invoice.save()

    po = JobOrder.objects.get(id = sales_invoice_po.id)
    po_items = ClientItem.objects.filter(client_po = po)

    payments = ClientPayment.objects.filter(invoice_issued=sales_invoice)

    context = {'salesinvoice' : sales_invoice,
               'po' : po,
               'po_items' : po_items,
               'payments' : payments}

    return render(request, 'sales/client_payment_detail.html', context)

def statement_of_accounts_list_view(request):
    client = Client.objects.all()
    sales_invoice = SalesInvoice.objects.filter(date_issued__isnull=False)

    context = {
        'client' : client,
        'sales_invoice' : sales_invoice,
        'date' : datetime.now()
    }

    return render(request, 'sales/statement_of_accounts.html', context)

#SAMPLE DYNAMIC FORM
def create_client_po(request):
    #note: instance should be an object
    clientpo_item_formset = inlineformset_factory(JobOrder, ClientItem, form=ClientPOFormItems, extra=1, can_delete=True)
    form = ClientPOForm(request.POST)
    if request.method == "POST":
        message = ""
        print(form)
        if form.is_valid():
            #Save PO form then use newly saved ClientPO as instance for ClientPOItems
            new_form = form.save(commit=False)
            #Set ClientPO.client from session user
            client_id = request.session['session_userid']
            current_client = Client.objects.get(id=client_id)
            new_form.client = current_client
            new_form = form.save()
            form_id = new_form.pk
            form_instance = JobOrder.objects.get(id=form_id)

            #Use PO form instance for PO items
            formset = clientpo_item_formset(request.POST, instance=form_instance)
            print(formset)
            if formset.is_valid():
                for form in formset:
                    form.save()
                formset_items = ClientItem.objects.filter(client_po_id = form_id)
                formset_item_total = formset_items.aggregate(sum=aggregates.Sum('item_price'))['sum'] or 0

                #totalled_clientpo = JobOrder.objects.get(id=form_id)
                form_instance.total_amount = formset_item_total
                form_instance.save()

                invoice = SalesInvoice(client=current_client, client_po=form_instance, total_amount=formset_item_total,
                                       amount_due=0)
                invoice.amount_due = invoice.calculate_total_amount_computed()
                invoice.save()

                #invoice = invoice.pk
                #invoice = SalesInvoice.objects.get(id=invoice)

                message = "PO successfully created"
                return redirect('sales:po-list-view')

            else:
                message += "Formset error"

        else:
            message = "Form is not valid"

        return render(request, 'accounts/client_page.html',
                              {'message': message}
                              )
    else:
        return render(request, 'sales/clientPO_form.html',
                              {'formset': clientpo_item_formset(),
                               'form': ClientPOForm}
                              )


#RUSH ORDER CRUD
def rush_order_list(request):
    rush_orders = JobOrder.objects.filter(rush_order = True).filter(status='Waiting')

    context = {
        'rush_orders' : rush_orders,
    }

    return render (request, 'sales/rush_order_list.html', context)

def rush_order_assessment(request, pk):
    rush_order = JobOrder.objects.get(pk=pk)
    client = rush_order.client

    if request.POST.get('approve_btn'):
        rush_order.status = 'On Queue'
        rush_order.save()
    elif request.POST.get('deny_btn'):
        rush_order.rush_order = 0
        rush_order.save()

    #credit status
    if client.overdue_balance > 0:
        client.credit_status = 1
        credit_status = True
    else:
        client.credit_status = 0
        credit_status = False

    #cost shit
    items = ClientItem.objects.filter(client_po = rush_order)
    mark_up = ProductionCost.objects.get(cost_type='Mark_up')
    electricity = ProductionCost.objects.get(cost_type='Electricity')

    for every in items:
        price = every.calculate_price_per_piece() * every.quantity
        profit = 0

        profit += (10000 * (
            every.calculate_price_per_piece()) - electricity.cost - (1600/every.quantity) - \
                   (300/every.quantity) - (
                               every.length * every.width * every.thickness )) / (
                              every.length * every.width * every.thickness )


    #matreq
    products = []
    material = []
    cylinder_count = 0
    color = ''

    matreq = False
    for each in items:
        products.append(each.products)
        material.append(each.products.material_type)
        for x in material:
            inventory = Inventory.objects.filter(rm_type=x)
            if inventory.exists():
                for y in inventory:
                    if y.quantity > each.quantity / 1000:
                        matreq = True
                    else:
                        matreq = False
                        break
                        break
            else:
                inventory = None
                matreq = False
                break
                break
        if each.printed == 1:
            cylinder_count = int(each.quantity / 10000)
            ink = Inventory.objects.filter(Q(item_type='Ink') & Q(item=each.color))
            if ink.exists():
                color = str(each.color)
                color_count = int(each.quantity / 2500)
                matreq = True
            else:
                matreq = False
                break
                break

    # matreq form
    if request.method == "POST":
        supplier = Supplier.objects.get(id=2)
        delivery_date = date.today() + timedelta(days=7)
        item = Inventory.objects.get(item='Generic Cylinder')
        supplierpo_item_formset = inlineformset_factory(SupplierPO, SupplierPOItems, form=SupplierPOItemsForm, extra=1,
                                                        can_delete=True)
        form = SupplierPO(supplier=supplier, delivery_date=delivery_date, date_issued=date.today())
        form.save()
        form_item = SupplierPOItems(supplier_po=form, item=item, quantity=cylinder_count)
        form_item.save()
        form.total_amount = form_item.total_price
        form.save()

        if matreq:
            clientpo.status = "On Queue"
            clientpo.save()

            for every in items:
                for x in material:
                    form1 = MaterialRequisitionForm(request.POST)
                    if form1.is_valid():
                        new_form = form1.save(commit=False)
                        new_form.client_item = every
                        new_form.item = Inventory.objects.filter(rm_type=x).first()
                        new_form.quantity = every.quantity / 1000  # TODO: Ensure quantity (raw mat to product ratio)
                        new_form.save()

                        # matreq = MaterialRequisition.objects.get(id = new_form.pk)
                        # matreq.client_item = every
                        # matreq.item = Inventory.objects.filter(rm_type=x).first()
                        # matreq.save()

                    print(form)

            form2 = MaterialRequisitionForm(request.POST)
            if form2.is_valid():
                ink_form = form2.save(commit=False)
                ink_form.client_item = every
                ink_form.item = Inventory.objects.get(item=color)
                ink_form.quantity = color_count
                ink_form.save()

    #TODO: Insert current job to generic schedule and show if other JOs will meet date_due
    #simulated sched
    cursor = connection.cursor()
    query = "SELECT j.id, i.laminate, i.printed, p.material_type FROM production_mgt_joborder j, sales_mgt_clientitem i, sales_mgt_product p " \
            "WHERE p.id = i.products_id and i.client_po_id = j.id and NOT j.status = 'Waiting' and " \
            "NOT j.status = 'Ready for delivery' and NOT j.status = 'Delivered'"
    cursor.execute(query)
    df = pd.read_sql(query, connection)
    data = {'id': pk,
            'laminate': each.laminate,
            'printed': each.printed,
            'material_type': x }
    df2 = pd.DataFrame(data, index=[0])
    print('df2: ')
    print(df2)
    df = df.append(df2, ignore_index=True)
    print('df after append: ')
    print(df)
    simulated_sched = final_gantt.generate_overview_gantt_chart(df)

    context = {
        'client': client,
        'rush_order' : rush_order,
        'credit_status' : credit_status,
        'matreq' : matreq,
        'cylinder_count' : cylinder_count,
        'profit': profit,
        'simulated_sched' : simulated_sched
    }

    return render(request, 'sales/rush_order_assessment.html', context)


#CLIENT CRUD
def client_add(request):
    form = ClientForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('sales:client_list')

    context = {
        'form' : form,
        'title' : "Add Client",
        'actiontype' : "Submit",
    }
    return render(request, 'sales/client_add.html', context)

def client_list(request):
    data = Client.objects.all()

    context = {
        'title' : 'Client List',
        'data' : data 
    }
    return render(request, 'sales/client_list.html', context)

def client_edit(request, id):
    data = Client.objects.get(id=id)
    form = ClientForm(request.POST or None, instance=data)

    if form.is_valid():
        form.save()
        return redirect('sales:client_list')
    
    context = {
        'form' : form,
        'data' : data,
        'title' : "Edit Client",
        'actiontype' : "Submit",
    }
    return render(request, 'sales/client_add.html', context)

#EMPLOYEE CRUD
def employee_add(request):
    form = EmployeeForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('sales:employee_list')

    context = {
        'form' : form,
        'title' : "Add Employee",
        'actiontype' : "Submit",
    }
    return render(request, 'sales/employee_add.html', context)

def employee_list(request):
    data = Employee.objects.all()
    context = {
        'title': 'Employee List',
        'data' : data 
    }
    return render(request, 'sales/employee_list.html', context)

def employee_edit(request, id):
    data = Employee.objects.get(id=id)
    form = EmployeeForm(request.POST or None, instance=data)
    if form.is_valid():
        form.save()
        return redirect('sales:employee_list')
    
    context = {
        'form' : form,
        'data' : data,
        'title' : "Edit Employee",
        'actiontype' : "Submit",
    }
    return render(request, 'sales/employee_add.html', context)

def employee_details(request, id):

    data = Employee.objects.get(id=id)

    form = EmployeeForm(request.POST or None, instance=data)
    if form.is_valid():
        form.save()
        return redirect('sales:employee_list')


    context = {
        'form':form,
        'data': data,
        'title': 'Employee Details'
    }

    return render(request, 'sales/employee_details.html', context)


def employee_delete(request, id):
    data = Employee.objects.get(id=id)
    data.delete()
    return redirect('sales:employee_list')

#FORECASTING

def demand_forecast(request):
    client = Client.objects.all()
    po = JobOrder.objects.all()

    context = {
        'client' : client,
        'po' : po,
    }
    return render(request, 'sales/client_demand_forecast.html', context)

#FIXME accdg to products_id
def most_common(lst):
    return max(set(lst), key=lst.count)

def demand_forecast_details(request, id):
    client_po = JobOrder.objects.filter(client_id=id)
    client = Client.objects.get(id=id)
    i = ClientItem.objects.all()
    items = []
    for every in i:
        for each in client_po:
            if every.client_po_id == each.id:
                items.append(every)

    item = most_common(items)
    p = item.products_id
    cursor = connection.cursor()
    forecast_ses = []
    forecast_hwes = []
    forecast_moving_average = []
    forecast_arima = []

    query = 'SELECT po.date_issued, poi.quantity FROM  production_mgt_joborder po, sales_mgt_clientitem poi WHERE ' \
            'po.client_id = '+str(id)+' AND poi.client_po_id = po.id AND poi.products_id = '+str(p)

    cursor.execute(query)
    df = pd.read_sql(query, connection)


    #forecast_decomposition.append(TimeSeriesForecasting.forecast_decomposition(df))
    a = TimeSeriesForecasting.forecast_ses(df)
    # print('BEFORE A', df)
    forecast_ses.extend(a)
    # print('BEFORE B', df)
    b = TimeSeriesForecasting.forecast_hwes(df)
    forecast_hwes.extend(b)
    c = TimeSeriesForecasting.forecast_moving_average(df)
    forecast_moving_average.extend(c)
    d = TimeSeriesForecasting.forecast_arima(df)
    forecast_arima.extend(d)

    context = {
        #'forecast_decomposition': forecast_decomposition,
        'forecast_ses': forecast_ses,
        'forecast_hwes': forecast_hwes,
        'forecast_moving_average': forecast_moving_average,
        'forecast_arima': forecast_arima,
        'item' : item,
        'client' : client
    }

    return render(request, 'sales/client_demand_forecast_details.html', context)