from datetime import datetime, date, timedelta, time
import datetime, calendar
import dateutil.parser
import random
from django.db import connection
from django.db.models import aggregates, Sum, Count
from django.forms import inlineformset_factory
from django.shortcuts import redirect
from django.shortcuts import render, HttpResponseRedirect, HttpResponse, Http404
from pandas import DataFrame
from django.contrib import messages
import math


from accounts.models import Employee
from inventory.forms import MaterialRequisitionForm, SupplierPOForm, SupplierPOItemsForm
from inventory.models import Inventory, Supplier, MaterialRequisition, SupplierPO, SupplierPOItems
from production.forms import ClientPOForm
from production.models import JobOrder, ExtruderSchedule, PrintingSchedule, CuttingSchedule, LaminatingSchedule, Machine
from utilities import TimeSeriesForecasting, cpsat
from .forms import ClientPOFormItems
from .forms import SupplierForm, ClientPaymentForm, EmployeeForm, ClientForm
from .models import ClientItem, Client, SalesInvoice, ClientPayment, ProductionCost, Product
import pandas as pd
from django.db.models import Q


#Forecasting imports
#import numpy as np
#from math import sqrt
#import pandas as pd
#import pandas._libs.tslibs.timedeltas
#import matplotlib.pyplot as plt
#from sklearn.metrics import mean_squared_error
#from matplotlib.pylab import rcParams
#rcParams['figure.figsize'] = 15, 6


# Create your views here.
def most_common(lst):
    if lst:
        return max(set(lst), key=lst.count)
    else:
        return None

# CRUD SUPPLIER
def supplier_add(request):
    form = SupplierForm(request.POST)
    if request.method == 'POST':
        HttpResponse(print(form.errors))
        if form.is_valid():
            form.save()
            return redirect('sales:supplier_list')

    context = {
        'form' : form,
        'title' : "Add Supplier",
        'actiontype' : "Submit",
    }
    return render(request, 'sales/supplier_add.html', context)

def supplier_list(request):
    supplier = Supplier.objects.all()
    context = {
        'title': 'Supplier List',
        'supplier' : supplier 
    }
    return render (request, 'sales/supplier_list.html', context)

def supplier_edit(request, id):
    supplier = Supplier.objects.get(id=id)
    form = SupplierForm(request.POST or None, instance=supplier)

    if form.is_valid():
        form.save()
        return redirect('sales:supplier_list')
    
    context = {
        'form' : form,
        'supplier' : supplier,
        'title' : "Edit Supplier",
        'actiontype' : "Submit",
    }
    return render(request, 'sales/supplier_add.html', context)

def supplier_delete(request, id):
    supplier = Supplier.objects.get(id=id)
    supplier.delete()
    return redirect('sales:supplier_list')
    
# CRUD PO
def edit_clientPO(request, id):
        client_po = JobOrder.objects.get(id=id)

        context = {
            'title': "Edit Purchase Order",
            'actiontype': "Submit",
            'client_po': client_po,
        }

        return render(request, 'sales/edit_clientPO.html/', context)

def delete_clientPO(request, id):
        client_po = JobOrder.objects.get(id=id)
        client_po.delete()
        return HttpResponseRedirect('../clientPO_list')

# PO List/Detail view + PO Confirm

def po_list_view(request):
    user = request.user
    id = user.id
    client = Client.objects.filter(accounts_id = id)
    employee = Employee.objects.filter(accounts_id = id)
    ideal = CuttingSchedule.objects.filter(ideal=True)
    end_dates = []
    x = ''
    client_po = []

    if client:
        client_po = JobOrder.objects.filter(client = Client.objects.get(accounts_id = id))
        x = 'Client'
        for each in client_po:
            for every in ideal:
                if every.job_order_id == each.id:

                    end_dates.append({'End' : every.sked_out.date(),
                                      'PO' : each.id})
    elif employee:
        x = 'Employee'
        if Employee.objects.get(accounts_id = id).position == "Sales Coordinator" or "General Manager":
            client_po = JobOrder.objects.all()
            for each in client_po:
                ideal_scheds = []
                for every in ideal:
                    if every.job_order_id == each.id:
                        ideal_scheds.append(every)
                ideal_scheds.sort(key=lambda i: i.sked_out)
                if ideal_scheds:
                    end_dates.append({'End': ideal_scheds[-1].sked_out.date(),
                                      'PO': each.id})
        elif employee.position == "Sales Agent":
            customer = Client.objects.filter(sales_agent_id = employee.id)
            po = JobOrder.objects.all()
            client_po = []
            for a in po:
              for y in customer:
                  if a.client_id == y.id:
                     client_po.append(a)

    context = {
        'title' : "Client Purchase Orders",
        'client_po' : client_po,
        'x' : x,
        'end_dates' : end_dates
    }

    return render(request, 'sales/clientPO_list.html', context)

def po_detail_view(request, pk):
    client_po = JobOrder.objects.get(pk=pk)
    client = client_po.client
    items = ClientItem.objects.filter(client_po = client_po)
    preprod = False
    if client_po.status == 'Waiting' or client_po.status == 'On Queue':
        preprod = True

    # credit status
    if client.overdue_balance > 0:
        client.credit_status = 1
        credit_status = True
    else:
        client.credit_status = 0
        credit_status = False

    #matreq determinant
    products = []
    material = []

    matreq = False
    for each in items:
        products.append(each.products)
        material.append(each.products.material_type)
        for x in material:
            inventory = Inventory.objects.filter(rm_type=x)
            if inventory.exists():
                for y in inventory:
                    if y.quantity >= each.quantity/1000:
                        matreq = True
                    else:
                        matreq = False
                        break
            else:
                matreq = False
                break

        if each.printed == 1:
            ink = Inventory.objects.filter(Q(item_type='Ink') & Q(item=each.color)).first()
            if ink is not None:
                if ink.quantity >= int(each.quantity/2500):
                    matreq = True
            else:
                matreq = False
                break

    context = {'client_po': client_po,
               'pk' : pk, 'matreq' : matreq, 'credit_status' : credit_status, 'preprod' : preprod}

    return render(request, 'sales/clientPO_detail.html', context)


def confirm_client_po(request, pk):
    clientpo = JobOrder.objects.get(pk=pk)
    client = clientpo.client
    items = ClientItem.objects.filter(client_po = clientpo)
    supplierpo_item_formset = None

    #credit status
    if client.overdue_balance > 0:
        client.credit_status = 1
        credit_status = True
    else:
        client.credit_status = 0
        credit_status = False

    #matreq determinant
    products = []
    material = []
    cylinder_count = 0
    color = ''

    matreq = False
    for each in items:
        products.append(each.products)
        material.append(each.products.material_type)
        for x in material:
            inventory = Inventory.objects.filter(rm_type=x)
            if inventory.exists():
                for y in inventory:
                    if y.quantity >= each.quantity/1000:
                        matreq = True
                    else:
                        matreq = False
                        request.session['matreq_quantity'] = each.quantity/1000
                        request.session['matreq_mat'] = x.id
                        break
            else:
                inventory = None
                matreq = False
                request.session['matreq_quantity'] = each.quantity / 1000
                request.session['matreq_mat'] = x.id
                break

        if each.printed == 1:
            cylinder_count = int(each.quantity/10000)
            ink = Inventory.objects.filter(Q(item_type='Ink') & Q(item=each.color)).first()
            if ink is not None:
                if ink.quantity >= int(each.quantity/2500):
                    color = str(each.color)
                    color_count = int(each.quantity/2500)
                    matreq = True
                else:
                    matreq = False
                    request.session['matreq_ink'] = str(each.color)
                    request.session['matreq_quantity'] = int(each.quantity / 2500)
            else:
                matreq = False
                request.session['matreq_ink'] = str(each.color)
                request.session['matreq_quantity'] = int(each.quantity/2500)
                break

    #matreq form
    if request.method == "POST" and 'confirm_btn' in request.POST:

        if matreq:
            # SAVE NEW PRODUCTION SCHEDULE
            in_production = JobOrder.objects.filter(
                ~Q(status='On Queue') & ~Q(status='Ready for delivery') & ~Q(status='Delivered') & ~Q(status='Waiting'))
            save_schedule(request, pk, None, None, True, True, True, True, in_production)
            clientpo.status = "On Queue"
            clientpo.save()
            for every in items:
                for x in material:
                    form1 = MaterialRequisitionForm(request.POST)
                    if form1.is_valid():
                        new_form = form1.save(commit=False)
                        new_form.client_item = every
                        new_form.item = Inventory.objects.filter(rm_type=x).first()
                        new_form.quantity = every.quantity/1000 #TODO: Ensure quantity (raw mat to product ratio)
                        new_form.save()

                        #matreq = MaterialRequisition.objects.get(id = new_form.pk)
                        #matreq.client_item = every
                        #matreq.item = Inventory.objects.filter(rm_type=x).first()
                        #matreq.save()

            if each.printed == 1:
                supplier = Supplier.objects.get(id=2)
                delivery_date = date.today() + timedelta(days=7)
                item = Inventory.objects.get(item='Generic Cylinder')

                supplierpo_item_formset = inlineformset_factory(SupplierPO, SupplierPOItems, form=SupplierPOItemsForm,
                                                                extra=1,
                                                                can_delete=True)
                form = SupplierPO(supplier=supplier, delivery_date=delivery_date, date_issued=date.today())
                form.save()
                form_item = SupplierPOItems(supplier_po=form, item=item, quantity=cylinder_count)
                form_item.save()
                form.total_amount = form_item.total_price
                form.save()

                form2 = MaterialRequisitionForm(request.POST)
                if form2.is_valid():
                        ink_form = form2.save(commit=False)
                        ink_form.client_item = every
                        ink_form.item = Inventory.objects.get(item=color)
                        ink_form.quantity = color_count
                        ink_form.save()

            return redirect('sales:po-list-view')


    context = {
        'clientpo': clientpo,
        'pk' : pk,
        'client' : client,
        'matreq' : matreq,
        'credit_status' : credit_status,
        'formset': supplierpo_item_formset,

            }

    return render(request, 'sales/clientPO_confirm.html', context)

