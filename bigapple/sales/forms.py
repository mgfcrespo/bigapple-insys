
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

        #widgets = {'date_required':DateTimePicker(options={"format": "YYYY-MM-DD", "pickSeconds": False}}


class SupplierForm(forms.ModelForm):
    DEPARTMENT = (
        ('Accounting and Finance', 'Accounting and Finance'),
        ('Human Resource', 'Human Resource'),
        ('Information Technology', 'Information Technology'),
        ('Marketing', 'Marketing'),
        ('Purchasing', 'Purchasing'),
        ('Research and Development', 'Research and Development'),
        ('Sales', 'Sales'),
        ('Others', 'Others'),
    )

    SUPPLIERTYPE = (
        ('Raw Material', 'Raw Material'),
        ('Machinery/Parts', 'Machinery/Parts'),
        ('Ink', 'Ink'),
        ('Others', 'Others'),
    )

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
    supplier_type = forms.CharField(max_length=200, label = 'supplier_type', widget = forms.Select(choices=SUPPLIERTYPE,
        attrs={'id':'supplier_type', 'name':'supplier_type', 'type':'text', 'required':'true'}
    ))
    
    class Meta:
        model = Supplier
        fields = ('company_name', 'contact_person', 'mobile_number', 'email_address',
        'description', 'supplier_type')
    
    #class ClientPOForm(forms.ModelForm):
        