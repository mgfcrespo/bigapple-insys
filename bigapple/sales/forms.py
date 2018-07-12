
from django import forms
from django.forms import ModelForm, ValidationError, Form, widgets
from production.models import JobOrder

from .models import ClientItem, ClientPO, Product, Client
from decimal import Decimal
from django.contrib.admin.widgets import AdminDateWidget

from .models import ClientItem, ClientPO, Product, Supplier

class DateInput(forms.DateInput):
    input_type = 'date'

class ClientPOFormItems(ModelForm):
    client_po = forms.CharField(label='')
    laminate = forms.BooleanField(initial=True, required=False)

    class Meta:
        model = ClientItem
        fields = ('products', 'width', 'length', 'gusset', 'color', 'quantity', 'laminate')

    def __init__(self, *args, **kwargs):
        super(ClientPOFormItems, self).__init__(*args, **kwargs)
        self.fields['products'].label = 'Product Type'


class ClientPOForm(ModelForm):

    class Meta:
        model = ClientPO
        fields = ('payment_terms', 'date_required', 'other_info')
        widgets = {
            'date_required': DateInput(),
        }

class SupplierForm(forms.ModelForm):

    company_name = forms.CharField(max_length=200, label = 'company_name', widget = forms.TextInput(
        attrs={'id':'company_name', 'name':'company_name', 'type':'text', 'required':'true'}
    ))
    first_name = forms.CharField(max_length=200, label = 'first_name', widget = forms.TextInput(
        attrs={'id':'first_name', 'name':'first_name', 'type':'text', 'required':'true'}
    ))
    last_name = forms.CharField(max_length=200, label = 'last_name', widget = forms.TextInput(
        attrs={'id':'last_name', 'name':'last_name', 'type':'text', 'required':'true'}
    ))
    mobile_number = forms.CharField(max_length=11, label = 'mobile_number', widget = forms.TextInput(
        attrs={'id':'mobile_number', 'name':'mobile_number', 'type':'number', 'required':'true'}
    ))
    email_address = forms.CharField(max_length=200, label = 'email_address', widget = forms.TextInput(
        attrs={'id':'email_address', 'name':'email_address', 'type':'email', 'required':'true'}
    ))
    description = forms.CharField(max_length=200, label = 'description', widget = forms.TextInput(
        attrs={'id':'description', 'name':'description', 'type':'text', 'required':'false'}
    ))
    
    class Meta:
        model = Supplier
        fields = ('company_name', 'first_name', 'last_name', 'mobile_number', 'email_address',
        'description')
    
    #class ClientPOForm(forms.ModelForm):
        