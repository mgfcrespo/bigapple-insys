
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from .models import ClientItem, ClientPO, ClientCreditStatus, Client, Product
from django.shortcuts import render
from .forms import ClientPOFormItems, ClientPOForm
from django.urls import reverse_lazy
from django.forms import formset_factory, inlineformset_factory

from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import ClientItem, ClientPO, ClientCreditStatus, Client
from django.shortcuts import render, reverse, HttpResponseRedirect
from django.db.models import aggregates

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


class PODetailView(DetailView):
    model = ClientPO
    template_name = 'sales/clientPO_detail.html'


'''
#Example for simple modelforms(for testing)
class POFormCreateView(FormView):
    form_class = ClientPOForm
    template_name = 'sales/clientPO_form.html'
    success_url = reverse_lazy('accounts:user-page-view')

    def form_valid(self, form):
        form.save()
        return super(POFormCreateView, self).form_valid(form)
'''

#SAMPLE DYNAMIC FORM
def display_client_po(request):
    #note:instance should be an object
    clientpo_item_formset = inlineformset_factory(ClientPO, ClientItem, form=ClientPOFormItems, extra=1, can_delete=True)
    if request.method == "POST":
        form = ClientPOForm(request.POST)

        new_form = form.save()
        new_form = new_form.pk
        form_instance = ClientPO.objects.get(id=new_form)

        if (form.is_valid()):
            message = "Thank you"
            formset = clientpo_item_formset(request.POST, instance=form_instance)

        if (formset.is_valid()):
            message = "Thank you"
            for form in formset:
                form.save()

            formset_items = ClientItem.objects.filter(client_po_id = new_form)
            formset_item_total = formset_items.aggregate(sum=aggregates.Sum('item_price'))['sum'] or 0

            totalled_clientpo = ClientPO.objects.get(id=new_form)
            totalled_clientpo.total_amount = formset_item_total
            totalled_clientpo.save()



        else:
            #form = ClientPOForm()
            #formset = clientpo_item_formset(instance=ClientPOform)
            message = "Forms are not valid"


        return render(request, 'index.html',
                              {'message': message}
                              )
    else:
        return render(request, 'sales/clientPO_form.html',
                              {'formset': clientpo_item_formset(),
                               'form': ClientPOForm}
                              )
