
from django import forms
from django.forms import ModelForm, ValidationError, Form, widgets
from production.models import JobOrder
from decimal import Decimal
from django.contrib.admin.widgets import AdminDateWidget

from .models import ClientItem, ClientPO, Product, Supplier, ClientPayment

class DateInput(forms.DateInput):
    input_type = 'date'

class ClientPOFormItems(ModelForm):
    client_po = forms.CharField(label='')
    laminate = forms.BooleanField(initial=True, required=False)

    class Meta:
        model = ClientItem
        fields = ('products', 'material_type', 'width', 'length', 'gusset', 'color', 'quantity', 'laminate')

    def __init__(self, *args, **kwargs):
        super(ClientPOFormItems, self).__init__(*args, **kwargs)
        self.fields['products'].label = 'Product Type'
        self.fields['products'].required = True
        self.fields['material_type'].label = 'Material'
        self.fields['material_type'].required = True
        self.fields['width'].required = True
        self.fields['length'].required = True
        self.fields['gusset'].required = True
        self.fields['color'].required = True
        self.fields['quantity'].required = True


class ClientPOForm(ModelForm):

    class Meta:
        model = ClientPO
        fields = ('date_required', 'other_info')
        widgets = {
            'date_required': DateInput()
        }

        def __init__(self, *args, **kwargs):
            super(ClientPOForm, self).__init__(*args, **kwargs)
            self.fields['date_required'].required = True
            self.fields['other_info'].required = False

class ClientPaymentForm(ModelForm):

    class Meta:
        model = ClientPayment
        fields = ('payment', 'payment_date')
        widgets = {
            'payment_date': DateInput()
        }

class SupplierForm(forms.ModelForm):

    company_name = forms.CharField(max_length=200, label = 'company_name', widget = forms.TextInput(
        attrs={'id':'company_name', 'name':'company_name', 'type':'text', 'required':'true'}
    ))
    contact_person = forms.CharField(max_length=200, label = 'contact_person', widget = forms.TextInput(
        attrs={'id':'contact_person', 'name':'contact_person', 'type':'text', 'required':'true'}
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
        fields = ('company_name', 'contact_person', 'mobile_number', 'email_address',
        'description')
    
    #class ClientPOForm(forms.ModelForm):
        