
from django import forms
from django.forms import ModelForm, ValidationError, Form, widgets
from production.models import JobOrder
from decimal import Decimal
from django.contrib.admin.widgets import AdminDateWidget

from .models import ClientItem, ClientPO, Product, Supplier, ClientPayment
from accounts.models import Client, Employee

class DateInput(forms.DateInput):
    input_type = 'date'

class ClientPOFormItems(ModelForm):
    client_po = forms.CharField(label='')
    laminate = forms.BooleanField(initial=True, required=False)
    printed = forms.BooleanField(initial=True, required=False)

    class Meta:
        model = ClientItem
        fields = ('products', 'width', 'length', 'thickness', 'gusset', 'color', 'quantity', 'laminate', 'printed', 'color_quantity')
        help_texts = {'color_quantity': "Only fill this if printed is checked"}

    def __init__(self, *args, **kwargs):
        super(ClientPOFormItems, self).__init__(*args, **kwargs)
        self.fields['products'].label = 'Material Type'
        self.fields['products'].required = True
        self.fields['width'].required = True
        self.fields['width'].label = 'Width(inches)'
        self.fields['length'].required = True
        self.fields['length'].label = 'Length(inches)'
        self.fields['thickness'].required = True
        self.fields['thickness'].label = 'Thickness(inches)'
        self.fields['gusset'].required = False
        self.fields['color'].required = True
        self.fields['quantity'].required = True
        self.fields['color_quantity'].required = False
        self.fields['color_quantity'].label = 'No. of Printing Colors'

    class Media:
        js = ('/static/create_po.js',)

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
            self.fields['date_required'].label = "Date Required"
            self.fields['other_info'].required = False
            self.fields['other_info'].label = "Other Info"


class ClientPaymentForm(ModelForm):

    class Meta:
        model = ClientPayment
        fields = ('payment', 'payment_date')
        widgets = {
            'payment_date': DateInput()
        }
class SupplierForm(forms.ModelForm):

    class Meta:
        model = Supplier
        fields = ('company_name', 'first_name', 'last_name', 'mobile_number', 'email_address',
        'description')
    
    mobile_number = forms.CharField(max_length=11)
    description = forms.CharField(required = False, widget = forms.Textarea(attrs={'rows':'3'}))

class ClientForm(forms.ModelForm):
    
    class Meta:
        model = Client
        fields = ('first_name', 'last_name', 'company', 'address', 'email', 'contact_number', 'tin',
         'sales_agent')

        
    contact_number = forms.CharField(max_length=11)
    sales_agent = forms.ModelChoiceField(queryset=Employee.objects.all())
        
    def __init__(self, *args, **kwargs):
        super(ClientForm, self).__init__(*args, **kwargs)
        self.fields['tin'].required = False
        self.fields['sales_agent'].queryset = Employee.objects.filter(position='Sales Agent')
  
class EmployeeForm(forms.ModelForm):
    POSITION = (
        ('General Manager', 'General Manager'),
        ('Sales Coordinator', 'Sales Coordinator'),
        ('Sales Agent', 'Sales Agent'),
        ('Credits and Collection Personnel', 'Credits and Collection Personnel'),
        ('Supervisor', 'Supervisor'),
        ('Line Leader', 'Line Leader'),
        ('Production Manager', 'Production Manager'),
        ('Cutting', 'Cutting'),
        ('Printing', 'Printing'),
        ('Extruder', 'Extruder'),
        ('Delivery', 'Delivery'),
        ('Warehouse', 'Warehouse'),
        ('Utility', 'Utility'),
        ('Maintenance', 'Maintenance'),

    )

    class Meta:
        model = Employee
        fields = ('first_name', 'last_name', 'birth_date', 'address', 'email', 'contact_number', 'sss',
        'philhealth', 'pagibig', 'tin', 'position')
        widgets = {
            'birth_date': DateInput()
        }

    contact_number = forms.CharField(max_length=11)
    position = forms.CharField(widget = forms.Select(choices=POSITION))

    def __init__(self, *args, **kwargs):
        super(EmployeeForm, self).__init__(*args, **kwargs)
        self.fields['sss'].required = False
        self.fields['philhealth'].required = False
        self.fields['pagibig'].required = False
        self.fields['tin'].required = False
    
    #class ClientPOForm(forms.ModelForm):
        