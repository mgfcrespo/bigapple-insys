from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.contrib.sessions.models import Session
from django.template import loader
from django.http import HttpResponse

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

from .models import Employee
from .models import Client

from accounts.forms import SignUpForm
from sales.models import ClientPO, ClientCreditStatus, Supplier
from production.models import JobOrder, ExtruderSchedule, PrintingSchedule, CuttingSchedule
from inventory.models import InventoryCountAsof
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
        username = request.user.username

        ClientPO_data = ClientPO.objects.all()
        rush_orders = ClientPO.objects.filter(rush_order=True)

        ClientCreditStatus_data = ClientCreditStatus.objects.all()
        Supplier_data = Supplier.objects.all()

        JobOrder_data = JobOrder.objects.all()
        ExtruderSchedule_data = ExtruderSchedule.objects.all()
        PrintingSchedule_data = PrintingSchedule.objects.all()
        CuttingSchedule_data = CuttingSchedule.objects.all()

        InventoryCountAsof_data = InventoryCountAsof.objects.all()

        context = {
            'ClientPO_data': ClientPO_data,
            'rush_orders': rush_orders,
            'ClientCreditStatus_data': ClientCreditStatus_data,
            'Supplier_data': Supplier_data,
            'JobOrder_data': JobOrder_data,
            'ExtruderSchedule_data': ExtruderSchedule_data,
            'PrintingSchedule_data': PrintingSchedule_data,
            'CuttingSchedule_data': CuttingSchedule_data,
            'InventoryCountAsof_data': InventoryCountAsof_data,
            'SupplierSalesInvoice_data': SupplierSalesInvoice_data,
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
