from django import forms
from django.forms import ModelForm, ValidationError, Form, widgets
from django.contrib.admin.widgets import AdminDateWidget
from .models import Supplier, SupplierPO, SupplierPOItems, Inventory, InventoryCount
from .models import MaterialRequisition
from .models import Employee
from datetime import date, datetime
from django.forms.formsets import BaseFormSet

# from django_select2.forms import ModelSelect2Widget
# from linked_select2.forms import LinkedModelSelect2Widget

class DateInput(forms.DateInput):
    input_type = 'date'

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
        ('PET', 'Polyethylene terephthalate'),
        ('Pelletized PE', 'Pelletized polyethylene '),
        ('Pelletized HD', 'Pelletized high-density polyethylene'),
    )

    item = forms.CharField(max_length=300)
    item_type = forms.CharField(max_length=200, label = 'item_type', widget = forms.Select(choices=ITEM_TYPES))
    rm_type = forms.CharField(max_length=200, label = 'rm_type', widget = forms.Select(choices=RM_TYPES))
    description = forms.CharField(widget = forms.Textarea(attrs={'rows':'3'}))
    quantity = forms.IntegerField()
    price = forms.FloatField()
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.all())


    class Meta:
        model = Inventory
        fields = ( 'item', 'item_type', 'rm_type', 'description', 'quantity', 'price', 'supplier')

    def __init__(self, *args, **kwargs):
        super(InventoryForm, self).__init__(*args, **kwargs)
        self.fields['item'].required = True
        self.fields['item_type'].required = True
        self.fields['rm_type'].required = True
        self.fields['description'].required = False
        self.fields['quantity'].required = True
        self.fields['price'].required = True
        self.fields['supplier'].required = True


class InventoryCountForm(ModelForm):

    class Meta:
        model = InventoryCount
        fields = ('inventory', 'old_count', 'new_count', 'count_person')

    new_count = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        super(InventoryCountForm, self).__init__(*args, **kwargs)
'''
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
        fields = ( 'supplier', 'price', 'rm_type', 'item') # 'item_type', 'item_name'

    supplier = forms.ModelChoiceField(queryset=Supplier.objects.all())
    item_type = forms.CharField(max_length=200, label = 'item_type', widget = forms.Select(choices=ITEM_TYPES))
    rm_type = forms.CharField(max_length=200, label = 'rm_type', widget = forms.Select(choices=RM_TYPES))
    item = forms.CharField(max_length=200, label= 'item')

'''
class SupplierPOForm(ModelForm):

    class Meta:
        model = SupplierPO
        fields = ('delivery_date', 'supplier')
        widgets = {
            'delivery_date': DateInput()
        }

        supplier = forms.CharField(max_length=200, label = 'supplier', widget = forms.Select(attrs={'id':'supplier'}))
        
class SupplierPOItemsForm(ModelForm):
    class Meta:
        model = SupplierPOItems
        fields = ('item', 'quantity')

        inventory = forms.ModelChoiceField(queryset=Inventory.objects.all())

    def __init__(self, *args, **kwargs):
        super(SupplierPOItemsForm, self).__init__(*args, **kwargs)
        self.fields['item'].queryset = Inventory.objects.all()

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
        fields = ()

    def __init__(self, *args, **kwargs):
        super(MaterialRequisitionForm, self).__init__(*args, **kwargs)

'''
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

'''
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

        
