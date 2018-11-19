from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView, ListView, FormView

from inventory.forms import MaterialRequisitionForm
from .models import ClientItem, Product
from django.shortcuts import render, redirect
from .forms import ClientPOFormItems
from django.urls import reverse_lazy
from django.forms import formset_factory, inlineformset_factory
from datetime import datetime, date
from django.http import JsonResponse

from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import render, reverse, HttpResponseRedirect, HttpResponse, Http404
from django.db.models import aggregates
from production.models import JobOrder
from .models import Supplier, ClientItem, Client, SalesInvoice, ClientPayment
from inventory.models import Inventory, Supplier, SupplierPO, SupplierPOItems
from accounts.models import Employee
from .forms import SupplierForm, ClientPaymentForm, EmployeeForm, ClientForm
from production.forms import ClientPOForm
from django.contrib.auth.models import User
from django import forms
import sys
from decimal import Decimal
from django.db import connection
from pandas import DataFrame
from utilities import TimeSeriesForecasting, ganttChart

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
        'supplier': supplier
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

    for every in items:
        price = every.calculate_price_per_piece() * every.quantity
        products = every.products
        material = products.material_type

        inventory = Inventory.objects.get(rm_type=material)
        quantity = inventory.quantity

        #TODO check for cylinder in matreq
        if quantity > 0:
            matreq = True
        else:
            matreq = False



    if request.method == "POST":
        clientpo.status = "On Queue"
        clientpo.save()

        for every in items:
            form = MaterialRequisitionForm(request.POST)
            form.client_item = every
            form.save()

            print(form)
            if form.is_valid():
                form.save()

        return redirect('sales:clientPO_list')


    context = {
        'clientpo': clientpo,
        'pk' : pk,
        'client' : client,
        'price' : price,
        'matreq' : matreq
    }

    return render(request, 'sales/clientPO_confirm.html', context)

#Invoice List/Detail View
def invoice_list_view(request):
    invoice = SalesInvoice.objects.filter(date_issued__isnull=False)

    if request.session['session_position'] == "Sales Coordinator":
        template = 'sales_coordinator_page_ui.html'
    elif request.session['session_position'] == "Sales Agent":
        template = 'sales_agent_page_ui.html'
    elif request.session['session_position'] == "Credits and Collection Personnel":
        template = 'credit_and_collection_personnel_page_ui.html'
    elif request.session['session_position'] == "General Manager":
        template = 'general_manager_page_ui.html'
    else:
        template = 'error.html'

    context = {
     'invoice': invoice,
     'template': template
        }

    return render(request, 'sales/sales_invoice_list.html', context)

def invoice_detail_view(request, pk, *args, **kwargs):

    salesinvoice = SalesInvoice.objects.get(pk=pk)
    form = ClientPaymentForm()
    payments = ClientPayment.objects.filter(invoice=salesinvoice)

    try:
        salesinvoice = SalesInvoice.objects.get(pk=pk)

        client = Client.objects.get(id=salesinvoice.client_id)
        client.save()
        salesinvoice.save()

        form = add_payment(request, pk, *args, **kwargs)

        if salesinvoice.amount_due <= 0 and salesinvoice.status != "Cancelled":
            salesinvoice.status = "Closed"
        else:
            salesinvoice.status = "Open"

        salesinvoice.save()

        payments = ClientPayment.objects.filter(invoice=salesinvoice)

        context = {'salesinvoice': salesinvoice,
                   'form' : form,
                   'payments' : payments,
                   'pk' : pk}

    except SalesInvoice.DoesNotExist:
        raise Http404("Sales Invoice does not exist")

    return render(request, 'sales/sales_invoice_details.html', context)


