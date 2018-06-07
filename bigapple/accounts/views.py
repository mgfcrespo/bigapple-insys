
from django.contrib.auth import authenticate, login, logout, forms
from django.shortcuts import render, reverse, HttpResponseRedirect
from django.contrib import messages

from django.contrib.sessions.models import Session
from .models import Client, Employee, User


from django.http import HttpResponse
from django.shortcuts import render



from .models import Address
from .models import ContactNumber
from .models import Email
from .models import Employee
from .models import Client

# Create your views here.


def user_page_view(request):

        user = request.user
        username = request.user.username

        request.session['session_username'] = username

        if user.employee is not None:
            employee_id = user.employee.id
            employee = Employee.objects.get(id=employee_id)

            if employee.position == 'GM':
                return render(request, 'accounts/general_manager_page.html')
            elif employee.position == 'SC':
                return render(request, 'accounts/sales_coordinator_page.html')
            elif employee.position == 'SA':
                return render(request, 'accounts/sales_agent_page.html')
            elif employee.position == 'CC':
                return render(request, 'accounts/credit_and_collection_page.html')
            elif employee.position == 'SV':
                return render(request, 'accounts/supervisor_page.html')
            elif employee.position == 'PM':
                return render(request, 'accounts/production_manager_page.html')
            elif employee.position == 'LL':
                return render(request, 'accounts/line_leader_page.html')

        else:
            return render(request, 'accounts/client_page.html')


def account_details(request):
    context = {
        'title': 'Account Content'
    }
    return render(request, 'accounts/account_details.html', context)

