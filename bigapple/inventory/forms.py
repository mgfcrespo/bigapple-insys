from django import forms
from django.forms import ModelForm, ValidationError, Form, widgets
from django.contrib.admin.widgets import AdminDateWidget
from .models import Supplier, SupplierItems

class SupplierItemsForm(forms.ModelForm):
    
    ITEM_TYPES = (
        ('RM', 'Raw Materials'),
        ('MP', 'Machine Parts'),
        ('INK', 'Ink'),
        ('OT', 'Others')
    )

    #supplier_choices = forms.ChoiceField(choices=[])
    # def __init__(self, user, *args, **kwargs):
    #     super(SupplierItemsForm, self).__init__(*args, **kwargs)
    # self.fields['supplier'] 

    # sup = Supplier.objects.all()
    # supplier = forms.ChoiceField(label = 'item_name', widget = forms.Select(choices=sup))

   
    supplier = forms.CharField(label = 'supplier', widget = forms.Select(
        attrs={'id':'supplier', 'name':'supplier', 'type':'text', 'required':'true'}
    ))

    item_name = forms.CharField(max_length=200, label = 'item_name', widget = forms.TextInput(
        attrs={'id':'item_name', 'name':'item_name', 'type':'text', 'required':'true'}
    ))
    item_type = forms.CharField(max_length=200, label = 'item_name', widget = forms.Select(choices=ITEM_TYPES,
        attrs={'id':'item_type', 'name':'item_type', 'type':'text', 'required':'true'}
    ))
    description = forms.CharField(max_length=200, label = 'description', widget = forms.TextInput(
        attrs={'id':'description', 'name':'description', 'type':'text', 'required':'true'}
    ))
    price = forms.CharField(max_length=200, label = 'price', widget = forms.TextInput(
        attrs={'id':'price', 'name':'price', 'type':'number', 'required':'true'}
    ))

    

    class Meta:
        model = SupplierItems
        fields = ('supplier', 'item_name', 'item_type', 'description', 'price')