def add_payment(request, pk, *args, **kwargs):
    form = ClientPaymentForm()

    if request.method == "POST":
            form = ClientPaymentForm(request.POST)
            form = form.save()
            new_form = form.pk

            salesinvoice = SalesInvoice.objects.get(pk=pk)
            client = Client.objects.get(id = salesinvoice.client_id)

            payment = ClientPayment.objects.get(pk=new_form)
            payment.client = client
            payment.invoice = salesinvoice

            payment.old_balance = salesinvoice.amount_due
            salesinvoice.amount_due -= payment.payment
            salesinvoice.total_paid += payment.payment
            payment.new_balance = payment.old_balance - payment.payment
            salesinvoice.amount_due = payment.new_balance

            client.outstanding_balance -= payment.payment

            salesinvoice.save()
            payment.save()
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
    sales_invoice = SalesInvoice.objects.all()

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

    if request.method == "POST":

        form = ClientPOForm(request.POST)

        #Get session user id
        client_id = request.session['session_userid']
        current_client = Client.objects.get(id=client_id)
        form.client = current_client
        form.save()

        '''
        #check if client has overdue balance
        credit_status = ClientCreditStatus.objects.get(client_id = current_client)
        if (credit_status.outstanding_balance < 0):
            credit_status = 1
        '''

        message = ""
        print(form)
        if form.is_valid():
            #Save PO form then use newly saved ClientPO as instance for ClientPOItems
            new_form = form.save()
            new_form = new_form.pk
            form_instance = JobOrder.objects.get(id=new_form)

            #Set ClientPO.client from session user
            form_instance.client = current_client
            form_instance.save()

            #TODO: Invoice should no be saved if PO is disapproved

            #Create JO object with ClientPO as a field
            #jo = JobOrder(client_po = form_instance)
            #jo.save()

            #Use PO form instance for PO items
            formset = clientpo_item_formset(request.POST, instance=form_instance)
            #print(formset)
            if formset.is_valid():
                for form in formset:
                    form.save()

                formset_items = ClientItem.objects.filter(client_po_id = new_form)
                formset_item_total = formset_items.aggregate(sum=aggregates.Sum('item_price'))['sum'] or 0

                totalled_clientpo = JobOrder.objects.get(id=new_form)
                totalled_clientpo.client = current_client
                totalled_clientpo.total_amount = formset_item_total
                totalled_clientpo.save()

                invoice = SalesInvoice(client=current_client, client_po=form_instance, total_amount=formset_item_total,
                                       amount_due=0)
                invoice.save()

                #invoice = invoice.pk
                #invoice = SalesInvoice.objects.get(id=invoice)
                invoice.amount_due = invoice.calculate_total_amount_computed()
                invoice.save()

                message = "PO successfully created"

            else:
                message += "Formset error"

        else:
            message = "Form is not valid"


        #TODO: change index.html. page should be redirected after successful submission
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
    rush_orders = JobOrder.objects.filter(rush_order = True)

    context = {
        'rush_orders' : rush_orders,
    }

    return render (request, 'sales/rush_order_list.html', context)

def rush_order_assessment(request, pk):
    rush_order = JobOrder.objects.get(pk=pk)
    client = rush_order.client

    if request.POST.get('approve_btn'):
        rush_order.status = 'Approved'
    elif request.POST.get('deny_btn'):
        rush_order.save()

    #credit status
    if client.overdue_balance > 0:
        client.credit_status = 0
        credit_status = False
    else:
        client.credit_status = 1
        credit_status = True

    #cost shit
    items = ClientItem.objects.filter(client_po = rush_order)
    #profit =

    #matreq
    products = []
    material = []
    for each in items:
        products.append(each.products)
        material.append(each.material_type)
    #TODO: get each item's material requirement + CYLINDER
    inventory = Inventory.objects.get(rm_type=material)
    quantity = inventory.quantity

    if quantity > 0:
        matreq = True
    else:
        matreq = False

    #simulated sched

    context = {
        'rush_order' : rush_order,
        'credit_status' : credit_status,
        'matreq' : matreq,
        #'simulated_sched' : simulated_sched
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

def employee_delete(request, id):
    data = Employee.objects.get(id=id)
    data.delete()
    return redirect('sales:employee_list')

#FORECASTING
def demand_list(request):
    client = Client.objects.all()

    context = {
        'client' : client
    }
    return render(request, 'sales/client_demand_forecast.html', context)


def demand_forecast(request, id):
    client_po = JobOrder.objects.filter(client_id=id)
    items = []
    i = ClientItem.objects.all()
    for every in i:
        for each in client_po:
            if every.client_po_id == each.client_po.id:
                items.append(every)
    cursor = connection.cursor()
    query = 'SELECT po.date_issued, p.products FROM accounts_mgt_client c, production_mgt_joborder po, sales_mgt_clientitem poi, sales_product p WHERE' \
            'p.id = poi.products_id AND poi.client_po_id = po.id AND po.client_id = '+id

    get_data = cursor.execute(query)
    df = DataFrame(get_data.fetchall())
    df.columns = get_data.keys()
    forecast_decomposition = []
    forecast_ses = []
    forecast_hwes = []
    forecast_moving_average = []
    forecast_arima = []

    for x in items:
        forecast_decomposition.append(TimeSeriesForecasting.forecast_decomposition(df))
        forecast_ses.append(TimeSeriesForecasting.forecast_ses(df))
        forecast_hwes.append(TimeSeriesForecasting.forecast_hwes(df))
        forecast_moving_average.append(TimeSeriesForecasting.forecast_moving_average(df))
        forecast_arima.append(TimeSeriesForecasting.forecast_arima(df))

    context = {
        'forecast_decomposition': forecast_decomposition,
        'forecast_ses': forecast_ses,
        'forecast_hwes': forecast_hwes,
        'forecast_moving_average': forecast_moving_average,
        'forecast_arima': forecast_arima,
        'items' : items
    }

    return render(request, 'sales/client_demand_forecast_details.html', context)

