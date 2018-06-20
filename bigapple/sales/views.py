from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import ClientItem, ClientPO, ClientCreditStatus, Client
from django.shortcuts import render, reverse, HttpResponseRedirect
from bigapple.apps.production.models import JobOrder

# Create your views here.
def sales_details(request):
    context = {
        'title': 'Sales Content'
    }

    return render(request, 'sales/sales_details.html', context)


def add_supplier(request):
    context = {
        'title': 'Add Supplier'
    }

    return render(request, 'sales/add_supplier.html', context)

class POListView(generic.ListView):
    model = ClientPO
    all_PO = ClientPO.objects.all()
    template_name = 'sales/clientPO_list.html'

class PODetailView(generic.DetailView):
    model = ClientPO
    template_name = 'sales/clientPO_details.html'


class POFormCreateView(CreateView):
    model = ClientItem
    template_name = 'sales/clientPO_form.html'
    fields = ('products', 'note', 'width', 'length', 'color', 'gusset', 'quantity')

class JOListView(generic.ListView):
    model = JobOrder
    all_JO = JobOrder.objects.all()
    template_name = 'sales/JO_list.html'

