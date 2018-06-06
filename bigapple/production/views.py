from django.http import HttpResponse
from django.shortcuts import render

from .models import Machine
from .models import WorkerSchedule
from .models import SalesInvoice

# Create your views here.
def production_details(request):
    context = {
        'title': 'Production Content'
    }

    return render(request, 'production/production_details.html', context)
