from django.views import generic
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from .models import ClientItem, ClientPO, ClientCreditStatus, Client
from django.shortcuts import render
from .forms import ClientPOForm, ClientPOFormset
from django.urls import reverse_lazy, reverse

# Create your views here.
def sales_details(request):
    context = {
        'title': 'Sales Content'
    }

    return render(request, 'sales/sales_details.html', context)

class POListView(generic.ListView):
    template_name = 'sales/clientPO_list.html'

    def get_queryset(self):
        return ClientPO.objects.all()


class PODetailView(generic.DetailView):
    model = ClientPO
    template_name = 'sales/clientPO_detail.html'


class POFormCreateView(FormView):
    form_class = ClientPOForm
    template_name = 'sales/clientPO_form.html'
    fields = ('products', 'note', 'width', 'length', 'color', 'gusset', 'quantity')
    success_url = reverse_lazy('accounts:user-page-view')

    def form_valid(self, form):
        form.save()
        return super(POFormCreateView, self).form_valid(form)


class POFormsetCreateView(FormView):
    form_class = ClientPOFormset
    template_name = 'sales/clientPO_form.html'


