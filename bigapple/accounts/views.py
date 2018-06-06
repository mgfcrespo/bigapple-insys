from django.http import HttpResponse
from django.shortcuts import render

from .models import Account

# Create your views here.
def accountDetails(request):
    #return HttpResponse('HELLO FROM POSTS')

    context = {
        'title': 'Accounts'
    }

    return render(request, 'accounts/accountDetails.html', context)
