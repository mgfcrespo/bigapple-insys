from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.contrib.sessions.models import Session
from django.db.models import Sum, Count
from django.template import loader
from django.http import HttpResponse

from django.db.models.functions import TruncMonth
from datetime import datetime

import array as arr


from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

from .models import Employee
from .models import Client

from accounts.forms import SignUpForm
from sales.models import Supplier
from production.models import JobOrder, ExtruderSchedule, PrintingSchedule, CuttingSchedule
from inventory.models import Inventory
# Create your views here.

def register(request):
    if request.method == 'POST' and 'Register' in request.POST:
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


@login_required(login_url='/profile/login/')
def user_page_view(request):

        user = request.user
        id = user.id
        username = request.user.username

        Client_data = Client.objects.all()
        Supplier_data = Supplier.objects.all()
        JobOrder_data = JobOrder.objects.all()

        JobOrder_data5 = JobOrder.objects.order_by('-id')[:5]
        rush_order = JobOrder.objects.filter(rush_order=True).exclude(status='delivered')[:3]

        LDPE = Inventory.objects.filter(rm_type='LDPE')
        LLDPE = Inventory.objects.filter(rm_type='LLDPE')
        HDPE = Inventory.objects.filter(item_type='HDPE')
        PP = Inventory.objects.filter(item_type='PP')
        PET = Inventory.objects.filter(item_type='PET')
        PE = Inventory.objects.filter(item_type='Pelletized PE')
        HD = Inventory.objects.filter(item_type='Pelletized HD')

        status_waiting = JobOrder.objects.filter(status='Waiting').count()
        status_onqueue = JobOrder.objects.filter(status='On Queue').count()
        status_cutting = JobOrder.objects.filter(status='Under Cutting').count()
        status_extrusion = JobOrder.objects.filter(status='Under Extrusion').count()
        status_printing = JobOrder.objects.filter(status='Under Printing').count()
        status_packaging = JobOrder.objects.filter(status='Under Packaging').count()
        status_ready = JobOrder.objects.filter(status='Ready for Delivery').count()
        status_delivered = JobOrder.objects.filter(status='Delivered').count()
        status_cancelled = JobOrder.objects.filter(status='Cancelled').count()

        dateToday = datetime.now()

        thisYear = datetime.now().year
        lastYear = datetime.now().year-1

        thisMonth = datetime.now().month

        POs = JobOrder.objects.filter(date_issued__month=thisMonth, date_issued__year=thisYear).annotate(count=Count('id'))
        POs_lastYear = JobOrder.objects.filter(date_issued__month=thisMonth, date_issued__year=lastYear).annotate(count=Count('id'))

        context = {
            'thisMonth': thisMonth,

            'thisYear': thisYear,
            'lastYear': lastYear,

            'POs': POs,
            'POs_lastYear': POs_lastYear,

            'LDPE': LDPE,
            'LLDPE': LLDPE,
            'HDPE': HDPE,
            'PP': PP,
            'PET': PET,
            'PE': PE,
            'HD': HD,

            'status_waiting': status_waiting,
            'status_onqueue': status_onqueue,
            'status_cutting': status_cutting,
            'status_extrusion': status_extrusion,
            'status_printing': status_printing,
            'status_packaging': status_packaging,
            'status_ready': status_ready,
            'status_delivered': status_delivered,
            'status_cancelled': status_cancelled,

            'Client_data': Client_data,
            'Supplier_data': Supplier_data,
            'JobOrder_data': JobOrder_data,
            'JobOrder_data5': JobOrder_data5,
            'rush_order': rush_order,
            }

        request.session['session_username'] = username
        if hasattr(request.user, 'employee'):
            employee_id = user.employee.id
            employee = Employee.objects.get(id=employee_id)

            request.session['session_position'] = employee.position
            request.session['session_fullname'] = employee.full_name
            request.session['session_userid'] = employee_id

            if employee.position == 'General Manager':
                return render(request, 'accounts/general_manager_page.html', context)
            elif employee.position == 'Sales Coordinator':
                return render(request, 'accounts/sales_coordinator_page.html', context)
            elif employee.position == 'Sales Agent':
                return render(request, 'accounts/sales_agent_page.html', context)
            elif employee.position == 'Credits and Collection Personnel':
                return render(request, 'accounts/credit_and_collection_personnel_page.html', context)
            elif employee.position == 'Supervisor':
                return render(request, 'accounts/supervisor_page.html', context)
            elif employee.position == 'Production Manager':
                return render(request, 'accounts/production_manager_page.html', context)
            elif employee.position == 'Line Leader':
                return render(request, 'accounts/line_leader_page.html', context)
        else:
            client_id = user.client.id
            client = Client.objects.get(id=client_id)
            request.session['session_position'] = 'Client'
            request.session['session_fullname'] = client.full_name
            request.session['session_userid'] = client_id
            return render(request, 'accounts/client_page.html')

def logout_view(request):
    logout(request)
    return redirect('accounts:user-page-view')

def account_details(request):

    context = {
        'title': 'Account Details',
        'actiontype': "Update",
    }
    return render(request, 'accounts/account_details.html', context)
