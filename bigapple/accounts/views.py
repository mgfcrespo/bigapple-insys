from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.contrib.sessions.models import Session

from django.http import HttpResponse

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

from .models import Address
from .models import ContactNumber
from .models import Email
from .models import Employee
from .models import Client

# Create your views here.

def register(request):
    if request.method == 'POST':
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
    return render(request, 'login.html', {'form': form})

@login_required(login_url='/profile/login/')
def user_page_view(request):

        user = request.user
        username = request.user.username

        request.session['session_username'] = username
        if hasattr(request.user, 'employee'):
            employee_id = user.employee.id
            employee = Employee.objects.get(id=employee_id)
            position = employee.position
            request.session['session_position'] = employee.position
            request.session['session_fullname'] = employee.full_name
            request.session['session_userid'] = employee_id


            if employee.position == 'GM':
                return render(request, 'accounts/general_manager_page.html')
            elif employee.position == 'SC':
                return render(request, 'accounts/sales_coordinator_page.html')
            elif employee.position == 'SA':
                return render(request, 'accounts/sales_agent_page.html')
            elif employee.position == 'CC':
                return render(request, 'accounts/credit_and_collection_personnel_page.html')
            elif employee.position == 'SV':
                return render(request, 'accounts/supervisor_page.html')
            elif employee.position == 'PM':
                return render(request, 'accounts/production_manager_page.html')
            elif employee.position == 'LL':
                return render(request, 'accounts/line_leader_page.html')
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
        'title': 'Account Content'
    }
    return render(request, 'accounts/account_details.html', context)

