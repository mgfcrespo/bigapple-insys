from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.contrib.sessions.models import Session
from django.db.models import Sum, Count
from django.template import loader
from django.http import HttpResponse

from django.db.models.functions import TruncMonth
from datetime import datetime

from production import views as production
from django.db import connection
import pandas as pd

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

from .models import Employee
from .models import Client

from accounts.forms import SignUpForm
from sales.models import Supplier, SalesInvoice
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
        rush_order = JobOrder.objects.filter(status='Waiting').order_by('date_required').exclude(rush_order=False)[:4]

        LDPE = Inventory.objects.filter(rm_type='LDPE').aggregate(Sum('quantity')).get('quantity__sum', 0)
        LLDPE = Inventory.objects.filter(rm_type='LLDPE').aggregate(Sum('quantity')).get('quantity__sum', 0)
        HDPE = Inventory.objects.filter(rm_type='HDPE').aggregate(Sum('quantity')).get('quantity__sum', 0)
        PP = Inventory.objects.filter(rm_type='PP').aggregate(Sum('quantity')).get('quantity__sum', 0)
        PET = Inventory.objects.filter(rm_type='PET').aggregate(Sum('quantity')).get('quantity__sum', 0)
        PE = Inventory.objects.filter(rm_type='PE').aggregate(Sum('quantity')).get('quantity__sum', 0)
        HD = Inventory.objects.filter(rm_type='HD').aggregate(Sum('quantity')).get('quantity__sum', 0)

        status_waiting = JobOrder.objects.filter(status='Waiting').count()
        status_onqueue = JobOrder.objects.filter(status='On Queue').count()
        status_cutting = JobOrder.objects.filter(status='Under Cutting').count()
        status_extrusion = JobOrder.objects.filter(status='Under Extrusion').count()
        status_printing = JobOrder.objects.filter(status='Under Printing').count()
        status_packaging = JobOrder.objects.filter(status='Under Packaging').count()
        status_ready = JobOrder.objects.filter(status='Ready for Delivery').count()
        status_delivered = JobOrder.objects.filter(status='Delivered').count()
        status_cancelled = JobOrder.objects.filter(status='Cancelled').count()

        thisYear = datetime.now().year
        lastYear = datetime.now().year-1

        thisMonth = datetime.now().month

        POs = JobOrder.objects.filter(date_issued__month=thisMonth, date_issued__year=thisYear).annotate(count=Count('id'))
        POs_lastMonth = JobOrder.objects.filter(date_issued__month=thisMonth-1, date_issued__year=thisYear).annotate(count=Count('id'))

        POs_lastYear = JobOrder.objects.filter(date_issued__month=thisMonth, date_issued__year=lastYear).annotate(count=Count('id'))
        POs_lastMonthlastYear = JobOrder.objects.filter(date_issued__month=thisMonth-1, date_issued__year=lastYear).annotate(count=Count('id'))

        cursor = connection.cursor()
        query = "SELECT j.id, i.laminate, i.printed, p.material_type FROM production_mgt_joborder j, sales_mgt_clientitem i, sales_mgt_product p WHERE p.id = i.products_id and i.client_po_id = j.id and NOT j.status=" + "'Waiting'" + " and NOT j.status=" + "'Ready for delivery'" + " and NOT j.status =" + "'Delivered'"
        cursor.execute(query)
        df = pd.read_sql(query, connection)

        gantt = production.final_gantt.generate_overview_gantt_chart(df=df)

        client = Client.objects.filter(accounts_id=id)
        employee = Employee.objects.filter(accounts_id=id)
        if client:
            client_po = JobOrder.objects.filter(client=Client.objects.get(accounts_id=id)).exclude(status='Delivered')[:5]
            x = 'Client'
        elif employee:
            x = 'Employee'
            if Employee.objects.get(accounts_id=id).position == "Sales Coordinator" or "General Manager":
                client_po = JobOrder.objects.all().exclude(status='Delivered')[:5]
            elif employee.position == "Sales Agent":
                customer = Client.objects.filter(sales_agent=employee).exclude(status='Delivered')[:10]
                po = JobOrder.objects.all()
                client_po = []

        invoice = SalesInvoice.objects.all()
        for x in invoice:
            x.save()
        invoice = SalesInvoice.objects.filter(status='Late')[:10]

        context = {
            'invoice': invoice,
            'client_po': client_po,

            'gantt': gantt,

            'POs_lastMonth': POs_lastMonth,
            'thisMonth': thisMonth,

            'thisYear': thisYear,
            'lastYear': lastYear,

            'POs': POs,
            'POs_lastYear': POs_lastYear,
            'POs_lastMonthlastYear':POs_lastMonthlastYear,

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
        elif hasattr(request.user, 'client'):
            client_id = user.client.id
            client = Client.objects.get(id=client_id)
            request.session['session_position'] = 'Client'
            request.session['session_fullname'] = client.full_name
            request.session['session_userid'] = client_id
            return render(request, 'accounts/client_page.html', context)

def logout_view(request):
    logout(request)
    return redirect('accounts:user-page-view')

def account_details(request):

    context = {
        'title': 'Account Details',
        'actiontype': "Update",
    }
    return render(request, 'accounts/account_details.html', context)
