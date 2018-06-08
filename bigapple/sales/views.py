from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import ClientItem, ClientPO, ClientCreditStatus, Client
from django.shortcuts import render, reverse, HttpResponseRedirect

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
    template_name = 'sales/clientPO_list.html'

    def get_queryset(self):
        return ClientPO.objects.all()


class PODetailView(generic.DetailView):
    model = ClientPO
    template_name = 'sales/clientPO_detail.html'


class POFormCreateView(CreateView):
    model = ClientItem
    template_name = 'sales/clientPO_form.html'
    fields = ('products', 'note', 'width', 'length', 'color', 'gusset', 'quantity')
