from django.forms import ModelForm, ValidationError
from .models import ClientItem, ClientPO, Product, Client
from decimal import Decimal
from django.contrib.admin.widgets import AdminDateWidget


class ClientPOFormItems(ModelForm):

    class Meta:
        model = ClientItem
        fields = ('products', 'note', 'width', 'length', 'color', 'gusset', 'quantity')


class ClientPOForm(ModelForm):

    class Meta:
        model = ClientPO
        fields = ('terms', 'other_info')
        #widgets = {'date_required':DateTimePicker(options={"format": "YYYY-MM-DD", "pickSeconds": False}}




