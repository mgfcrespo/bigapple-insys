from django import forms
from django.forms import ModelForm, ValidationError, Form, widgets
from django.contrib.admin.widgets import AdminDateWidget
from .models import Supplier, SupplierPO, SupplierPOItems, MaterialRequisition, Inventory, MaterialRequisitionItems
from datetime import date, datetime
from django.forms.formsets import BaseFormSet

# from django_select2.forms import ModelSelect2Widget
# from linked_select2.forms import LinkedModelSelect2Widget

class InventoryForm(forms.ModelForm):
    
    ITEM_TYPES = (
        ('Raw Materials', 'Raw Materials'),
        ('Machine Parts', 'Machine Parts'),
        ('Ink', 'Ink'),
        ('Others', 'Others')
    )

    RM_TYPES = (
        ('--', '----------------'),
        ('LDPE', 'Low-density polyethylene'),
        ('LLDPE', 'Linear low-density polyethylene'),
        ('HDPE', 'High-density polyethylene'),
        ('PP', 'Polypropylene'),
        ('PET', 'Polyethylene terephthalate')
    )

    supplier = forms.ModelChoiceField(queryset=Supplier.objects.all())

    item_type = forms.CharField(max_length=200, label = 'item_name', widget = forms.Select(choices=ITEM_TYPES))
    rm_type = forms.CharField(max_length=200, label = 'rm_type', widget = forms.Select(choices=RM_TYPES))

    description = forms.CharField(widget = forms.Textarea(attrs={'rows':'3'}))

    class Meta:
        model = Inventory
        fields = ('supplier', 'item_name', 'item_type', 'rm_type', 'description', 'price', 'quantity')


class SupplierPOForm(ModelForm):

    class Meta:
        model = SupplierPO
        fields = ('supplier', 'total_amount', 'delivery_date')

        supplier = forms.CharField(max_length=200, label = 'supplier', widget = forms.Select(attrs={'id':'supplier'}))
        
class SupplierPOItemsForm(ModelForm):
    price = forms.CharField(label = 'price', widget = forms.TextInput(
        attrs={'id':'price', 'name':'price'}
    ))

    class Meta:
        model = SupplierPOItems
        fields = ('item_name', 'price', 'quantity', 'total_price')

    def __init__(self, *args, **kwargs):
        super(SupplierPOItemsForm, self).__init__(*args, **kwargs)
        self.fields['item_name'].queryset = Inventory.objects.none()

        # if 'supplier' in SupplierPOForm.data:
        #     try:
        #         supplier_id = int(SupplierPOForm.data.get('supplier'))
        #         self.fields['item_name'].queryset = Inventory.objects.filter(supplier_id=supplier_id).order_by('item_name')
        #     except (ValueError, TypeError):
        #         pass  # invalid input from the client; ignore and fallback to empty City queryset
        # elif self.instance.pk:
        #     self.fields['item_name'].queryset = self.instance.supplier.item_name_set.order_by('item_name')

class MaterialRequisitionForm(forms.ModelForm):

    class Meta:
        model = MaterialRequisition
        fields = ('issued_to', 'shift')


class MaterialRequisitionItemsForm(forms.ModelForm):

    class Meta:
        model = MaterialRequisitionItems
        fields = ('brand', 'quantity', 'to_be_used_for')

        brand = forms.ModelChoiceField(queryset=Inventory.objects.all())

class BaseMRFormSet(BaseFormSet):
    def clean(self):
        """
        Adds validation to check that no two 
        """
        if any(self.errors):
            return

            brand = []
            quantity = []
            to_be_used_for = []
            duplicates = False
            
            for form in self.forms:
                if form.cleaned_data:
                    brand = form.cleaned_data['brand']
                    quantity = form.cleaned_data['quantity']
                    to_be_used_for = form.cleaned_data['to_be_used_for']

        
