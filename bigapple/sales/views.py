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
#from utilities import TimeSeriesForecasting, ganttChart

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

    context = {'client_po': client_po}

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
    invoice = SalesInvoice.objects.all()

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
    payments = ClientPayment.objects.filter(invoice_issued=salesinvoice)

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

        payments = ClientPayment.objects.filter(invoice_issued=salesinvoice)

        context = {'salesinvoice': salesinvoice,
                   'form' : form,
                   'payments' : payments}

    except SalesInvoice.DoesNotExist:
        raise Http404("Sales Invoice does not exist")

    return render(request, 'sales/sales_invoice_details.html', context)


def add_payment(request, pk, *args, **kwargs):
    form = ClientPaymentForm()

    if request.method == "POST":
            form = ClientPaymentForm(request.POST)
            form = form.save()

            salesinvoice = SalesInvoice.objects.get(pk=pk)
            client = Client.objects.get(id = salesinvoice.client_id)

            payment = ClientPayment.objects.get(id=form.pk)
            payment.client = client
            payment.invoice_issued = salesinvoice

            payment.old_balance = salesinvoice.amount_due
            salesinvoice.amount_due -= payment.payment
            salesinvoice.total_paid += payment.payment
            payment.new_balance = payment.old_balance - payment.payment
            salesinvoice.amount_due = payment.new_balance

            salesinvoice.save()
            payment.save()
            client.save()

            form = ClientPaymentForm()
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

                # Create Invoice
                invoice = SalesInvoice(client=current_client, client_po=form_instance, total_amount=formset_item_total, amount_due=0)
                invoice.save()

                #TODO: Invoice should not be issued unless JO is complete

                invoice = SalesInvoice.objects.get(id=invoice.pk)
                invoice.amount_due = invoice.calculate_total_amount_computed
                invoice.save()

                outstanding_balance = current_client.outstanding_balance
                outstanding_balance += invoice.amount_due
                current_client.save()


                message = "PO successfully created"

            else:
                message += "Formset error"

        else:
            message = "Form is not valid"


        #TODO: change index.html. page should be redirected after successful submission
        return render(request, 'accounts/user-page-view.html',
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
    credit_status = Client.objects.all().values_list('credit_status', flat=True)

    #cost shit
    items = ClientItem.objects.filter(client_po = rush_order)
    #profit =

    #matreq
    products = []
    material = []
    for each in items:
        products.append(each.products)
        material.append(each.material_type)
    #TODO: get each item's material requirement
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

'''
#Forecasting view
def call_forecasting(request):
    ...

#DATASET QUERY
def query_dataset():
# Importing data
    df = pd.read_sql(ClientPO.objects.all())
    # Printing head
    df.head()


#TIME SERIES FORECASTING
# x = 'what is being forecasted' queryset
#y = time queryset
class Forecasting_Algo:
    def __init__(self, train_x, train_y, test_x, test_y):
        self.train_x = train_x
        self.train_y = train_y
        self.test_x = test_x
        self.test_y = test_y

    def naive_method(self):
        ...
    def simple_average(self):
        ...
    def moving_average(self):
        ...
    def single_exponential_smoothing(self):
        ...
    def linear_trend_method(self):
        ...
    def seasonal_method(self):
        ...
    def ARIMA(self):
        ...
'''
