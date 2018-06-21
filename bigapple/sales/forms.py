from django import forms
from .models import ClientItem, ClientPO, Product, Supplier

class ClientPOForm(forms.Form):
    model = ClientPO
    fields = ('date_issued', 'date_required', 'terms', 'other_info', 'client', 'client_items', 'total_amount', 'laminate', 'confirmed')

    class Meta:
        model = ClientItem
        fields = '__all__'

class AddSupplier_Form(forms.Form):    
    model = Supplier
    fields = ('company_name', 'contact_person', 'department', 'mobile_number', 'email_address',
    'supplier_type', 'description')

        