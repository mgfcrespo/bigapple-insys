from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.contrib.sessions.models import Session
from django.db.models import Sum, Count
from django.template import loader
from django.http import HttpResponse

from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta, date, time
import datetime, calendar

from production import views as production
from django.db import connection
import pandas as pd

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

from .models import Employee
from .models import Client

from accounts.forms import SignUpForm
from sales.models import Supplier, SalesInvoice, ClientItem, Product
from production.models import JobOrder, ExtruderSchedule, PrintingSchedule, CuttingSchedule, LaminatingSchedule, Machine
from inventory.models import Inventory
from utilities import TimeSeriesForecasting, cpsat
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

def most_common(lst):
    return max(set(lst), key=lst.count)

def client_demand_query(id, product_id):
    cursor_client = connection.cursor()
    query_client = 'SELECT po.date_issued, poi.quantity FROM  production_mgt_joborder po, sales_mgt_clientitem poi WHERE ' \
                   'po.client_id = ' +str(id)+ ' AND poi.client_po_id = po.id AND poi.products_id = '+str(product_id)

    cursor_client.execute(query_client)
    df_client = pd.read_sql(query_client, connection)

    return df_client

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

        thisYear = date.today().year
        lastYear = date.today().year-1

        thisMonth = date.today().month

        POs = JobOrder.objects.filter(date_issued__month=thisMonth, date_issued__year=thisYear).annotate(count=Count('id'))
        POs_lastMonth = JobOrder.objects.filter(date_issued__month=thisMonth-1, date_issued__year=thisYear).annotate(count=Count('id'))

        POs_lastYear = JobOrder.objects.filter(date_issued__month=thisMonth, date_issued__year=lastYear).annotate(count=Count('id'))
        POs_lastMonthlastYear = JobOrder.objects.filter(date_issued__month=thisMonth-1, date_issued__year=lastYear).annotate(count=Count('id'))

        forecast_ses = []
        forecast_hwes = []
        forecast_moving_average = []
        forecast_arima = []

        product = None

        #PRODUCTION SCHEDULE
        plot_list = []
        ideal = []
        ex = []
        for x in ExtruderSchedule.objects.filter(ideal=True):
            job = x.job_order
            if job.status == 'Ready for delivery' or job.status == 'Delivered':
                pass
            else:
                ex.append(x)
        ex_list = list(ex)
        ideal.append(ex_list)
        cu = []
        for y in CuttingSchedule.objects.filter(ideal=True):
            job = y.job_order
            if job.status == 'Ready for delivery' or job.status == 'Delivered':
                pass
            else:
                cu.append(y)
        cu_list = list(cu)
        ideal.append(cu_list)
        pr = []
        for z in PrintingSchedule.objects.filter(ideal=True):
            job = z.job_order
            if job.status == 'Ready for delivery' or job.status == 'Delivered':
                pass
            else:
                pr.append(z)
        pr_list = list(pr)
        ideal.append(pr_list)
        la = []
        for a in LaminatingSchedule.objects.filter(ideal=True):
            job = a.job_order
            if job.status == 'Ready for delivery' or job.status == 'Delivered':
                pass
            else:
                la.append(a)
        la_list = list(la)
        ideal.append(la_list)

        if ideal:
            if ex:
                for i in ex:
                    job = i.job_order_id
                    item = ClientItem.objects.get(client_po_id=job)
                    product = item.products
                    mat = product.material_type

                    sked_dict = {'Task': 'Extrusion',
                                 'Start': i.sked_in,
                                 'Finish': i.sked_out,
                                 'Resource': mat,
                                 'Machine': i.sked_mach,
                                 'Worker': i.sked_op
                                 }
                    plot_list.append(sked_dict)

            if cu:
                for j in cu:
                    job = j.job_order_id
                    item = ClientItem.objects.get(client_po_id=job)
                    product = item.products
                    mat = product.material_type

                    sked_dict = {'Task': 'Cutting',
                                 'Start': i.sked_in,
                                 'Finish': i.sked_out,
                                 'Resource': mat,
                                 'Machine': i.sked_mach,
                                 'Worker': i.sked_op
                                 }
                    plot_list.append(sked_dict)
            if pr:
                for k in pr:
                    job = k.job_order_id
                    item = ClientItem.objects.get(client_po_id=job)
                    product = item.products
                    mat = product.material_type

                    sked_dict = {'Task': 'Printing',
                                 'Start': i.sked_in,
                                 'Finish': i.sked_out,
                                 'Resource': mat,
                                 'Machine': i.sked_mach,
                                 'Worker': i.sked_op
                                 }
                    plot_list.append(sked_dict)
            if la:
                for l in la:
                    job = l.job_order_id
                    item = ClientItem.objects.get(client_po_id=job)
                    product = item.products
                    mat = product.material_type

                    sked_dict = {'Task': 'Laminating',
                                 'Start': i.sked_in,
                                 'Finish': i.sked_out,
                                 'Resource': mat,
                                 'Machine': i.sked_mach,
                                 'Worker': i.sked_op
                                 }
                    plot_list.append(sked_dict)

            print('plot_list:')
            print(plot_list)
        else:
            cursor = connection.cursor()
            query = "SELECT j.id, i.laminate, i.printed, p.material_type FROM production_mgt_joborder j, sales_mgt_clientitem i, sales_mgt_product p WHERE p.id = i.products_id and i.client_po_id = j.id and NOT j.status=" + "'Waiting'" + " and NOT j.status=" + "'Ready for delivery'" + " and NOT j.status =" + "'Delivered'"
            cursor.execute(query)
            df = pd.read_sql(query, connection)
            plot_list = cpsat.flexible_jobshop(df)

        today = date.today()
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=7)
        start_month = today.replace(day=1)
        week = []
        month = []
        for i in range(0, 7):
            week.append(start_week)
            start_week += timedelta(days=1)
        for i in range(0, calendar.monthrange(today.year, today.month)[1]):
            month.append(start_month)
            start_month += timedelta(days=1)
        start_week = today - timedelta(days=today.weekday())
        this_week = []
        this_month = []

        for i in range(len(plot_list)):
            if start_week <= plot_list[i]['Start'].date() <= end_week:
                this_week.append(plot_list[i])
            if plot_list[i]['Start'].month == today.month:
                this_month.append(plot_list[i])

        client = Client.objects.filter(accounts_id=id)
        employee = Employee.objects.filter(accounts_id=id)
        client_po = []
        if client:
            client_po = JobOrder.objects.filter(client=Client.objects.get(accounts_id=id)).exclude(status='Delivered')[:5]
            x = 'Client'

            # CLIENT DEMAND FORECAST FOR CLIENT
            mga_po = JobOrder.objects.filter(client=Client.objects.get(accounts_id=id))
            i = ClientItem.objects.all()
            mga_item = []
            for every in mga_po:
                for each in i:
                    if each.client_po_id == every.id:
                        mga_item.append(each.products_id)

            itong_item = most_common(mga_item)
            itong_item = Product.objects.get(id=itong_item)

            forecast_ses = []
            forecast_hwes = []
            forecast_moving_average = []
            forecast_arima = []

            df_client = client_demand_query(user.client.id, itong_item.id)

            product = itong_item

            # forecast_decomposition.append(TimeSeriesForecasting.forecast_decomposition(df))
            a = TimeSeriesForecasting.forecast_ses(df_client)
            a[1] = int(float(a[1]))
            forecast_ses.extend(a)
            b = TimeSeriesForecasting.forecast_hwes(df_client)
            b[1] = int(float(b[1]))
            forecast_hwes.extend(b)
            c = TimeSeriesForecasting.forecast_moving_average(df_client)
            c[1] = int(float(c[1]))
            forecast_moving_average.extend(c)
            #d = TimeSeriesForecasting.forecast_arima(df_client)
            #d[1] = int(float(d[1]))
            #forecast_arima.extend(d)

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

            'machines': Machine.objects.all(),
            'this_week': this_week,
            'this_month': this_month,
            'week': week,
            'month': month,
            'today': today,

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

            'forecast_ses' : forecast_ses,
            'forecast_hwes': forecast_hwes,
            'forecast_moving_average': forecast_moving_average,
            'forecast_arima': forecast_arima,
            'product': product,
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
