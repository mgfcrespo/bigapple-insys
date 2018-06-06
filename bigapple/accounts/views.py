from django.http import HttpResponse
from django.shortcuts import render

from .models import Account
from .models import Address
from .models import ContactNumber
from .models import Email
from .models import Employee
from .models import Client

# Create your views here.
def account_details(request):
    context = {
        'title': 'Account Content'
    }

    return render(request, 'accounts/account_details.html', context)
