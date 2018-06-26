
from django import forms
from django.forms import ModelForm, ValidationError, Form, widgets
from .models import ClientItem, ClientPO, Product, Client
from decimal import Decimal
from django.contrib.admin.widgets import AdminDateWidget




from .models import ClientItem, ClientPO, Product, Supplier


class ClientPOFormItems(ModelForm):
    client_po = forms.CharField(label='')
    laminate = forms.BooleanField(initial=True, widget=forms.CheckboxInput)

    class Meta:
        model = ClientItem
        fields = ('products', 'width', 'length', 'color', 'gusset', 'quantity', 'laminate')
        widgets = {
            'laminate': widgets.CheckboxInput(attrs={'class': 'required checkbox form-control'})
        }

    def __init__(self, *args, **kwargs):
        super(ClientPOFormItems, self).__init__(*args, **kwargs)
        for laminate in self.fields:
            self.fields[laminate].required = False

class ClientPOForm(ModelForm):

    class Meta:
        model = ClientPO
        fields = ('terms', 'other_info')




class AddSupplier_Form(Form):
    model = Supplier
    fields = ('company_name', 'contact_person', 'department', 'mobile_number', 'email_address',
    'supplier_type', 'description')

        

