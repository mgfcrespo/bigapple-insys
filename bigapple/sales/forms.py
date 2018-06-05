from django import forms
from .models import ClientItem, ClientPO, Product

class ClientPOForm(forms.ModelForm):

    class Meta:
        model = ClientItem
        fields = '__all__'