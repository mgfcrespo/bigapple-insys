from django import forms
from django.forms import ModelForm, ValidationError, Form, widgets
from django.contrib.admin.widgets import AdminDateWidget
from .models import Supplier, SupplierPO, SupplierPOItems, Inventory, MaterialRequisitionItems, SupplierRawMaterials, InventoryCountAsof
from .models import PurchaseRequisition, PurchaseRequisitionItems, MaterialRequisition, MaterialRequisitionItems
from .models import Employee
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

    item_type = forms.CharField(max_length=200, label = 'item_type', widget = forms.Select(choices=ITEM_TYPES))
    description = forms.CharField(widget = forms.Textarea(attrs={'rows':'3'}))

    class Meta:
        model = Inventory
        fields = ( 'item', 'item_type', 'description', 'quantity')

    def __init__(self, *args, **kwargs):
        super(InventoryForm, self).__init__(*args, **kwargs)
        self.fields['item'].required = False
        self.fields['item_type'].required = False
        self.fields['description'].required = False
        self.fields['quantity'].required = False
        self.fields['quantity'].widget.attrs['readonly'] = True

class SupplierRawMaterialsForm(ModelForm):
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

    class Meta:
        model = SupplierRawMaterials
        fields = ( 'supplier', 'price', 'rm_type') # 'item_type', 'item_name'

    supplier = forms.ModelChoiceField(queryset=Supplier.objects.all())
    item_type = forms.CharField(max_length=200, label = 'item_name', widget = forms.Select(choices=ITEM_TYPES))
    rm_type = forms.CharField(max_length=200, label = 'rm_type', widget = forms.Select(choices=RM_TYPES))

class InventoryCountAsofForm(ModelForm):
    class Meta:
        model = InventoryCountAsof
        fields = ( 'inventory', 'new_count')

        inventory = forms.ModelChoiceField(queryset=Inventory.objects.all())

class SupplierPOForm(ModelForm):

    class Meta:
        model = SupplierPO
        fields = ('delivery_date', 'supplier')

        delivery_date = forms.DateField(initial=date.today(), widget = forms.DateInput(attrs={'id':'delivery_date'}))
        supplier = forms.CharField(max_length=200, label = 'supplier', widget = forms.Select(attrs={'id':'supplier'}))
        
class SupplierPOItemsForm(ModelForm):
    price = forms.CharField(label = 'price', widget = forms.TextInput(
        attrs={'id':'price', 'name':'price'}
    ))

    class Meta:
        model = SupplierPOItems
        fields = ('item_name', 'quantity')

        inventory = forms.ModelChoiceField(queryset=SupplierRawMaterials.objects.all())
    # def __init__(self, *args, **kwargs):
    #     super(SupplierPOItemsForm, self).__init__(*args, **kwargs)
    #     self.fields['item_name'].queryset = Inventory.objects.none()

        # if 'supplier_po.supplier' in self.data:
        #     try:
        #         supplier_po.supplier_id = int(self.data.get('id'))
        #         self.fields['item_name'].queryset = Inventory.objects.filter(supplier=supplier_po.supplier_id).order_by('item_name')
        #     except (ValueError, TypeError):
        #         pass  # invalid input from the client; ignore and fallback to empty City queryset
        # elif self.instance.pk:
        #     self.fields['item_name'].queryset = self.instance.supplier_po.supplier.item_name_set.order_by('item_name')

class MaterialRequisitionForm(forms.ModelForm):

    class Meta:
        model = MaterialRequisition
        fields = ('issued_to', 'shift')

        issued_to = forms.ModelChoiceField(queryset=Employee.objects.all())

    def __init__(self, *args, **kwargs):
        super(MaterialRequisitionForm, self).__init__(*args, **kwargs)
       
        self.fields["issued_to"].queryset = Employee.objects.filter(position__in=['General Manager', 'Sales Coordinator', 'Supervisor',
        'Line Leader', 'Production Manager', 'Cutting', 'Printing', 'Extruder', 'Delivery', 'Warehouse', 'Utility', 
        'Maintenance'])

class MaterialRequisitionItemsForm(forms.ModelForm):

    class Meta:
        model = MaterialRequisitionItems
        fields = ('brand', 'quantity', 'to_be_used_for')

        brand = forms.ModelChoiceField(queryset=Inventory.objects.all())

class PurchaseRequisitionForm(forms.ModelForm):

    class Meta:
        model = PurchaseRequisition
        fields = ('placed_by', 'date_required')

        placed_by = forms.ModelChoiceField(queryset=Employee.objects.all())

    def __init__(self, *args, **kwargs):
        super(PurchaseRequisitionForm, self).__init__(*args, **kwargs)
       
        self.fields["issued_to"].queryset = Employee.objects.filter(position__in=['General Manager', 'Sales Coordinator', 'Supervisor',
        'Line Leader', 'Production Manager', 'Cutting', 'Printing', 'Extruder', 'Delivery', 'Warehouse', 'Utility', 
        'Maintenance'])

class PurchaseRequisitionItemsForm(forms.ModelForm):

    class Meta:
        model = PurchaseRequisitionItems
        fields = ('item', 'quantity')

        item = forms.ModelChoiceField(queryset=Inventory.objects.all())

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

        
