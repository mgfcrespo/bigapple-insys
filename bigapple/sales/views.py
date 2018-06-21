
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


# Create your views here.
def sales_details(request):
    context = {
        'title': 'Sales Content'
    }

    return render(request, 'sales/sales_details.html', context)


def supplier_list(request):
    query = Supplier.objects.all()
    context = {
        'query' : query,
    }
    return render(request, 'sales/supplier_list.html', context)


def add_supplier(request):
    query = Supplier.objects.all() 
    context = {
        'title' : "New Supplier",
        'actiontype' : "Add",
        'query' : query,
    }

    if request.method == 'POST':
        company_name = request.POST['company_name']
        contact_person = request.POST['contact_person']
        department = request.POST['department']
        mobile_number = request.POST['mobile_number']
        email_address = request.POST['email_address']
        supplier_type = request.POST['supplier_type']
        description = request.POST['description']

        result = Supplier(company_name=company_name, contact_person=contact_person, department=department,
        mobile_number=mobile_number, email_address=email_address, supplier_type=supplier_type, description=description)
        result.save()
        return HttpResponseRedirect('../supplier_list')
    
    else:
        return render(request, 'sales/add_supplier.html', context)

def edit_supplier(request, id):
    supplier = Supplier.objects.get(id=id)
    
    context = {
        'title' : "Edit Supplier",
        'actiontype' : "Edit",
        'supplier' : supplier,
    }

    return render(request, 'sales/edit_supplier.html/', context)

def delete_supplier(request, id):
    supplier = Supplier.objects.get(id=id)
    supplier.delete()
    return HttpResponseRedirect('../supplier_list')

class POListView(generic.ListView):
    model = ClientPO
    all_PO = ClientPO.objects.all()
    template_name = 'sales/clientPO_list.html'

class PODetailView(DetailView):
    model = ClientPO
    template_name = 'sales/clientPO_details.html'


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
    clientpo_item_formset = inlineformset_factory(ClientPO, ClientItem, form=ClientPOFormItems, extra=2, can_delete=True)
    if request.method == "POST":
        form = ClientPOForm(request.POST)

        new_form = form.save()
        new_form = new_form.pk
        form_instance = ClientPO.objects.get(id=new_form)

        if (form.is_valid()):
            formset = clientpo_item_formset(request.POST, instance=form_instance)

        if (formset.is_valid()):
            for form in formset:
                form.save()

            formset_items = ClientItem.objects.filter(client_po_id = new_form)
            formset_item_total = formset_items.aggregate(sum=aggregates.Sum('item_price'))['sum'] or 0

            totalled_clientpo = ClientPO.objects.get(id=new_form)
            totalled_clientpo.total_amount = formset_item_total
            totalled_clientpo.save()
            message = "Thank you"


        else:
            message = "Forms are not valid"


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

    #def get_queryset(self):
    #return JobOrder.objects.all()


