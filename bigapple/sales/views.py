<<<<<<< HEAD
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from .models import ClientItem, ClientPO, ClientCreditStatus, Client, Product
from django.shortcuts import render
from .forms import ClientPOFormItems, ClientPOForm
from django.urls import reverse_lazy
from django.forms import formset_factory, inlineformset_factory
=======
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import ClientItem, ClientPO, ClientCreditStatus, Client
from django.shortcuts import render, reverse, HttpResponseRedirect
>>>>>>> a9bf0b8dbe9542f09e4a6e4318e3d5f45e3fae7e

# Create your views here.
def sales_details(request):
    context = {
        'title': 'Sales Content'
    }

    return render(request, 'sales/sales_details.html', context)

<<<<<<< HEAD
class POListView(ListView):
=======

def add_supplier(request):
    context = {
        'title': 'Add Supplier'
    }

    return render(request, 'sales/add_supplier.html', context)

class POListView(generic.ListView):
>>>>>>> a9bf0b8dbe9542f09e4a6e4318e3d5f45e3fae7e
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


def display_client_po(request):
    clientpo_item_formset = inlineformset_factory(ClientPO, ClientItem, form=ClientPOFormItems, extra=1)
    if request.method == "POST":
        form = ClientPOForm(request.POST)
        if (form.is_valid()):
            message = "Thank you"
            form.save()

        formset = clientpo_item_formset(request.POST, instance=form)


        if (formset.is_valid()):
            form.save()
            message = "Thank you"
            for form in formset:
                print(form)
                form.save()
        else:
            form = ClientPOForm()
            formset = clientpo_item_formset(instance=ClientPO)
            message = "Something went wrong"


        return render(request, 'index.html',
                              {'message': message}
                              )
    else:
        return render(request, 'sales/clientPO_form.html',
                              {'formset': clientpo_item_formset(),
                               'form': ClientPOForm}
                              )
