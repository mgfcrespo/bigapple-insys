from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import ClientItem, ClientPO, ClientCreditStatus, Client


# Create your views here.
class POListView(generic.ListView):
    template_name = 'sales/clientPO_list.html'

    def get_queryset(self):
        return ClientPO.objects.all()


class PODetailView(generic.DetailView):
    model = ClientPO
    template_name = 'sales/clientPO_detail.html'


class POFormCreate(CreateView):
    model = ClientItem
    template_name = 'sales/clientPO_form.html'
    fields = ('products', 'note', 'width', 'length', 'color', 'gusset', 'quantity')