#Invoice List/Detail View
def invoice_list_view(request):

    invoice = SalesInvoice.objects.filter(date_issued__isnull=False)

    if request.session['session_position'] == 'Client':
        invoice = SalesInvoice.objects.filter(Q(date_issued__isnull=False) & Q(client_id=request.session['session_userid']))

    context = {
     'invoice': invoice
        }

    return render(request, 'sales/sales_invoice_list.html', context)

def invoice_detail_view(request, pk):

    sales_invoice = SalesInvoice.objects.get(pk=pk)
    #form = ClientPaymentForm()
    payments = ClientPayment.objects.filter(invoice_id=sales_invoice.id)


    try:
        client = Client.objects.get(id=sales_invoice.client_id)
        form = ClientPaymentForm(request.POST)

        if request.method == "POST":
            if form.is_valid():
                form = form.save(commit=False)
                form.client = client
                form.invoice = sales_invoice
                form.old_balance = sales_invoice.amount_due
                form.new_balance = form.old_balance - form.payment
                form.save()

                sales_invoice.total_paid += form.payment
                sales_invoice.amount_due -= form.payment
                client.outstanding_balance -= form.payment

                if sales_invoice.status == 'Late':
                    client.overdue_balance -= form.payment

            sales_invoice.save()
            client.save()

        if sales_invoice.amount_due <= 0.0 and sales_invoice.status != "Cancelled":
            sales_invoice.status = "Closed"
            sales_invoice.save()


        payments = ClientPayment.objects.filter(invoice=sales_invoice)

        context = {'salesinvoice': sales_invoice,
                   'form' : form,
                   'payments' : payments,
                   'pk' : pk}


    except SalesInvoice.DoesNotExist:
        raise Http404("Sales Invoice does not exist")

    return render(request, 'sales/sales_invoice_details.html', context)


def add_payment(request, pk):
    sales_invoice = SalesInvoice.objects.get(pk=pk)
    client = Client.objects.get(id=sales_invoice.client_id)
    form = ClientPaymentForm(request.POST)

    if request.method == "POST":
        if form.is_valid():
            form = form.save(commit=False)
            form.client = client
            form.invoice = sales_invoice
            form.old_balance = sales_invoice.amount_due
            form.new_balance = form.old_balance - form.payment
            form.save()

            sales_invoice.total_paid += form.payment
            sales_invoice.amount_due -= form.payment
            client.outstanding_balance -= form.payment

        sales_invoice.save()
        client.save()

    return form

def payment_list_view(request):
    user = request.user
    id = user.id
    client = Client.objects.get(accounts_id=id)

    client = client
    sales_invoice = SalesInvoice.objects.filter(client=client)
    client_payment = ClientPayment.objects.filter(client = client)

    context = {
        'client' : client,
        'client_payment' : client_payment,
        'sales_invoice' : sales_invoice
    }

    return render(request, 'sales/client_payment_list.html', context)

def payment_detail_view(request, pk):
    sales_invoice = SalesInvoice.objects.get(pk=pk)
    sales_invoice_po = sales_invoice.client_po

    if sales_invoice.amount_due <= 0 and sales_invoice.status != "Cancelled":
        sales_invoice.status = "Closed"
    else:
        sales_invoice.status = "Open"


    sales_invoice.save()

    po = JobOrder.objects.get(id = sales_invoice_po.id)
    po_items = ClientItem.objects.filter(client_po = po)

    payments = ClientPayment.objects.filter(invoice_issued=sales_invoice)

    context = {'salesinvoice' : sales_invoice,
               'po' : po,
               'po_items' : po_items,
               'payments' : payments}

    return render(request, 'sales/client_payment_detail.html', context)

def statement_of_accounts_list_view(request):
    client = Client.objects.all()
    sales_invoice = SalesInvoice.objects.filter(status='Late')

    context = {
        'client' : client,
        'sales_invoice' : sales_invoice,
        'date' : datetime.datetime.now()
    }

    return render(request, 'sales/statement_of_accounts.html', context)

#SAMPLE DYNAMIC FORM
def create_client_po(request):
    #FORECAST
    matreq = False
    credit_status = False
    client_po = JobOrder.objects.filter(client_id=request.session['session_userid'])
    client = Client.objects.get(id=request.session['session_userid'])
    i = ClientItem.objects.all()
    items = []
    for every in i:
        for each in client_po:
            if every.client_po_id == each.id:
                items.append(every.products_id)

    item = most_common(items)
    item = Product.objects.get(id=item)
    cursor = connection.cursor()
    forecast_ses = []
    forecast_hwes = []
    forecast_moving_average = []

    query = 'SELECT po.date_issued, poi.quantity FROM  production_mgt_joborder po, sales_mgt_clientitem poi WHERE ' \
            'po.client_id = ' + str(request.session['session_userid']) + ' AND poi.client_po_id = po.id AND poi.products_id = ' + str(item.id)

    cursor.execute(query)
    df = pd.read_sql(query, connection)

    product = item

    # forecast_decomposition.append(TimeSeriesForecasting.forecast_decomposition(df))
    a = TimeSeriesForecasting.forecast_ses(df)
    a[1] = int(float(a[1]))
    forecast_ses.extend(a)
    b = TimeSeriesForecasting.forecast_hwes(df)
    b[1] = int(float(b[1]))
    forecast_hwes.extend(b)
    c = TimeSeriesForecasting.forecast_moving_average(df)
    c[1] = int(float(c[1]))
    forecast_moving_average.extend(c)

    #TODO Compare EOQ with quantity of Inventory items, suggest high stock Products

    clientpo_item_formset = inlineformset_factory(JobOrder, ClientItem, form=ClientPOFormItems, extra=1, can_delete=True)
    form = ClientPOForm(request.POST)
    if request.method == "POST":
        message = ""
        print(form)
        if form.is_valid():
            #Save PO form then use newly saved ClientPO as instance for ClientPOItems
            new_form = form.save(commit=False)
            #Set ClientPO.client from session user
            client_id = request.session['session_userid']
            current_client = Client.objects.get(id=client_id)
            new_form.client = current_client
            new_form = form.save()
            form_id = new_form.pk
            form_instance = JobOrder.objects.get(id=form_id)

            #Use PO form instance for PO items
            formset = clientpo_item_formset(request.POST, instance=form_instance)
            print(formset)
            if formset.is_valid():
                for form in formset:
                    form.save()
                formset_items = ClientItem.objects.filter(client_po_id = form_id)
                formset_item_total = formset_items.aggregate(sum=aggregates.Sum('item_price'))['sum'] or 0

                #totalled_clientpo = JobOrder.objects.get(id=form_id)
                form_instance.total_amount = formset_item_total
                form_instance.save()

                invoice = SalesInvoice(client=current_client, client_po=form_instance, total_amount=formset_item_total,
                                       amount_due=0)
                invoice.amount_due = invoice.calculate_total_amount_computed()
                invoice.save()

                message = "PO successfully created"
                return redirect('sales:po-list-view')

            else:
                message += "Formset error"

        else:
            message = "Form is not valid"

        return render(request, 'accounts/client_page.html',
                              {'message': message,
        'forecast_ses': forecast_ses,
        'forecast_hwes': forecast_hwes,
        'forecast_moving_average': forecast_moving_average,
        'product' : product}
                              )
    else:
        return render(request, 'sales/clientPO_form.html',
                              {'formset': clientpo_item_formset(),
                               'form': ClientPOForm,
        'forecast_ses': forecast_ses,
        'forecast_hwes': forecast_hwes,
        'forecast_moving_average': forecast_moving_average,
        'product' : product
        }
                              )


#RUSH ORDER CRUD
def rush_order_list(request):
    rush_orders = JobOrder.objects.filter(rush_order = True).filter(status='Waiting')

    context = {
        'rush_orders' : rush_orders,
    }

    return render (request, 'sales/rush_order_list.html', context)

