from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView, ListView
from .models import ClientItem, ClientPO, ClientCreditStatus, Client, Product
from django.shortcuts import render, redirect
from .forms import ClientPOFormItems, ClientPOForm
from django.urls import reverse_lazy
from django.forms import formset_factory, inlineformset_factory

from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import render, reverse, HttpResponseRedirect, HttpResponse
from django.db.models import aggregates
from production.models import JobOrder
from .models import Supplier, ClientItem, ClientPO, ClientCreditStatus, Client, SalesInvoice
from .forms import ClientPOForm, SupplierForm
import sys


'''
# #Forecasting imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
from math import sqrt
from matplotlib.pylab import rcParams
rcParams['figure.figsize'] = 15, 6
'''

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
        'actiontype' : "Add",
    }
    return render(request, 'sales/supplier_add.html', context)



def supplier_list(request):
    supplier = Supplier.objects.all()
    context = {
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
        'actiontype' : "Edit",
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
        client_po = ClientPO.objects.get(id=id)

        context = {
            'title': "Edit Purchase Order",
            'actiontype': "Edit",
            'client_po': client_po,
        }

        return render(request, 'sales/edit_clientPO.html/', context)

def delete_clientPO(request, id):
        client_po = ClientPO.objects.get(id=id)
        client_po.delete()
        return HttpResponseRedirect('../clientPO_list')


# List views
class POListView(ListView):
    template_name = 'sales/clientPO_list.html'
    print(sys.path)

    def get_queryset(self):
        return ClientPO.objects.all()


class PODetailView(DetailView):
    model = ClientPO
    template_name = 'sales/clientPO_detail.html'

    '''
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    '''

'''
#Example for simple modelforms(for testing)
class POFormCreateView(FormView):
    form_class = ClientPOForm

class POFormCreateView(CreateView):
    model = ClientItem
    template_name = 'sales/clientPO_form.html'
    success_url = reverse_lazy('accounts:user-page-view')

    def form_valid(self, form):
        form.save()
        return super(POFormCreateView, self).form_valid(form)
'''

#SAMPLE DYNAMIC FORM
def create_client_po(request):
    #note:instance should be an object
    clientpo_item_formset = inlineformset_factory(ClientPO, ClientItem, form=ClientPOFormItems, extra=1, can_delete=True)


    if request.method == "POST":
        form = ClientPOForm(request.POST)
        message = ""
        print(form)
        if form.is_valid():
            new_form = form.save()
            new_form = new_form.pk
            form_instance = ClientPO.objects.get(id=new_form)


            formset = clientpo_item_formset(request.POST, instance=form_instance)
            print(formset)
            if formset.is_valid():
                for form in formset:
                    form.save()

                formset_items = ClientItem.objects.filter(client_po_id = new_form)
                formset_item_total = formset_items.aggregate(sum=aggregates.Sum('item_price'))['sum'] or 0

                totalled_clientpo = ClientPO.objects.get(id=new_form)
                totalled_clientpo.total_amount = formset_item_total
                totalled_clientpo.save()
                message = "PO successfully created"

            else:
                message += "Formset error"

        else:
            message = ""


        #todo change index.html. page should be redirected after successful submission
        return render(request, 'index.html',
                              {'message': message}
                              )
    else:
        return render(request, 'sales/clientPO_form.html',
                              {'formset': clientpo_item_formset(),
                               'form': ClientPOForm}
                              )



class JOListView(generic.ListView):
    model = JobOrder
    all_JO = JobOrder.objects.all()
    template_name = 'sales/JO_list.html'

    for JobOrder in all_JO:
        client_items = ClientItem.objects.filter(client_po_id=JobOrder.client_po.id)


class ClientCreditStatusListView(ListView):
    model = ClientCreditStatus
    all_credit_status = ClientCreditStatus.objects.all()
    template_name = 'sales/client_payment_monitoring.html'


'''
class RushOrderListView(generic.ListView):
    model = ClientPO
    all_rush_order = ClientPO.objects.get(ClientPO.lead_time<=14)
    template_name = 'sales/rush_order_list.html'
'''


#SALES INVOICE CRUD
def sales_invoice_list(request):
    sales_invoice = SalesInvoice.objects.all()
    context = {
        'sales_invoice' : sales_invoice 
    }
    return render (request, 'sales/sales_invoice_list.html', context)

def sales_invoice_details(request, id):
    sales_invoice = SalesInvoice.objects.get(id=id)
  
    context = {
        'sales_invoice' : sales_invoice,
        'title' : sales_invoice.id,
    }
    return render(request, 'sales/sales_invoice_details.html', context)

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
