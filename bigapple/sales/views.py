from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from .models import ClientItem, ClientPO, ClientCreditStatus, Client, Product
from django.shortcuts import render
from .forms import ClientPOFormItems, ClientPOForm
from django.urls import reverse_lazy
from django.forms import formset_factory, inlineformset_factory

from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import render, reverse, HttpResponseRedirect
from django.db.models import aggregates
from production.models import JobOrder
from .models import Supplier, ClientItem, ClientPO, ClientCreditStatus, Client
from .forms import AddSupplier_Form
from .forms import ClientPOForm


# Create your views here.
def sales_details(request):
    context = {
        'title': 'Sales Content'
    }

    return render(request, 'sales/sales_details.html', context)


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

# CRUD JO

# List views

class POListView(ListView):
    template_name = 'sales/clientPO_list.html'

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
    clientpo_item_formset = inlineformset_factory(ClientPO, ClientItem, form=ClientPOFormItems, extra=2, can_delete=True)

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

class ClientCreditStatusListView(generic.ListView):
    model = ClientCreditStatus
    all_credit_status = ClientCreditStatus.objects.all()
    template_name = 'sales/client_payment_monitoring.html'

'''
class RushOrderListView(generic.ListView):
    model = ClientPO
    all_rush_order = ClientPO.objects.get(ClientPO.lead_time<=14)
    template_name = 'sales/rush_order_list.html'
'''