def rush_order_assessment(request, pk):
    rush_order = JobOrder.objects.get(pk=pk)
    client = rush_order.client
    items = ClientItem.objects.filter(client_po = rush_order)

    #credit status
    if client.overdue_balance > 0:
        client.credit_status = 1
        credit_status = True
    else:
        client.credit_status = 0
        credit_status = False

    #cost shit
    mark_up = ProductionCost.objects.get(cost_type='Mark_up')
    mark_up = mark_up.cost
    electricity = ProductionCost.objects.get(cost_type='Electricity')

    for every in items:
        price = every.calculate_price_per_piece() * every.quantity
        profit = 0

        profit += float(mark_up) * (10000 * (
            every.calculate_price_per_piece()) - electricity.cost - (1600/every.quantity) - \
                   (300/every.quantity) - (
                               every.length * every.width * every.thickness )) / (
                              every.length * every.width * every.thickness )
    #matreq determinant
    products = []
    material = []
    cylinder_count = 0
    color = ''

    matreq = False
    for each in items:
        products.append(each.products)
        material.append(each.products.material_type)
        for x in material:
            inventory = Inventory.objects.filter(rm_type=x)
            if inventory.exists():
                for y in inventory:
                    if y.quantity > each.quantity/1000:
                        matreq = True
                    else:
                        matreq = False
                        request.session['matreq_quantity'] = each.quantity / 1000
                        request.session['matreq_mat'] = x
                        break
            else:
                inventory = None
                matreq = False
                request.session['matreq_quantity'] = each.quantity / 1000
                request.session['matreq_mat'] = x
                break
        print('matreq first run:')
        print(matreq)

        if each.printed == 1:
            cylinder_count = int(each.quantity/10000)
            ink = Inventory.objects.filter(Q(item_type='Ink') & Q(item=each.color)).first()
            if ink:
                color = str(each.color)
                color_count = int(each.quantity/2500)
                matreq = True
            else:
                matreq = False
                request.session['matreq_ink'] = str(each.color)
                request.session['matreq_quantity'] = int(each.quantity / 2500)
                break
    print('matreq for second run:')
    print(matreq)

    #matreq form
    if request.method == "POST":
        if matreq:
            print('MATREQ TRUE')
            for every in items:
                for x in material:
                    form1 = MaterialRequisitionForm(request.POST)
                    if form1.is_valid():
                        new_form = form1.save(commit=False)
                        new_form.client_item = every
                        new_form.item = Inventory.objects.filter(rm_type=x).first()
                        new_form.quantity = every.quantity/1000 #TODO: Ensure quantity (raw mat to product ratio)
                        new_form.save()
                        print('MATREQ FORM SAVED')

                        #matreq = MaterialRequisition.objects.get(id = new_form.pk)
                        #matreq.client_item = every
                        #matreq.item = Inventory.objects.filter(rm_type=x).first()
                        #matreq.save()

            if each.printed == 1:
                supplier = Supplier.objects.get(id=2)
                delivery_date = date.today() + timedelta(days=7)
                item = Inventory.objects.get(item='Generic Cylinder')

                supplierpo_item_formset = inlineformset_factory(SupplierPO, SupplierPOItems,
                                                                form=SupplierPOItemsForm, extra=1,
                                                                can_delete=True)
                form = SupplierPO(supplier=supplier, delivery_date=delivery_date, date_issued=date.today())
                form.save()
                form_item = SupplierPOItems(supplier_po=form, item=item, quantity=cylinder_count)
                form_item.save()
                form.total_amount = form_item.total_price
                form.save()

                if ink:
                    form2 = MaterialRequisitionForm(request.POST)
                    if form2.is_valid():
                        ink_form = form2.save(commit=False)
                        ink_form.client_item = every
                        ink_form.item = Inventory.objects.get(item=color)
                        ink_form.quantity = color_count
                        ink_form.save()
                else:
                    pass

    #Current schedule
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

                sked_dict = {'ID': job,
                             'Task': 'Extrusion',
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

                sked_dict = {'ID': job,
                             'Task': 'Cutting',
                             'Start': j.sked_in,
                             'Finish': j.sked_out,
                             'Resource': mat,
                             'Machine': j.sked_mach,
                             'Worker': j.sked_op
                             }
                plot_list.append(sked_dict)
        if pr:
            for k in pr:
                job = k.job_order_id
                item = ClientItem.objects.get(client_po_id=job)
                product = item.products
                mat = product.material_type

                sked_dict = {'ID': job,
                             'Task': 'Printing',
                             'Start': k.sked_in,
                             'Finish': k.sked_out,
                             'Resource': mat,
                             'Machine': k.sked_mach,
                             'Worker': k.sked_op
                             }
                plot_list.append(sked_dict)
        if la:
            for l in la:
                job = l.job_order_id
                item = ClientItem.objects.get(client_po_id=job)
                product = item.products
                mat = product.material_type

                sked_dict = {'ID': job,
                             'Task': 'Laminating',
                             'Start': l.sked_in,
                             'Finish': l.sked_out,
                             'Resource': mat,
                             'Machine': l.sked_mach,
                             'Worker': l.sked_op
                             }
                plot_list.append(sked_dict)


    #Simulated sched
    cursor = connection.cursor()
    query = "SELECT j.id, i.laminate, i.printed, p.material_type FROM production_mgt_joborder j, sales_mgt_clientitem i, sales_mgt_product p " \
            "WHERE p.id = i.products_id and i.client_po_id = j.id and NOT j.status = 'Waiting' and " \
            "NOT j.status = 'Ready for delivery' and NOT j.status = 'Delivered'"
    cursor.execute(query)
    df = pd.read_sql(query, connection)
    data = {'id': pk,
            'laminate': each.laminate,
            'printed': each.printed,
            'material_type': x }
    df2 = pd.DataFrame(data, index=[0])
    print('df2: ')
    print(df2)
    df = df.append(df2, ignore_index=True)
    print('df after append: ')
    print(df)
    in_production = JobOrder.objects.filter(
        ~Q(status='On Queue') & ~Q(status='Ready for delivery') & ~Q(status='Delivered') & ~Q(status='Waiting'))
    plot_list2 = cpsat.flexible_jobshop(df, None, None, True, True, True, True, in_production)

    machines = Machine.objects.all()
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

    for i in range(len(plot_list2)):
        if start_week <= plot_list2[i]['Start'].date() <= end_week:
            this_week.append(plot_list2[i])
        if plot_list2[i]['Start'].month == today.month:
            this_month.append(plot_list2[i])

    #plot_list (current) VS plot_list2 (simulated) VS job's date required
    new_list = []
    new_list2 = []
    for c in range(len(plot_list)):
        if plot_list[c]['Task'] == 'Cutting':
            new_list.append(plot_list[c])
    for d in range(len(plot_list2)):
        if plot_list2[d]['Task'] == 'Cutting':
            new_list2.append(plot_list2[d])

    d_list = []
    discrepancy = []
    for a in range(len(new_list)):
        for b in range(len(new_list2)):
            if new_list[a]['ID'] == new_list2[b]['ID']:
                job = JobOrder.objects.get(id=new_list[a]['ID'])
                job = job.date_required
                #job = job.replace(tzinfo=None)
                q = new_list[a]['Finish']
                w = new_list2[b]['Finish']
                q = q.replace(tzinfo=None)
                w = w.replace(tzinfo=None)
                CurrentDiff = (w - q)
                CurrentDiff = CurrentDiff - datetime.timedelta(microseconds=CurrentDiff.microseconds)
                ClientDiff = (w.date() - job)
                ClientDiff = ClientDiff - datetime.timedelta(seconds=ClientDiff.seconds,
                                                             microseconds=ClientDiff.microseconds)

                discrepancy = {'ID': new_list[a]['ID'],
                               'CurrentDiff': CurrentDiff,
                               # Simulated VS Current; if (-), it ends EARLIER than previous sched
                               'ClientDiff': ClientDiff  # Simulated VS Client-suggested
                               }
                d_list.append(discrepancy)

    if 'approve_btn' in request.POST:
        #SAVE NEW PRODUCTION SCHEDULE
        in_production = JobOrder.objects.filter(
            ~Q(status='On Queue') & ~Q(status='Ready for delivery') & ~Q(status='Delivered') & ~Q(status='Waiting'))
        save_schedule(request, pk, None, None, True, True, True, True, in_production)
        rush_order.status = 'On Queue'
        rush_order.save()
        return redirect('sales:rush_order_list')

    elif 'deny_btn' in request.POST:
        print('denied')
        rush_order.rush_order = 0
        rush_order.save()

        return redirect('sales:rush_order_list')

    context = {
        'discrepancy' : d_list,
        'client': client,
        'rush_order' : rush_order,
        'credit_status' : credit_status,
        'matreq' : matreq,
        'cylinder_count' : cylinder_count,
        'profit': profit,
        'machines': machines,
        'this_week': this_week,
        'this_month': this_month,
        'week': week,
        'month': month,
        'today': today
    }

    return render(request, 'sales/rush_order_assessment.html', context)


#CLIENT CRUD
def client_add(request):
    form = ClientForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('sales:client_list')

    context = {
        'form' : form,
        'title' : "Add Client",
        'actiontype' : "Submit",
    }
    return render(request, 'sales/client_add.html', context)

def client_list(request):
    data = Client.objects.all()

    context = {
        'title' : 'Client List',
        'data' : data 
    }
    return render(request, 'sales/client_list.html', context)

def client_edit(request, id):
    data = Client.objects.get(id=id)
    form = ClientForm(request.POST or None, instance=data)

    if form.is_valid():
        form.save()
        return redirect('sales:client_list')
    
    context = {
        'form' : form,
        'data' : data,
        'title' : "Edit Client",
        'actiontype' : "Submit",
    }
    return render(request, 'sales/client_add.html', context)

#EMPLOYEE CRUD
def employee_add(request):
    form = EmployeeForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('sales:employee_list')

    context = {
        'form' : form,
        'title' : "Add Employee",
        'actiontype' : "Submit",
    }
    return render(request, 'sales/employee_add.html', context)

def employee_list(request):
    data = Employee.objects.all()
    context = {
        'title': 'Employee List',
        'data' : data 
    }
    return render(request, 'sales/employee_list.html', context)

def employee_edit(request, id):
    data = Employee.objects.get(id=id)
    form = EmployeeForm(request.POST or None, instance=data)
    if form.is_valid():
        form.save()
        return redirect('sales:employee_list')
    
    context = {
        'form' : form,
        'data' : data,
        'title' : "Edit Employee",
        'actiontype' : "Submit",
    }
    return render(request, 'sales/employee_add.html', context)

def employee_details(request, id):
    data = Employee.objects.get(id=id)
    ex_schedule = []
    cu_schedule = []
    pr_schedule = []
    la_schedule = []
    new_sked_op = None
    date = datetime.date.today()
    start_week = date - datetime.timedelta(date.weekday())
    end_week = start_week + datetime.timedelta(7)
    e = ExtruderSchedule.objects.filter(Q(sked_op_id=id) & Q(sked_in__range=[start_week, end_week]))
    c = CuttingSchedule.objects.filter(Q(sked_op_id=id) & Q(sked_in__range=[start_week, end_week]))
    l = LaminatingSchedule.objects.filter(Q(sked_op_id=id) & Q(sked_in__range=[start_week, end_week]))
    p = PrintingSchedule.objects.filter(Q(sked_op_id=id) & Q(sked_in__range=[start_week, end_week]))

    if e:
        for i in e:
            ex_schedule.append(i)
    if c:
        for j in c:
            cu_schedule.append(j)
    if l:
        for k in l:
            la_schedule.append(k)
    if p:
        for x in p:
            pr_schedule.append(x)

    if request.method == 'POST':
        unavailable = None
        for_replacement = None
        if request.POST.get('unavailable1'):
            unavailable = request.POST.get('unavailable1')
            unavailable = dateutil.parser.parse(unavailable)
            for y in e:
                compare = y.sked_in
                compare = compare.replace(tzinfo=None)
                if compare.year == unavailable.year \
                        and compare.month == unavailable.month \
                        and compare.day == unavailable.day \
                        and compare.hour == unavailable.hour:
                    for_replacement = y
                    break
                else:
                    pass
        elif request.POST.get('unavailable2'):
            unavailable = request.POST.get('unavailable2')
            unavailable = dateutil.parser.parse(unavailable)
            for z in c:
                compare = z.sked_in
                compare = compare.replace(tzinfo=None)
                if compare.year == unavailable.year \
                        and compare.month == unavailable.month \
                        and compare.day == unavailable.day \
                        and compare.hour == unavailable.hour:
                    for_replacement = z
                    break
                else:
                    pass
        elif request.POST.get('unavailable3'):
            unavailable = request.POST.get('unavailable3')
            unavailable = dateutil.parser.parse(unavailable)
            for q in p:
                compare = q.sked_in
                compare = compare.replace(tzinfo=None)
                if compare.year == unavailable.year \
                        and compare.month == unavailable.month \
                        and compare.day == unavailable.day \
                        and compare.hour == unavailable.hour:
                    for_replacement = q
                    break
                else:
                    pass
        elif request.POST.get('unavailable4'):
            unavailable = request.POST.get('unavailable4')
            unavailable = dateutil.parser.parse(unavailable)
            for w in l:
                compare = w.sked_in
                compare = compare.replace(tzinfo=None)
                if compare.year == unavailable.year \
                        and compare.month == unavailable.month \
                        and compare.day == unavailable.day \
                        and compare.hour == unavailable.hour:
                    for_replacement = w
                    break
                else:
                    pass
        ekis = []
        di_pweds = []
        di_pweds.extend(list(ExtruderSchedule.objects.filter(sked_in__range=[for_replacement.sked_in, for_replacement.sked_out])))
        di_pweds.extend(list(CuttingSchedule.objects.filter(sked_in__range=[for_replacement.sked_in, for_replacement.sked_out])))
        di_pweds.extend(list(LaminatingSchedule.objects.filter(sked_in__range=[for_replacement.sked_in, for_replacement.sked_out])))
        di_pweds.extend(list(PrintingSchedule.objects.filter(sked_in__range=[for_replacement.sked_in, for_replacement.sked_out])))
        all_workers = Employee.objects.filter(Q(position='Extruder') | Q(position='Cutting') | Q(position='Printing') | Q(position='Laminating'))
        for a in di_pweds:
            ekis.append(a.sked_op)

        new_sked_op = list(set(all_workers).difference(ekis))[0]
        aaa = for_replacement.sked_in
        aaa = aaa.replace(tzinfo=None)
        if new_sked_op and datetime.datetime.now() < aaa:
            for_replacement.sked_op = new_sked_op
            for_replacement.save()
            messages.info(request,
                          'You have reassigned the task for Job '+str(for_replacement.job_order_id)+' scheduled at ' + str(unavailable) + ' to ' + str(new_sked_op) + '.')
        elif datetime.datetime.now() > aaa:
            messages.info(request, 'It is past the time of the task intended to be reassigned!')

    form = EmployeeForm(request.POST or None, instance=data)
    if form.is_valid():
        form.save()
        return redirect('sales:employee_list')

    context = {
        'form':form,
        'data': data,
        'title': 'Employee Details',
        'ex_schedule' : ex_schedule,
        'cu_schedule' : cu_schedule,
        'pr_schedule' : pr_schedule,
        'la_schedule' : la_schedule,
        'new_sked_op' : new_sked_op
    }

    return render(request, 'sales/employee_details.html', context)


def employee_delete(request, id):
    data = Employee.objects.get(id=id)
    data.delete()
    return redirect('sales:employee_list')

#FORECASTING

def demand_forecast(request):
    client = Client.objects.all()
    po = JobOrder.objects.all().order_by('-date_issued')

    context = {
        'client' : client,
        'po' : po,
    }
    return render(request, 'sales/client_demand_forecast.html', context)

def demand_forecast_details(request, id):
    client_po = JobOrder.objects.filter(client_id=id)
    client = Client.objects.get(id=id)
    i = ClientItem.objects.all()
    forecast_ses = []
    forecast_hwes = []
    forecast_moving_average = []
    product = []
    items = []
    for every in i:
        for each in client_po:
            if every.client_po_id == each.id:
                items.append(every.products_id)

    if items:
        item = most_common(items)
        item = Product.objects.get(id=item)
        cursor = connection.cursor()
        forecast_ses = []
        forecast_hwes = []
        forecast_moving_average = []

        query = 'SELECT po.date_issued, poi.quantity FROM  production_mgt_joborder po, sales_mgt_clientitem poi WHERE ' \
                'po.client_id = '+str(id)+' AND poi.client_po_id = po.id AND poi.products_id = '+str(item.id)

        cursor.execute(query)
        df = pd.read_sql(query, connection)

        product = item

        a = TimeSeriesForecasting.forecast_ses(df)
        a[1] = int(float(a[1]))
        forecast_ses.extend(a)
        b = TimeSeriesForecasting.forecast_hwes(df)
        b[1] = int(float(b[1]))
        forecast_hwes.extend(b)
        c = TimeSeriesForecasting.forecast_moving_average(df)
        c[1] = int(float(c[1]))
        forecast_moving_average.extend(c)

    context = {
        #'forecast_decomposition': forecast_decomposition,
        'forecast_ses': forecast_ses,
        'forecast_hwes': forecast_hwes,
        'forecast_moving_average': forecast_moving_average,
        #'forecast_arima': forecast_arima,
        #'item' : item,
        'client' : client,
        'product' : product
    }

    return render(request, 'sales/client_demand_forecast_details.html', context)

def assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout):
    assigned = False
    occupied = False
    operator = None
    random.shuffle(list(ideal_workers))

    for q in ideal_workers:
        occupied = False
        for w in all_skeds:
            if w.sked_in.date() == skedin.date() and w.sked_op_id == q.id:
                occupied = True
                break
        if not occupied:
            if ideal_sched[x]['Task'] == 'Extrusion':
                e = ExtruderSchedule(job_order_id=ideal_sched[x]['ID'], ideal=True, sked_op=q, sked_in=skedin, sked_out=skedout,
                                 sked_mach=ideal_sched[x]['Machine'])
                e.save()
                print('CREATED: ' + str(job) + str(skedin) +' for ' + str(q) +' from ideal workers')
                operator = q
                assigned = True
                break
            elif ideal_sched[x]['Task'] == 'Cutting':
                c = CuttingSchedule(job_order_id=ideal_sched[x]['ID'], ideal=True, sked_op=q, sked_in=skedin, sked_out=skedout,
                                 sked_mach=ideal_sched[x]['Machine'])
                c.save()
                print('CREATED: ' + str(job) + str(skedin) +' for ' + str(q) +' from ideal workers')
                operator = q
                assigned = True
                break
            elif ideal_sched[x]['Task'] == 'Printing':
                p = PrintingSchedule(job_order_id=ideal_sched[x]['ID'], ideal=True, sked_op=q, sked_in=skedin, sked_out=skedout,
                                 sked_mach=ideal_sched[x]['Machine'])
                p.save()
                print('CREATED: ' + str(job) + str(skedin) +' for ' + str(q) +' from ideal workers')
                operator = q
                assigned = True
                break
            elif ideal_sched[x]['Task'] == 'Laminating':
                l = LaminatingSchedule(job_order_id=ideal_sched[x]['ID'], ideal=True, sked_op=q, sked_in=skedin, sked_out=skedout,
                                 sked_mach=ideal_sched[x]['Machine'])
                l.save()
                print('CREATED: ' + str(job) + str(skedin) +' for ' + str(q) +' from ideal workers')
                operator = q
                assigned = True
                break

    random.shuffle(list(other_workers))
    # Elif no one from ideal_workers, repeat above and get from all other workers.
    if not assigned:
        print('NOT ASSIGNED')
        for e in other_workers:
            occupied = False
            print('e: '+str(e))
            for r in all_skeds:
                if r.sked_in.date() == skedin.date() and r.sked_op_id == e.id:
                    occupied = True
                    break
            if not occupied:
                if ideal_sched[x]['Task'] == 'Extrusion':
                    e = ExtruderSchedule(job_order_id=ideal_sched[x]['ID'], ideal=True, sked_op=e, sked_in=skedin, sked_out=skedout,
                                    sked_mach=ideal_sched[x]['Machine'])
                    e.save()
                    print('CREATED: ' + str(job) + str(skedin) + ' for ' + str(e) + ' from other workers')
                    operator = e
                    assigned = True
                    break
                elif ideal_sched[x]['Task'] == 'Cutting':
                    c = CuttingSchedule(job_order_id=ideal_sched[x]['ID'], ideal=True, sked_op=e, sked_in=skedin, sked_out=skedout,
                                     sked_mach=ideal_sched[x]['Machine'])
                    c.save()
                    print('CREATED: ' + str(job) + str(skedin) + ' for ' + str(e) + ' from other workers')
                    operator = e
                    assigned = True
                    break
                elif ideal_sched[x]['Task'] == 'Printing':
                    p = PrintingSchedule(job_order_id=ideal_sched[x]['ID'], ideal=True, sked_op=e, sked_in=skedin, sked_out=skedout,
                                     sked_mach=ideal_sched[x]['Machine'])
                    p.save()
                    print('CREATED: ' + str(job) + str(skedin) + ' for ' + str(e) + ' from other workers')
                    operator = e
                    assigned = True
                    break
                elif ideal_sched[x]['Task'] == 'Laminating':
                    l = LaminatingSchedule(job_order_id=ideal_sched[x]['ID'], ideal=True, sked_op=e, sked_in=skedin, sked_out=skedout,
                                     sked_mach=ideal_sched[x]['Machine'])
                    l.save()
                    print('CREATED: ' + str(job) + str(skedin) + ' for ' + str(e) + ' from other workers')
                    operator = e
                    assigned = True
                    break
    # Else, make ideal schedule with sked_op = None.
    if not assigned:
        if ideal_sched[x]['Task'] == 'Extrusion':
            e = ExtruderSchedule(job_order_id=ideal_sched[x]['ID'], ideal=True, sked_op=None, sked_in=skedin, sked_out=skedout,
                             sked_mach=ideal_sched[x]['Machine'])
            e.save()
            print('CREATED: ' + str(job) + str(skedin) + ' for None')
            assigned = True
        elif ideal_sched[x]['Task'] == 'Cutting':
            c = CuttingSchedule(job_order_id=ideal_sched[x]['ID'], ideal=True, sked_op=None, sked_in=skedin, sked_out=skedout,
                             sked_mach=ideal_sched[x]['Machine'])
            c.save()
            print('CREATED: ' + str(job) + str(skedin) + ' for None')
            assigned = True
        elif ideal_sched[x]['Task'] == 'Printing':
            p = PrintingSchedule(job_order_id=ideal_sched[x]['ID'], ideal=True, sked_op=None, sked_in=skedin, sked_out=skedout,
                             sked_mach=ideal_sched[x]['Machine'])
            p.save()
            print('CREATED: ' + str(job) + str(skedin) + ' for None')
            assigned = True
        elif ideal_sched[x]['Task'] == 'Laminating':
            l = LaminatingSchedule(job_order_id=ideal_sched[x]['ID'], ideal=True, sked_op=None, sked_in=skedin, sked_out=skedout,
                             sked_mach=ideal_sched[x]['Machine'])
            l.save()
            print('CREATED: ' + str(job) + str(skedin) + ' for None')
            assigned = True

    return operator

def divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout, skedindate, shift1, shift2, shift3, new_ideal_sched):
    #assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout)
    sked_dict = {'ID': ideal_sched[x]['ID'],
                 'Machine': ideal_sched[x]['Machine'],
                 'Task': ideal_sched[x]['Task'],
                 'Start': skedin,
                 'Finish': skedout,
                 'Resource': ideal_sched[x]['Resource'],
                 'Worker': assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin,
                                           skedout),
                 }
    new_ideal_sched.append(sked_dict)
    duration = ideal_sched[x]['Finish'] - ideal_sched[x]['Start']
    duration -= timedelta(hours=8)
    duration = math.ceil(duration.total_seconds() / 3600)
    remaining_shifts = math.ceil(duration / 8)
    count = remaining_shifts
    remaining_days = math.ceil(remaining_shifts / 3)
    for a in range(remaining_days):
        #Shift 2
        if count > 0:
            all_skeds = []
            all_skeds.extend(ExtruderSchedule.objects.filter(ideal=True))
            all_skeds.extend(CuttingSchedule.objects.filter(ideal=True))
            all_skeds.extend(PrintingSchedule.objects.filter(ideal=True))
            all_skeds.extend(LaminatingSchedule.objects.filter(ideal=True))
            skedin = datetime.combine(skedindate, time(14, 0))
            skedout = datetime.combine(skedindate, time(22, 0))
            shift2.append((job, skedindate))
            #assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout)
            sked_dict = {'ID': ideal_sched[x]['ID'],
                         'Machine': ideal_sched[x]['Machine'],
                         'Task': ideal_sched[x]['Task'],
                         'Start': skedin,
                         'Finish': skedout,
                         'Resource': ideal_sched[x]['Resource'],
                         'Worker': assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout),
                         }
            new_ideal_sched.append(sked_dict)
            count -= 1
        #Shift 3
        if count > 0:
            all_skeds = []
            all_skeds.extend(ExtruderSchedule.objects.filter(ideal=True))
            all_skeds.extend(CuttingSchedule.objects.filter(ideal=True))
            all_skeds.extend(PrintingSchedule.objects.filter(ideal=True))
            all_skeds.extend(LaminatingSchedule.objects.filter(ideal=True))
            skedin = datetime.combine(skedindate, time(22, 0))
            skedout = datetime.combine(skedindate + timedelta(days=1), time(6, 0))
            shift3.append((job, skedindate))
            #assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout)
            sked_dict = {'ID': ideal_sched[x]['ID'],
                         'Machine': ideal_sched[x]['Machine'],
                         'Task': ideal_sched[x]['Task'],
                         'Start': skedin,
                         'Finish': skedout,
                         'Resource': ideal_sched[x]['Resource'],
                         'Worker': assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin,
                                                   skedout),
                         }
            new_ideal_sched.append(sked_dict)
            count -= 1
            skedindate += timedelta(days=1)
        #Shift 1 next day
        if count > 0:
            all_skeds = []
            all_skeds.extend(ExtruderSchedule.objects.filter(ideal=True))
            all_skeds.extend(CuttingSchedule.objects.filter(ideal=True))
            all_skeds.extend(PrintingSchedule.objects.filter(ideal=True))
            all_skeds.extend(LaminatingSchedule.objects.filter(ideal=True))
            skedin = datetime.combine(skedindate, time(6, 0))
            skedout = datetime.combine(skedindate, time(14, 0))
            shift1.append((job, skedindate))
            #assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout)
            sked_dict = {'ID': ideal_sched[x]['ID'],
                         'Machine': ideal_sched[x]['Machine'],
                         'Task': ideal_sched[x]['Task'],
                         'Start': skedin,
                         'Finish': skedout,
                         'Resource': ideal_sched[x]['Resource'],
                         'Worker': assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin,
                                                   skedout),
                         }
            new_ideal_sched.append(sked_dict)
            count -= 1

    if count == 0:
        print('SEPARATED TO SHIFTS: ' + str(ideal_sched[x]['ID']))

def divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout, skedindate, shift1, shift2, shift3, new_ideal_sched):
    #assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout)
    sked_dict = {'ID': ideal_sched[x]['ID'],
                 'Machine': ideal_sched[x]['Machine'],
                 'Task': ideal_sched[x]['Task'],
                 'Start': skedin,
                 'Finish': skedout,
                 'Resource': ideal_sched[x]['Resource'],
                 'Worker': assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin,
                                           skedout),
                 }
    new_ideal_sched.append(sked_dict)
    duration = ideal_sched[x]['Finish'] - ideal_sched[x]['Start']
    duration -= timedelta(hours=8)
    duration = math.ceil(duration.total_seconds() / 3600)
    remaining_shifts = math.ceil(duration / 8)
    count = remaining_shifts
    remaining_days = math.ceil(remaining_shifts / 3)
    for a in range(remaining_days):
        #Shift 3
        if count > 0:
            all_skeds = []
            all_skeds.extend(ExtruderSchedule.objects.filter(ideal=True))
            all_skeds.extend(CuttingSchedule.objects.filter(ideal=True))
            all_skeds.extend(PrintingSchedule.objects.filter(ideal=True))
            all_skeds.extend(LaminatingSchedule.objects.filter(ideal=True))
            skedin = datetime.combine(skedindate, time(22, 0))
            skedout = datetime.combine(skedindate + timedelta(days=1), time(6, 0))
            shift3.append((job, skedindate))
            #assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout)
            sked_dict = {'ID': ideal_sched[x]['ID'],
                         'Machine': ideal_sched[x]['Machine'],
                         'Task': ideal_sched[x]['Task'],
                         'Start': skedin,
                         'Finish': skedout,
                         'Resource': ideal_sched[x]['Resource'],
                         'Worker': assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout),
                         }
            new_ideal_sched.append(sked_dict)
            count -= 1
            skedindate += timedelta(days=1)
        #Shift 1 next day
        if count > 0:
            all_skeds = []
            all_skeds.extend(ExtruderSchedule.objects.filter(ideal=True))
            all_skeds.extend(CuttingSchedule.objects.filter(ideal=True))
            all_skeds.extend(PrintingSchedule.objects.filter(ideal=True))
            all_skeds.extend(LaminatingSchedule.objects.filter(ideal=True))
            skedin = datetime.combine(skedindate, time(6, 0))
            skedout = datetime.combine(skedindate, time(14, 0))
            shift1.append((job, skedindate))
            #assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout)
            sked_dict = {'ID': ideal_sched[x]['ID'],
                         'Machine': ideal_sched[x]['Machine'],
                         'Task': ideal_sched[x]['Task'],
                         'Start': skedin,
                         'Finish': skedout,
                         'Resource': ideal_sched[x]['Resource'],
                         'Worker': assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin,
                                                   skedout),
                         }
            new_ideal_sched.append(sked_dict)
            count -= 1
        #Shift 2 next day
        if count > 0:
            all_skeds = []
            all_skeds.extend(ExtruderSchedule.objects.filter(ideal=True))
            all_skeds.extend(CuttingSchedule.objects.filter(ideal=True))
            all_skeds.extend(PrintingSchedule.objects.filter(ideal=True))
            all_skeds.extend(LaminatingSchedule.objects.filter(ideal=True))
            skedin = datetime.combine(skedindate, time(14, 0))
            skedout = datetime.combine(skedindate, time(22, 0))
            shift2.append((job, skedindate))
            #assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout)
            sked_dict = {'ID': ideal_sched[x]['ID'],
                         'Machine': ideal_sched[x]['Machine'],
                         'Task': ideal_sched[x]['Task'],
                         'Start': skedin,
                         'Finish': skedout,
                         'Resource': ideal_sched[x]['Resource'],
                         'Worker': assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin,
                                                   skedout),
                         }
            new_ideal_sched.append(sked_dict)
            count -= 1

    if count == 0:
        print('SEPARATED TO SHIFTS: ' + str(ideal_sched[x]['ID']))

def divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout, skedindate, shift1, shift2, shift3, new_ideal_sched):
    #assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout)
    sked_dict = {'ID': ideal_sched[x]['ID'],
                 'Machine': ideal_sched[x]['Machine'],
                 'Task': ideal_sched[x]['Task'],
                 'Start': skedin,
                 'Finish': skedout,
                 'Resource': ideal_sched[x]['Resource'],
                 'Worker': assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin,
                                           skedout),
                 }
    new_ideal_sched.append(sked_dict)
    duration = ideal_sched[x]['Finish'] - ideal_sched[x]['Start']
    duration -= timedelta(hours=8)
    duration = math.ceil(duration.total_seconds() / 3600)
    remaining_shifts = math.ceil(duration / 8)
    count = remaining_shifts
    remaining_days = math.ceil(remaining_shifts / 3)
    for a in range(remaining_days):
        #Shift 1 next day
        if count > 0:
            all_skeds = []
            all_skeds.extend(ExtruderSchedule.objects.filter(ideal=True))
            all_skeds.extend(CuttingSchedule.objects.filter(ideal=True))
            all_skeds.extend(PrintingSchedule.objects.filter(ideal=True))
            all_skeds.extend(LaminatingSchedule.objects.filter(ideal=True))
            skedindate += timedelta(days=1)
            skedin = datetime.combine(skedindate, time(6, 0))
            skedout = datetime.combine(skedindate, time(14, 0))
            shift1.append((job, skedindate))
            #assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout)
            sked_dict = {'ID': ideal_sched[x]['ID'],
                         'Machine': ideal_sched[x]['Machine'],
                         'Task': ideal_sched[x]['Task'],
                         'Start': skedin,
                         'Finish': skedout,
                         'Resource': ideal_sched[x]['Resource'],
                         'Worker': assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout),
                         }
            new_ideal_sched.append(sked_dict)
            count -= 1
        #Shift 2 next day
        if count > 0:
            all_skeds = []
            all_skeds.extend(ExtruderSchedule.objects.filter(ideal=True))
            all_skeds.extend(CuttingSchedule.objects.filter(ideal=True))
            all_skeds.extend(PrintingSchedule.objects.filter(ideal=True))
            all_skeds.extend(LaminatingSchedule.objects.filter(ideal=True))
            skedin = datetime.combine(skedindate, time(14, 0))
            skedout = datetime.combine(skedindate, time(22, 0))
            shift2.append((job, skedindate))
            #assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout)
            sked_dict = {'ID': ideal_sched[x]['ID'],
                         'Machine': ideal_sched[x]['Machine'],
                         'Task': ideal_sched[x]['Task'],
                         'Start': skedin,
                         'Finish': skedout,
                         'Resource': ideal_sched[x]['Resource'],
                         'Worker': assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin,
                                                   skedout),
                         }
            new_ideal_sched.append(sked_dict)
            count -= 1
            skedindate += timedelta(days=1)
        #Shift 3 next day
        if count > 0:
            all_skeds = []
            all_skeds.extend(ExtruderSchedule.objects.filter(ideal=True))
            all_skeds.extend(CuttingSchedule.objects.filter(ideal=True))
            all_skeds.extend(PrintingSchedule.objects.filter(ideal=True))
            all_skeds.extend(LaminatingSchedule.objects.filter(ideal=True))
            skedin = datetime.combine(skedindate, time(22, 0))
            skedout = datetime.combine(skedindate + timedelta(days=1), time(6, 0))
            shift3.append((job, skedindate))
            #assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout)
            sked_dict = {'ID': ideal_sched[x]['ID'],
                         'Machine': ideal_sched[x]['Machine'],
                         'Task': ideal_sched[x]['Task'],
                         'Start': skedin,
                         'Finish': skedout,
                         'Resource': ideal_sched[x]['Resource'],
                         'Worker': assign_operator(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin,
                                                   skedout),
                         }
            new_ideal_sched.append(sked_dict)
            count -= 1
            skedindate += timedelta(days=1)

    if count == 0:
        print('SEPARATED TO SHIFTS: ' + str(ideal_sched[x]['ID']))


