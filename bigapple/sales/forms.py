from django import forms
from django.forms import BaseModelFormSet, ModelForm, modelformset_factory
from .models import ClientItem, ClientPO, Product, Client

class ClientPOForm(forms.ModelForm):

    class Meta:
        model = ClientItem
        fields = ('products', 'note', 'width', 'length', 'color', 'gusset', 'quantity')


class ClientPOFormset(forms.BaseModelFormSet):

    class Meta:
        clientpo_formset = modelformset_factory(ClientItem, form=ClientPOForm, fields=('products', 'note', 'width', 'length', 'color', 'gusset', 'quantity'), max_num=10, extra=5)
        formset = clientpo_formset()