def save_schedule(request, pk, actual_out, job_match, extrusion_not_final, cutting_not_final, printing_not_final, laminating_not_final, in_production):
    ideal_ex = ExtruderSchedule.objects.filter(ideal=True)
    ideal_cu = CuttingSchedule.objects.filter(ideal=True)
    ideal_la = LaminatingSchedule.objects.filter(ideal=True)
    ideal_pr = PrintingSchedule.objects.filter(ideal=True)

    for x in ideal_ex:
        job = x.job_order
        if job.status == 'Under Extrusion' or job.status == 'On Queue':
            x.delete()
            for b in ideal_cu:
                if b.job_order_id == job.id and b.id is not None:
                    b.delete()
            for f in ideal_la:
                if f.job_order_id == job.id and f.id is not None:
                    f.delete()
            for g in ideal_pr:
                if g.job_order_id == job.id and g.id is not None:
                    g.delete()
            print('DELETED EX: ' + str(job))
    for y in ideal_cu:
        job = y.job_order
        if job.status == 'Under Cutting':
            y.delete()
            print('DELETED CU: ' + str(job))
    for z in ideal_la:
        job = z.job_order
        if job.status == 'Under Laminating':
            z.delete()
            for c in ideal_cu:
                if c.job_order_id == job.id and c.id is not None:
                    c.delete()
            print('DELETED LA: ' + str(job))
    for a in ideal_pr:
        job = a.job_order
        if job.status == 'Under Printing':
            a.delete()
            for d in ideal_cu:
                if d.job_order_id == job.id and d.id is not None:
                    d.delete()
            for h in ideal_la:
                if h.job_order_id == job.id and h.id is not None:
                    h.delete()
            print('DELETED PR: ' + str(job))

    cursor = connection.cursor()
    query = "SELECT j.id, i.laminate, i.printed, p.material_type FROM production_mgt_joborder j, sales_mgt_clientitem i, sales_mgt_product p " \
            "WHERE p.id = i.products_id and i.client_po_id = j.id and " \
            "NOT j.status=" + "'Waiting'" + " and NOT j.status=" + "'Ready for delivery'" + " and NOT j.status =" + "'Delivered'"
    cursor.execute(query)
    df = pd.read_sql(query, connection)

    if pk is not None:
        item = ClientItem.objects.get(client_po_id=pk)
        mat = item.products.material_type

        data = {'id': pk,
                'laminate': item.laminate,
                'printed': item.printed,
                'material_type': mat}
        df2 = pd.DataFrame(data, index=[0])
        df = df.append(df2, ignore_index=True)

    ideal_sched = cpsat.flexible_jobshop(df, actual_out, job_match, extrusion_not_final, cutting_not_final,
                                         printing_not_final, laminating_not_final, in_production)

    [print("%s %s %s %s %s %s %s\n" % (
    item['ID'], item['Machine'], item['Task'], item['Start'], item['Finish'], item['Resource'], item['Worker']))
     for item in ideal_sched]

    shift1 = []  # 0600-1400
    shift2 = []  # 1400-2200
    shift3 = []  # 2200-0600'
    new_ideal_sched = []
    ideal_sched.sort(key=lambda i: i['Start'])

    for x in range(len(ideal_sched)):
        if 2 <= ideal_sched[x]['Start'].hour < 10:
            print('JOB: ' + str(ideal_sched[x]['ID']))
            job = (ideal_sched[x]['ID'], ideal_sched[x]['Task'])
            skedin = datetime.combine(ideal_sched[x]['Start'].date(), time(6, 0))
            skedindate = skedin.date()
            skedout = datetime.combine(ideal_sched[x]['Start'].date(), time(14, 0))
            push = 0
            job_shifts = []
            occupied_shifts = []
            latest = None
            each = None
            all_skeds = []
            all_skeds.extend(ExtruderSchedule.objects.filter(ideal=True))
            all_skeds.extend(CuttingSchedule.objects.filter(ideal=True))
            all_skeds.extend(PrintingSchedule.objects.filter(ideal=True))
            all_skeds.extend(LaminatingSchedule.objects.filter(ideal=True))
            shift1.append((job, skedindate))
            if ideal_sched[x]['Task'] == 'Extrusion':
                ideal_workers = Employee.objects.filter(position='Extruder')
                other_workers = Employee.objects.filter(
                    Q(position='Cutting') | Q(position='Printing') | Q(position='Laminating'))
                # If someone from ideal_workers =! sked_op of any ideal schedule of that day, assign shift.
                for each in all_skeds:
                    if each.job_order_id == ideal_sched[x]['ID']:
                        job_shifts.append(each)
                job_shifts.sort(key=lambda x: x.sked_in)
                if job_shifts:
                    latest = job_shifts[-1]
                for each in all_skeds:
                    if each.sked_mach == ideal_sched[x]['Machine']:
                        occupied_shifts.append(each)
                occupied_shifts.sort(key=lambda x: x.sked_in)
                if occupied_shifts:
                    each = occupied_shifts[-1]
                if each and latest:
                    if each.sked_in.time() == time(22, 0) or latest.sked_in.time() == time(22, 0):
                        if latest is None or each.sked_in > latest.sked_in:
                            latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0) or latest.sked_in.time() == time(14, 0):
                        if latest is None or each.sked_in > latest.sked_in:
                            latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0) or latest.sked_in.time() == time(6, 0):
                        if latest is None or each.sked_in > latest.sked_in:
                            latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif each:
                    if each.sked_in.time() == time(22, 0):
                        latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0):
                        latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0):
                        latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif latest:
                    if latest.sked_in.time() == time(22, 0):
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif latest.sked_in.time() == time(14, 0):
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif latest.sked_in.time() == time(6, 0):
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                if push == 1:
                    print('PUSH TO SHIFT 1: ' + str(ideal_sched[x]['ID']))
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 2:
                    print('PUSH TO SHIFT 2: ' + str(ideal_sched[x]['ID']))
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 3:
                    print('PUSH TO SHIFT 3: ' + str(ideal_sched[x]['ID']))
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                else:
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)
            elif ideal_sched[x]['Task'] == 'Cutting':
                ideal_workers = Employee.objects.filter(position='Cutting')
                other_workers = Employee.objects.filter(
                    Q(position='Extruder') | Q(position='Printing') | Q(position='Laminating'))
                for each in all_skeds:
                    if each.job_order_id == ideal_sched[x]['ID']:
                        job_shifts.append(each)
                job_shifts.sort(key=lambda x: x.sked_in)
                if job_shifts:
                    latest = job_shifts[-1]
                for each in all_skeds:
                    if each.sked_mach == ideal_sched[x]['Machine']:
                        occupied_shifts.append(each)
                occupied_shifts.sort(key=lambda x: x.sked_in)
                if occupied_shifts:
                    each = occupied_shifts[-1]
                if each and latest:
                    if each.sked_in.time() == time(22, 0) or latest.sked_in.time() == time(22, 0):
                        if latest is None or each.sked_in > latest.sked_in:
                            latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0) or latest.sked_in.time() == time(14, 0):
                        if latest is None or each.sked_in > latest.sked_in:
                            latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0) or latest.sked_in.time() == time(6, 0):
                        if latest is None or each.sked_in > latest.sked_in:
                            latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif each:
                    if each.sked_in.time() == time(22, 0):
                        latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0):
                        latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0):
                        latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif latest:
                    if latest.sked_in.time() == time(22, 0):
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif latest.sked_in.time() == time(14, 0):
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif latest.sked_in.time() == time(6, 0):
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                if push == 1:
                    print('PUSH TO SHIFT 1: ' + str(ideal_sched[x]['ID']))
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 2:
                    print('PUSH TO SHIFT 2: ' + str(ideal_sched[x]['ID']))
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 3:
                    print('PUSH TO SHIFT 3: ' + str(ideal_sched[x]['ID']))
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                else:
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)
            elif ideal_sched[x]['Task'] == 'Printing':
                ideal_workers = Employee.objects.filter(position='Printing')
                other_workers = Employee.objects.filter(
                    Q(position='Extruder') | Q(position='Cutting') | Q(position='Laminating'))
                for each in all_skeds:
                    if each.job_order_id == ideal_sched[x]['ID']:
                        job_shifts.append(each)
                job_shifts.sort(key=lambda x: x.sked_in)
                if job_shifts:
                    latest = job_shifts[-1]
                for each in all_skeds:
                    if each.sked_mach == ideal_sched[x]['Machine']:
                        occupied_shifts.append(each)
                occupied_shifts.sort(key=lambda x: x.sked_in)
                if occupied_shifts:
                    each = occupied_shifts[-1]
                if each and latest:
                    if each.sked_in.time() == time(22, 0) or latest.sked_in.time() == time(22, 0):
                        if latest is None or each.sked_in > latest.sked_in:
                            latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0) or latest.sked_in.time() == time(14, 0):
                        if latest is None or each.sked_in > latest.sked_in:
                            latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0) or latest.sked_in.time() == time(6, 0):
                        if latest is None or each.sked_in > latest.sked_in:
                            latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif each:
                    if each.sked_in.time() == time(22, 0):
                        latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0):
                        latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0):
                        latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif latest:
                    if latest.sked_in.time() == time(22, 0):
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif latest.sked_in.time() == time(14, 0):
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif latest.sked_in.time() == time(6, 0):
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                if push == 1:
                    print('PUSH TO SHIFT 1: ' + str(ideal_sched[x]['ID']))
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 2:
                    print('PUSH TO SHIFT 2: ' + str(ideal_sched[x]['ID']))
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 3:
                    print('PUSH TO SHIFT 3: ' + str(ideal_sched[x]['ID']))
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                else:
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

            elif ideal_sched[x]['Task'] == 'Laminating':
                ideal_workers = Employee.objects.filter(position='Laminating')
                other_workers = Employee.objects.filter(
                    Q(position='Extruder') | Q(position='Cutting') | Q(position='Printing'))
                for each in all_skeds:
                    if each.job_order_id == ideal_sched[x]['ID']:
                        job_shifts.append(each)
                job_shifts.sort(key=lambda x: x.sked_in)
                if job_shifts:
                    latest = job_shifts[-1]
                for each in all_skeds:
                    if each.sked_mach == ideal_sched[x]['Machine']:
                        occupied_shifts.append(each)
                occupied_shifts.sort(key=lambda x: x.sked_in)
                if occupied_shifts:
                    each = occupied_shifts[-1]
                if each and latest:
                    if each.sked_in.time() == time(22, 0) or latest.sked_in.time() == time(22, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0) or latest.sked_in.time() == time(14, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0) or latest.sked_in.time() == time(6, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif each:
                    if each.sked_in.time() == time(22, 0):
                        latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0):
                        latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0):
                        latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif latest:
                    if latest.sked_in.time() == time(22, 0):
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif latest.sked_in.time() == time(14, 0):
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif latest.sked_in.time() == time(6, 0):
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                if push == 1:
                    print('PUSH TO SHIFT 1: ' + str(ideal_sched[x]['ID']))
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 2:
                    print('PUSH TO SHIFT 2: ' + str(ideal_sched[x]['ID']))
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 3:
                    print('PUSH TO SHIFT 3: ' + str(ideal_sched[x]['ID']))
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                else:
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

        elif 10 <= ideal_sched[x]['Start'].hour < 18:
            print('JOB: ' + str(ideal_sched[x]['ID']))
            job = (ideal_sched[x]['ID'], ideal_sched[x]['Task'])
            skedin = datetime.combine(ideal_sched[x]['Start'].date(), time(14, 0))
            skedindate = skedin.date()
            skedout = datetime.combine(ideal_sched[x]['Start'].date(), time(22, 0))
            push = 0
            job_shifts = []
            occupied_shifts = []
            latest = None
            each = None
            all_skeds = []
            all_skeds.extend(ExtruderSchedule.objects.filter(ideal=True))
            all_skeds.extend(CuttingSchedule.objects.filter(ideal=True))
            all_skeds.extend(PrintingSchedule.objects.filter(ideal=True))
            all_skeds.extend(LaminatingSchedule.objects.filter(ideal=True))
            shift1.append((job, skedindate))
            if ideal_sched[x]['Task'] == 'Extrusion':
                ideal_workers = Employee.objects.filter(position='Extruder')
                other_workers = Employee.objects.filter(Q(position='Cutting') | Q(position='Printing'))
                for each in all_skeds:
                    if each.job_order_id == ideal_sched[x]['ID']:
                        job_shifts.append(each)
                job_shifts.sort(key=lambda x: x.sked_in)
                if job_shifts:
                    latest = job_shifts[-1]
                for each in all_skeds:
                    if each.sked_mach == ideal_sched[x]['Machine']:
                        occupied_shifts.append(each)
                occupied_shifts.sort(key=lambda x: x.sked_in)
                if occupied_shifts:
                    each = occupied_shifts[-1]
                if each and latest:
                    if each.sked_in.time() == time(22, 0) or latest.sked_in.time() == time(22, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0) or latest.sked_in.time() == time(14, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0) or latest.sked_in.time() == time(6, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif each:
                    if each.sked_in.time() == time(22, 0):
                        latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0):
                        latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0):
                        latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif latest:
                    if latest.sked_in.time() == time(22, 0):
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif latest.sked_in.time() == time(14, 0):
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif latest.sked_in.time() == time(6, 0):
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                if push == 1:
                    print('PUSH TO SHIFT 1: ' + str(ideal_sched[x]['ID']))
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 2:
                    print('PUSH TO SHIFT 2: ' + str(ideal_sched[x]['ID']))
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 3:
                    print('PUSH TO SHIFT 3: ' + str(ideal_sched[x]['ID']))
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                else:
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

            elif ideal_sched[x]['Task'] == 'Cutting':
                ideal_workers = Employee.objects.filter(position='Cutting')
                other_workers = Employee.objects.filter(
                    Q(position='Extruder') | Q(position='Printing') | Q(position='Laminating'))
                for each in all_skeds:
                    if each.job_order_id == ideal_sched[x]['ID']:
                        job_shifts.append(each)
                job_shifts.sort(key=lambda x: x.sked_in)
                if job_shifts:
                    latest = job_shifts[-1]
                for each in all_skeds:
                    if each.sked_mach == ideal_sched[x]['Machine']:
                        occupied_shifts.append(each)
                occupied_shifts.sort(key=lambda x: x.sked_in)
                if occupied_shifts:
                    each = occupied_shifts[-1]
                if each and latest:
                    if each.sked_in.time() == time(22, 0) or latest.sked_in.time() == time(22, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0) or latest.sked_in.time() == time(14, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0) or latest.sked_in.time() == time(6, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif each:
                    if each.sked_in.time() == time(22, 0):
                        latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0):
                        latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0):
                        latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif latest:
                    if latest.sked_in.time() == time(22, 0):
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif latest.sked_in.time() == time(14, 0):
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif latest.sked_in.time() == time(6, 0):
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                if push == 1:
                    print('PUSH TO SHIFT 1: ' + str(ideal_sched[x]['ID']))
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 2:
                    print('PUSH TO SHIFT 2: ' + str(ideal_sched[x]['ID']))
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 3:
                    print('PUSH TO SHIFT 3: ' + str(ideal_sched[x]['ID']))
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                else:
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

            elif ideal_sched[x]['Task'] == 'Printing':
                ideal_workers = Employee.objects.filter(position='Printing')
                other_workers = Employee.objects.filter(
                    Q(position='Extruder') | Q(position='Cutting') | Q(position='Laminating'))
                for each in all_skeds:
                    if each.job_order_id == ideal_sched[x]['ID']:
                        job_shifts.append(each)
                job_shifts.sort(key=lambda x: x.sked_in)
                if job_shifts:
                    latest = job_shifts[-1]
                for each in all_skeds:
                    if each.sked_mach == ideal_sched[x]['Machine']:
                        occupied_shifts.append(each)
                occupied_shifts.sort(key=lambda x: x.sked_in)
                if occupied_shifts:
                    each = occupied_shifts[-1]
                if each and latest:
                    if each.sked_in.time() == time(22, 0) or latest.sked_in.time() == time(22, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0) or latest.sked_in.time() == time(14, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0) or latest.sked_in.time() == time(6, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif each:
                    if each.sked_in.time() == time(22, 0):
                        latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0):
                        latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0):
                        latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif latest:
                    if latest.sked_in.time() == time(22, 0):
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif latest.sked_in.time() == time(14, 0):
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif latest.sked_in.time() == time(6, 0):
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                if push == 1:
                    print('PUSH TO SHIFT 1: ' + str(ideal_sched[x]['ID']))
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 2:
                    print('PUSH TO SHIFT 2: ' + str(ideal_sched[x]['ID']))
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 3:
                    print('PUSH TO SHIFT 3: ' + str(ideal_sched[x]['ID']))
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                else:
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

            elif ideal_sched[x]['Task'] == 'Laminating':
                ideal_workers = Employee.objects.filter(position='Laminating')
                other_workers = Employee.objects.filter(
                    Q(position='Extruder') | Q(position='Cutting') | Q(position='Printing'))
                for each in all_skeds:
                    if each.job_order_id == ideal_sched[x]['ID']:
                        job_shifts.append(each)
                job_shifts.sort(key=lambda x: x.sked_in)
                if job_shifts:
                    latest = job_shifts[-1]
                for each in all_skeds:
                    if each.sked_mach == ideal_sched[x]['Machine']:
                        occupied_shifts.append(each)
                occupied_shifts.sort(key=lambda x: x.sked_in)
                if occupied_shifts:
                    each = occupied_shifts[-1]
                if each and latest:
                    if each.sked_in.time() == time(22, 0) or latest.sked_in.time() == time(22, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0) or latest.sked_in.time() == time(14, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0) or latest.sked_in.time() == time(6, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif each:
                    if each.sked_in.time() == time(22, 0):
                        latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0):
                        latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0):
                        latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif latest:
                    if latest.sked_in.time() == time(22, 0):
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif latest.sked_in.time() == time(14, 0):
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif latest.sked_in.time() == time(6, 0):
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                if push == 1:
                    print('PUSH TO SHIFT 1: ' + str(ideal_sched[x]['ID']))
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 2:
                    print('PUSH TO SHIFT 2: ' + str(ideal_sched[x]['ID']))
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 3:
                    print('PUSH TO SHIFT 3: ' + str(ideal_sched[x]['ID']))
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                else:
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

        elif 18 <= ideal_sched[x]['Start'].hour or ideal_sched[x]['Start'].hour > 2:
            print('JOB: ' + str(ideal_sched[x]['ID']))
            job = (ideal_sched[x]['ID'], ideal_sched[x]['Task'])
            skedin = datetime.combine(ideal_sched[x]['Start'].date(), time(22, 0))
            skedindate = skedin.date()
            skedout = datetime.combine(ideal_sched[x]['Start'].date() + timedelta(days=1), time(6, 0))
            push = 0
            job_shifts = []
            occupied_shifts = []
            latest = None
            each = None
            all_skeds = []
            all_skeds.extend(ExtruderSchedule.objects.filter(ideal=True))
            all_skeds.extend(CuttingSchedule.objects.filter(ideal=True))
            all_skeds.extend(PrintingSchedule.objects.filter(ideal=True))
            all_skeds.extend(LaminatingSchedule.objects.filter(ideal=True))
            shift1.append((job, skedindate))
            if ideal_sched[x]['Task'] == 'Extrusion':
                ideal_workers = Employee.objects.filter(position='Extruder')
                other_workers = Employee.objects.filter(Q(position='Cutting') | Q(position='Printing'))
                for each in all_skeds:
                    if each.job_order_id == ideal_sched[x]['ID']:
                        job_shifts.append(each)
                job_shifts.sort(key=lambda x: x.sked_in)
                if job_shifts:
                    latest = job_shifts[-1]
                for each in all_skeds:
                    if each.sked_mach == ideal_sched[x]['Machine']:
                        occupied_shifts.append(each)
                occupied_shifts.sort(key=lambda x: x.sked_in)
                if occupied_shifts:
                    each = occupied_shifts[-1]
                if each and latest:
                    if each.sked_in.time() == time(22, 0) or latest.sked_in.time() == time(22, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0) or latest.sked_in.time() == time(14, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0) or latest.sked_in.time() == time(6, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif each:
                    if each.sked_in.time() == time(22, 0):
                        latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0):
                        latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0):
                        latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif latest:
                    if latest.sked_in.time() == time(22, 0):
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif latest.sked_in.time() == time(14, 0):
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif latest.sked_in.time() == time(6, 0):
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                if push == 1:
                    print('PUSH TO SHIFT 1: ' + str(ideal_sched[x]['ID']))
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 2:
                    print('PUSH TO SHIFT 2: ' + str(ideal_sched[x]['ID']))
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 3:
                    print('PUSH TO SHIFT 3: ' + str(ideal_sched[x]['ID']))
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                else:
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

            elif ideal_sched[x]['Task'] == 'Cutting':
                ideal_workers = Employee.objects.filter(position='Cutting')
                other_workers = Employee.objects.filter(
                    Q(position='Extruder') | Q(position='Printing') | Q(position='Laminating'))
                for each in all_skeds:
                    if each.job_order_id == ideal_sched[x]['ID']:
                        job_shifts.append(each)
                job_shifts.sort(key=lambda x: x.sked_in)
                if job_shifts:
                    latest = job_shifts[-1]
                for each in all_skeds:
                    if each.sked_mach == ideal_sched[x]['Machine']:
                        occupied_shifts.append(each)
                occupied_shifts.sort(key=lambda x: x.sked_in)
                if occupied_shifts:
                    each = occupied_shifts[-1]
                if each and latest:
                    if each.sked_in.time() == time(22, 0) or latest.sked_in.time() == time(22, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0) or latest.sked_in.time() == time(14, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0) or latest.sked_in.time() == time(6, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif each:
                    if each.sked_in.time() == time(22, 0):
                        latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0):
                        latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0):
                        latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif latest:
                    if latest.sked_in.time() == time(22, 0):
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif latest.sked_in.time() == time(14, 0):
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif latest.sked_in.time() == time(6, 0):
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                if push == 1:
                    print('PUSH TO SHIFT 1: ' + str(ideal_sched[x]['ID']))
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 2:
                    print('PUSH TO SHIFT 2: ' + str(ideal_sched[x]['ID']))
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 3:
                    print('PUSH TO SHIFT 3: ' + str(ideal_sched[x]['ID']))
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                else:
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

            elif ideal_sched[x]['Task'] == 'Printing':
                ideal_workers = Employee.objects.filter(position='Printing')
                other_workers = Employee.objects.filter(
                    Q(position='Extruder') | Q(position='Cutting') | Q(position='Laminating'))
                for each in all_skeds:
                    if each.job_order_id == ideal_sched[x]['ID']:
                        job_shifts.append(each)
                job_shifts.sort(key=lambda x: x.sked_in)
                if job_shifts:
                    latest = job_shifts[-1]
                for each in all_skeds:
                    if each.sked_mach == ideal_sched[x]['Machine']:
                        occupied_shifts.append(each)
                occupied_shifts.sort(key=lambda x: x.sked_in)
                if occupied_shifts:
                    each = occupied_shifts[-1]
                if each and latest:
                    if each.sked_in.time() == time(22, 0) or latest.sked_in.time() == time(22, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0) or latest.sked_in.time() == time(14, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0) or latest.sked_in.time() == time(6, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif each:
                    if each.sked_in.time() == time(22, 0):
                        latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0):
                        latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0):
                        latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif latest:
                    if latest.sked_in.time() == time(22, 0):
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif latest.sked_in.time() == time(14, 0):
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif latest.sked_in.time() == time(6, 0):
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                if push == 1:
                    print('PUSH TO SHIFT 1: ' + str(ideal_sched[x]['ID']))
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 2:
                    print('PUSH TO SHIFT 2: ' + str(ideal_sched[x]['ID']))
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 3:
                    print('PUSH TO SHIFT 3: ' + str(ideal_sched[x]['ID']))
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                else:
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

            elif ideal_sched[x]['Task'] == 'Laminating':
                ideal_workers = Employee.objects.filter(position='Laminating')
                other_workers = Employee.objects.filter(
                    Q(position='Extruder') | Q(position='Cutting') | Q(position='Printing'))
                for each in all_skeds:
                    if each.job_order_id == ideal_sched[x]['ID']:
                        job_shifts.append(each)
                job_shifts.sort(key=lambda x: x.sked_in)
                if job_shifts:
                    latest = job_shifts[-1]
                for each in all_skeds:
                    if each.sked_mach == ideal_sched[x]['Machine']:
                        occupied_shifts.append(each)
                occupied_shifts.sort(key=lambda x: x.sked_in)
                if occupied_shifts:
                    each = occupied_shifts[-1]
                if each and latest:
                    if each.sked_in.time() == time(22, 0) or latest.sked_in.time() == time(22, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0) or latest.sked_in.time() == time(14, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0) or latest.sked_in.time() == time(6, 0):
                        if each.sked_in > latest.sked_in:
                            latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif each:
                    if each.sked_in.time() == time(22, 0):
                        latest = each
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif each.sked_in.time() == time(14, 0):
                        latest = each
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif each.sked_in.time() == time(6, 0):
                        latest = each
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                elif latest:
                    if latest.sked_in.time() == time(22, 0):
                        push = 1
                        skedindate = latest.sked_in.date() + timedelta(days=1)
                        skedin = datetime.combine(skedindate, time(6, 0))
                        skedout = datetime.combine(skedindate, time(14, 0))
                    elif latest.sked_in.time() == time(14, 0):
                        push = 3
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(22, 0))
                        skedout = datetime.combine(skedindate, time(6, 0))
                    elif latest.sked_in.time() == time(6, 0):
                        push = 2
                        skedindate = latest.sked_in.date()
                        skedin = datetime.combine(skedindate, time(14, 0))
                        skedout = datetime.combine(skedindate, time(22, 0))
                if push == 1:
                    print('PUSH TO SHIFT 1: ' + str(ideal_sched[x]['ID']))
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 2:
                    print('PUSH TO SHIFT 2: ' + str(ideal_sched[x]['ID']))
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                elif push == 3:
                    print('PUSH TO SHIFT 3: ' + str(ideal_sched[x]['ID']))
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate, shift1, shift2, shift3, new_ideal_sched)
                else:
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout,
                                  skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

    return new_ideal_sched
