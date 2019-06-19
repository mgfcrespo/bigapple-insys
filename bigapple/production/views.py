from __future__ import print_function

import datetime, calendar
from datetime import date, datetime, time, timedelta


import pandas as pd
from django.db import connection
from django.db.models import Q, Sum
from django.shortcuts import render, redirect

from django import forms
from django.forms import ModelForm, ValidationError, Form, widgets, DateTimeInput
from inventory.forms import MaterialRequisition
from inventory.forms import MaterialRequisitionForm
from sales.models import ClientItem, SalesInvoice
from utilities import final_gantt
from utilities import cpsat, cpsatworkertest
from sales import views as sales_views
from .forms import ExtruderScheduleForm, PrintingScheduleForm, CuttingScheduleForm, LaminatingScheduleForm
from .forms import JODetailsForm
from .models import JobOrder, ExtruderSchedule, PrintingSchedule, CuttingSchedule, LaminatingSchedule
from .models import Machine
from django.contrib import messages
from accounts.models import Employee
from plotly.offline import plot
from plotly.graph_objs import Scatter

# scheduling import
# Import Python wrapper for or-tools constraint solver.

#from ortools.constraint_solver import pywrapcp


# Create your views here.
def production_details(request):
    context = {
        'title': 'Production Content'
    }

    return render(request, 'production/production_details.html', context)


def job_order_list(request):
    data = JobOrder.objects.exclude(status='Waiting').exclude(status='Ready for Delivery').exclude(status='Delivered')
    items = ClientItem.objects.filter(client_po=data)


    if request.session['session_position'] == "General Manager":
        template = 'general_manager_page_ui.html'
    elif request.session['session_position'] == "Production Manager":
        template = 'production_manager_page_ui.html'
    else:
        template = 'line_leader_page_ui.html'
    context = {
        'items': items,
        'title': 'Job Order List',
        'data' : data,
        'template' : template
    }
    return render (request, 'production/job_order_list.html', context)

def job_order_details(request, id):
		
    data = JobOrder.objects.get(id=id)
    items = ClientItem.objects.filter(client_po=data)
    quan = 0
    tity = 0
    withinmargin = False
    form = JODetailsForm(request.POST or None)
    extrusion = ExtruderSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False)).order_by('datetime_in')
    printing = PrintingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False)).order_by('datetime_in')
    cutting = CuttingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False)).order_by('datetime_in')
    laminating = LaminatingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False)).order_by('datetime_in')
    ex_done = False
    pr_done = False
    cu_done = False
    la_done = False

    for x in extrusion:
        if x.final:
            ex_done = True
            break
        else:
            ex_done = False

    for y in printing:
        if y.final:
            pr_done = True
            break
        else:
            pr_done = False

    for z in cutting:
        if z.final:
            cu_done = True
            break
        else:
            cu_done = False

    for a in laminating:
        if a.final:
            la_done = True
            break
        else:
            la_done = False

    ideal_ex = ExtruderSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=True))
    ideal_cu = CuttingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=True))
    ideal_pr = PrintingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=True))
    ideal_la = LaminatingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=True))

    if extrusion.count() > 0:
        first_ex = ExtruderSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False)).earliest('datetime_in')
    else:
        first_ex = []
    if cutting.count() > 0:
        first_cu = CuttingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False)).earliest('datetime_in')
    else:
        first_cu = []
    if printing.count() > 0:
        first_pr = PrintingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False)).earliest('datetime_in')
    else:
        first_pr = []
    if laminating.count() > 0:
        first_la = LaminatingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False)).earliest('datetime_in')
    else:
        first_la = []

    if ex_done:
        last_ex = ExtruderSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False)).latest('datetime_out')
    else:
        last_ex = []
    if cu_done:
        last_cu = CuttingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False)).latest('datetime_out')
        for x in items:
            quan = int(x.quantity * 0.1)
            tity = x.quantity
            break
        if abs(tity-last_cu.quantity) > quan:
            withinmargin = True
    else:
        last_cu = []
    if pr_done:
        last_pr = PrintingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False)).latest('datetime_out')
    else:
        last_pr = []
    if la_done:
        last_la = LaminatingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False)).latest('datetime_out')
    else:
        last_la = []

    if request.method == 'POST':
      data.remarks = request.POST.get("remarks")
      data.save()

      return redirect('production:job_order_details', id = data.id)
        
    form.fields["remarks"].initial = data.remarks

    context = {
      'form': form,
      'title' : data.job_order,
      'data': data,
      'extrusion': extrusion,
      'printing': printing,
      'cutting': cutting,
      'laminating' : laminating,
      'items' : items,
      'ideal_cu': ideal_cu,
      'ideal_pr': ideal_pr,
      'ideal_la': ideal_la,
      'ideal_ex': ideal_ex,
      'first_ex' : first_ex,
      'first_cu' : first_cu,
      'first_la' : first_la,
      'first_pr' : first_pr,
      'last_ex': last_ex,
      'last_cu': last_cu,
      'last_la': last_la,
      'last_pr': last_pr,
      'withinmargin' : withinmargin

    }
    return render(request, 'production/job_order_details.html', context)

def finished_job_order_list_view(request):
    object_list = JobOrder.objects.filter(Q(status='Ready for delivery') | Q(status='Delivered'))
    invoice = SalesInvoice.objects.all()

    for x in object_list:
        if str(x.id) in request.POST:
            x.status = "Delivered"
            x.date_delivered = date.today()
            print(x)
            x.save()

    context = {
        'object_list': object_list,
        'invoice' : invoice
    }

    return render(request, 'production/finished_job_order_list.html', context)

# EXTRUDER 
def add_extruder_schedule(request, id):

    data = JobOrder.objects.get(id=id)
    item = ClientItem.objects.get(client_po_id=id)
    e = ExtruderSchedule.objects.filter(Q(job_order_id = id) & Q(ideal=False))
    e.job_order = id
    form = ExtruderScheduleForm(request.POST)
    ideal = ExtruderSchedule.objects.filter(Q(job_order_id = id) & Q(ideal=True)).first()
    printed = False
    all_ideal = []
    if item.printed == 1:
        printed = True

    if request.method == 'POST':
        data.status = 'Under Extrusion'
        data.save()
        if form.is_valid():
            '''
            all_ideal = ExtruderSchedule.objects.filter(
                Q(ideal=True) & Q(sked_mach=Machine.objects.get(machine_id=form['machine'].value())) & ~Q(job_order_id=id))
            if all_ideal:
                for x in all_ideal:
                    xdatetimein = datetime.strptime(form['datetime_in'].value(), '%Y-%m-%d %H:%M')
                    if x.sked_in.year == xdatetimein.year \
                        and x.sked_in.month == xdatetimein.month \
                        and x.sked_in.day == xdatetimein.day \
                        and x.sked_in.hour == xdatetimein.hour:
                        print('NEW SCHED! ACTUAL MATCHES IDEAL!')
                        sales_views.save_schedule(request)
                        break
            '''

            x = request.POST.get("weight_rolls")
            y = float(x)*float(4.74)
            form = form.save(commit=False)
            form.balance = float(y)
            form.ideal = False
            new_schedule = form.save()
            if form.final:
                if printed:
                    data.status = 'Under Printing'
                    data.save()
                else:
                    data.status = 'Under Cutting'
                    data.save()
                '''
                if all_ideal:
                    for x in all_ideal:
                        xdatetimeout = datetime.strptime(form['datetime_out'].value(), '%Y-%m-%d %H:%M')
                        if x.sked_out.year == xdatetimeout.year \
                            and x.sked_out.month == xdatetimeout.month \
                            and x.sked_out.day == xdatetimeout.day \
                            and x.sked_out.hour == xdatetimeout.hour:
                            sales_views.save_schedule(request)
                            break
                '''
            else:
                data.save()
        return redirect('production:job_order_details', id = id)

    number_rolls = float(item.quantity / 10000)
    weight_rolls = number_rolls * 5
    core_weight = weight_rolls / 1.5
    output_kilos = weight_rolls

    if e:
        sum_number_rolls = float(e.aggregate(Sum('number_rolls'))['number_rolls__sum'])
        balance_number_rolls = number_rolls - sum_number_rolls
        number_rolls = balance_number_rolls
        sum_weight_rolls = float(e.aggregate(Sum('weight_rolls'))['weight_rolls__sum'])
        balance_weight_rolls = weight_rolls - sum_weight_rolls
        weight_rolls = balance_weight_rolls
        sum_core_weight = float(e.aggregate(Sum('core_weight'))['core_weight__sum'])
        balance_core_weight = core_weight - sum_core_weight
        core_weight = balance_core_weight
        sum_output_kilos = float(e.aggregate(Sum('output_kilos'))['output_kilos__sum'])
        balance_output_kilos = output_kilos - sum_output_kilos
        output_kilos = balance_output_kilos
    else:
        number_rolls = number_rolls
        weight_rolls = weight_rolls
        core_weight = core_weight
        output_kilos = weight_rolls

    if ideal is not None:
        sked_in = ideal.sked_in
        sked_out = ideal.sked_out
        sked_op = ideal.sked_op
        sked_mach = ideal.sked_mach
    else:
        sked_in = datetime.now()
        sked_out = datetime.now() + timedelta(days=int((item.quantity * 80)/70000))

    # SHIFTS: 6am-2pm, 2pm-10pm, 10pm-6am
    SHIFTS = (
        (1, 1),
        (2, 2),
        (3, 3)
    )

    if time(6,0) <= datetime.now().time() <= time(14,0):
        shift = 1
    elif time(14,0) <= datetime.now().time() <= time(22,0):
        shift = 2
    elif time(22,0) <= datetime.now().time() <= time(6,0):
        shift = 3
    else:
        shift = 0

    #TODO Add Machine and Worker initial placeholder
    form.fields["machine"].queryset = Machine.objects.filter(Q(machine_type='Extruder') & Q(state='OK'))
    form.fields["job_order"].queryset = JobOrder.objects.filter(id=id)
    form.fields["datetime_in"] = forms.DateTimeField(input_formats=['%d-%m-%Y %H:%M'], label='datetime_in', widget=forms.DateTimeInput(attrs={'value': str(sked_in)[:16]}))
    form.fields["datetime_out"] = forms.DateTimeField(input_formats=['%d-%m-%Y %H:%M'], label='datetime_out', widget=forms.DateTimeInput(attrs={'value': str(sked_out)[:16]}))
    form.fields["shift"] = forms.IntegerField(widget=forms.Select(choices=SHIFTS), initial=shift)
    form.fields["weight_rolls"] = forms.FloatField(widget=forms.NumberInput(attrs={'value': weight_rolls}))
    form.fields["core_weight"] = forms.FloatField(widget=forms.NumberInput(attrs={'value': core_weight}))
    form.fields["output_kilos"] = forms.FloatField(widget=forms.NumberInput(attrs={'value': output_kilos}))
    form.fields["number_rolls"] = forms.FloatField(widget=forms.NumberInput(attrs={'value': number_rolls}))

    context = {
      'data': data,
      'form': form,
      'id' : id,
      'sked_mach' : sked_mach
    }
    
    return render (request, 'production/add_extruder_schedule.html', context)

# PRINTING
def add_printing_schedule(request, id):
    data = JobOrder.objects.get(id=id)
    form = PrintingScheduleForm(request.POST)
    item = ClientItem.objects.get(client_po_id=id)
    ideal = PrintingSchedule.objects.filter(Q(job_order_id = id) & Q(ideal=True)).first()
    p = PrintingSchedule.objects.filter(Q(job_order_id = id) & Q(ideal=False))
    p.job_order = id
    items = ClientItem.objects.filter(client_po = id)
    laminate = False
    for x in items:
        if x.laminate == 1:
            laminate = True
            break

    if p.count == 0:
        data.status = 'Under Printing'
        data.save()
		
    print(form.errors)
    if request.method == 'POST':
      data.status = 'Under Printing'
      data.save()
      if form.is_valid():
          form = form.save(commit=False)
          form.ideal = False
          new_schedule = form.save()
          if form.final:
              if laminate:
                data.status = 'Under Laminating'
                data.save()
              else:
                data.status = 'Under Cutting'
                data.save()
      return redirect('production:job_order_details', id = data.id)

    number_rolls = float(item.quantity / 10000)
    weight_rolls = number_rolls * 5
    core_weight = weight_rolls / 1.5
    output_kilos = weight_rolls

    if p:
        sum_number_rolls = float(p.aggregate(Sum('number_rolls'))['number_rolls__sum'])
        balance_number_rolls = number_rolls - sum_number_rolls
        number_rolls = balance_number_rolls
        sum_weight_rolls = float(p.aggregate(Sum('weight_rolls'))['weight_rolls__sum'])
        balance_weight_rolls = weight_rolls - sum_weight_rolls
        weight_rolls = balance_weight_rolls
        sum_core_weight = float(p.aggregate(Sum('core_weight'))['core_weight__sum'])
        balance_core_weight = core_weight - sum_core_weight
        core_weight = balance_core_weight
        sum_output_kilos = float(p.aggregate(Sum('output_kilos'))['output_kilos__sum'])
        balance_output_kilos = output_kilos - sum_output_kilos
        output_kilos = balance_output_kilos
    else:
        number_rolls = number_rolls
        weight_rolls = weight_rolls
        core_weight = core_weight
        output_kilos = weight_rolls



    if ideal is not None:
        sked_in = ideal.sked_in
        sked_out = ideal.sked_out
    else:
        sked_in = datetime.now()
        sked_out = datetime.now() + timedelta(days=int((item.quantity * 100)/70000))

      # SHIFTS: 6am-2pm, 2pm-10pm, 10pm-6am
    SHIFTS = (
          (1, 1),
          (2, 2),
          (3, 3)
      )

    if time(6, 0) <= datetime.now().time() <= time(14, 0):
        shift = 1
    elif time(14, 0) <= datetime.now().time() <= time(22, 0):
        shift = 2
    elif time(22, 0) <= datetime.now().time() <= time(6, 0):
        shift = 3
    else:
          shift = 0

    form.fields["machine"].queryset = Machine.objects.filter(Q(machine_type='Printing') & Q(state='OK'))
    form.fields["job_order"].queryset = JobOrder.objects.filter(id=id)
    form.fields["datetime_in"] = forms.DateTimeField(input_formats=['%d-%m-%Y %H:%M'], label='datetime_in',
                                                     widget=forms.DateTimeInput(attrs={'value': str(sked_in)[:16]}))
    form.fields["datetime_out"] = forms.DateTimeField(input_formats=['%d-%m-%Y %H:%M'], label='datetime_out',
                                                      widget=forms.DateTimeInput(attrs={'value': str(sked_out)[:16]}))
    form.fields["shift"] = forms.IntegerField(widget=forms.Select(choices=SHIFTS), initial=shift)
    form.fields["weight_rolls"] = forms.FloatField(widget=forms.NumberInput(attrs={'value': weight_rolls}))
    form.fields["core_weight"] = forms.FloatField(widget=forms.NumberInput(attrs={'value': core_weight}))
    form.fields["output_kilos"] = forms.FloatField(widget=forms.NumberInput(attrs={'value': output_kilos}))
    form.fields["number_rolls"] = forms.FloatField(widget=forms.NumberInput(attrs={'value': number_rolls}))

    context = {
      'data': data,
      'form': form,
        'id': id
    }
    
    return render (request, 'production/add_printing_schedule.html', context)

# CUTTING
def add_cutting_schedule(request, id):
    data = JobOrder.objects.get(id=id)
    item = ClientItem.objects.get(client_po_id=id)
    form = CuttingScheduleForm(request.POST)
    invoice = SalesInvoice.objects.get(client_po = data)
    client = data.client
    ideal = CuttingSchedule.objects.filter(Q(job_order_id=id) & Q(ideal=True)).first()

    c = CuttingSchedule.objects.filter(Q(job_order_id = id) & Q(ideal=False))
    c.job_order = id

    if c.count == 0:
        data.status = 'Under Cutting'
        data.save()
		
    print(form.errors)
    if request.method == 'POST':
      data.status = 'Under Cutting'
      data.save()
      if form.is_valid():
        form = form.save(commit=False)
        form.ideal = False
        new_schedule = form.save()
        if form.final:
            data.status = 'Ready for delivery'
            data.save()
            invoice.date_issued = date.today()
            invoice.date_due = invoice.calculate_date_due()
            invoice.total_paid = 0
            invoice.save()

            client.outstanding_balance += invoice.total_amount_computed
            client.save()
        return redirect('production:job_order_details', id = data.id)

    number_rolls = float(item.quantity / 10000)
    output_kilos = number_rolls * 5
    quantity = item.quantity

    if c:
        sum_number_rolls = float(c.aggregate(Sum('number_rolls'))['number_rolls__sum'])
        balance_number_rolls = number_rolls - sum_number_rolls
        number_rolls = balance_number_rolls
        sum_output_kilos = float(c.aggregate(Sum('output_kilos'))['output_kilos__sum'])
        balance_output_kilos = output_kilos - sum_output_kilos
        output_kilos = balance_output_kilos
        sum_quantity = float(c.aggregate(Sum('quantity'))['quantity__sum'])
        balance_quantity = quantity - sum_quantity
        quantity = balance_quantity

    else:
        number_rolls = number_rolls
        output_kilos = output_kilos
        quantity = quantity


    if ideal is not None:
        sked_in = ideal.sked_in
        sked_out = ideal.sked_out
    else:
        sked_in = datetime.now()
        sked_out = datetime.now() + timedelta(days=int((quantity * 60)/70000))

    SHIFTS = (
        (1, 1),
        (2, 2),
        (3, 3)
    )

    if time(6,0) <= datetime.now().time() <= time(14,0):
        shift = 1
    elif time(14,0) <= datetime.now().time() <= time(22,0):
        shift = 2
    elif time(22,0) <= datetime.now().time() <= time(6,0):
        shift = 3
    else:
        shift = 0

    form.fields["machine"].queryset = Machine.objects.filter(Q(machine_type='Cutting') & Q(state='OK'))
    form.fields["job_order"].queryset = JobOrder.objects.filter(id=id)
    form.fields["datetime_in"] = forms.DateTimeField(input_formats=['%d-%m-%Y %H:%M'], label='datetime_in',
                                                     widget=forms.DateTimeInput(
                                                         attrs={'value': str(sked_in)[:16]}))
    form.fields["datetime_out"] = forms.DateTimeField(input_formats=['%d-%m-%Y %H:%M'], label='datetime_out',
                                                      widget=forms.DateTimeInput(
                                                          attrs={'value': str(sked_out)[:16]}))
    form.fields["shift"] = forms.IntegerField(widget=forms.Select(choices=SHIFTS), initial=shift)
    form.fields["quantity"] = forms.FloatField(widget=forms.NumberInput(attrs={'value': quantity}))
    form.fields["output_kilos"] = forms.FloatField(widget=forms.NumberInput(attrs={'value': output_kilos}))
    form.fields["number_rolls"] = forms.FloatField(widget=forms.NumberInput(attrs={'value': number_rolls}))

    context = {
      'data': data,
      'form': form,
        'id' : id
    }
    
    return render (request, 'production/add_cutting_schedule.html', context)


def add_laminating_schedule(request, id):
    data = JobOrder.objects.get(id=id)
    form = LaminatingScheduleForm(request.POST)
    l = LaminatingSchedule.objects.filter(Q(job_order_id = id) & Q(ideal=False))
    item = ClientItem.objects.get(client_po_id=id)
    ideal = LaminatingSchedule.objects.filter(Q(job_order_id=id) & Q(ideal=True)).first()
    l.job_order = id

    if l.count == 0:
        data.status = 'Under Laminating'
        data.save()

    print(form.errors)
    if request.method == 'POST':
        data.status = 'Under Laminating'
        data.save()
        if form.is_valid():
            form = form.save(commit=False)
            form.ideal = False
            new_schedule = form.save()
            if form.final:
                data.status = 'Under Cutting'
                data.save()
        return redirect('production:job_order_details', id=data.id)

    quantity = item.quantity

    if ideal is not None:
        sked_in = ideal.sked_in
        sked_out = ideal.sked_out
    else:
        sked_in = datetime.now()
        sked_out = datetime.now() + timedelta(days=int((quantity * 60)/70000))

    SHIFTS = (
        (1, 1),
        (2, 2),
        (3, 3)
    )

    if time(6, 0) <= datetime.now().time() <= time(14, 0):
        shift = 1
    elif time(14, 0) <= datetime.now().time() <= time(22, 0):
        shift = 2
    elif time(22, 0) <= datetime.now().time() <= time(6, 0):
        shift = 3
    else:
        shift = 0

    form.fields["machine"].queryset = Machine.objects.filter(Q(machine_type='Laminating') & Q(state='OK'))
    form.fields["job_order"].queryset = JobOrder.objects.filter(id=id)
    form.fields["datetime_in"] = forms.DateTimeField(input_formats=['%d-%m-%Y %H:%M'], label='datetime_in',
                                                         widget=forms.DateTimeInput(
                                                             attrs={'value': str(sked_in)[:16]}))
    form.fields["datetime_out"] = forms.DateTimeField(input_formats=['%d-%m-%Y %H:%M'], label='datetime_out',
                                                          widget=forms.DateTimeInput(
                                                              attrs={'value': str(sked_out)[:16]}))
    form.fields["shift"] = forms.IntegerField(widget=forms.Select(choices=SHIFTS), initial=shift)
    form.fields["quantity"] = forms.FloatField(widget=forms.NumberInput(attrs={'value': quantity}))

    context = {
        'data': data,
        'form': form,
        'id' : id
    }

    return render(request, 'production/add_laminating_schedule.html', context)
# JO approval 
def jo_approval(request, id):

    jo_id = JobOrder.objects.get(id=id)
    client_po = JobOrder.objects.get(id = jo_id.client_po.id)
    client_po.status = 'Approved'
    client_po.save()
    jo_id.status = "On Queue"
    jo_id.save()

    client_items = ClientItem.objects.filter(client_po = jo_id.client_po.id)
    
    #forms
    form = MaterialRequisitionForm

    print("JO:" ,jo_id)
    print("Client PO:" ,jo_id.client_po.id)

    #variables
    HDPE = 0
    PP = 0
    PET = 0
    LDPE = 0
    LLDPE = 0
    
    for data in client_items:
        print(data.material_type, data.quantity)

        if data.products.material_type == "HDPE":
            #rm for HDPE ratio 3:2:1
            q = data.quantity
            x = (q/100)/6
            HDPE+= x*3
            PP+= x*2  
            PET+= x*1

        elif data.products.material_type == "PP":
            q = data.quantity
            x= (q/100)/6
            PP+= x*3
            PET+= x*2  
            HDPE+= x*1

        elif data.products.material_type == "LDPE":
            q = data.quantity
            x= (q/100)/6
            LDPE+= x*3
            LLDPE+= x*2  
            HDPE+= x*1

    print(LDPE, HDPE, PP, PET, LLDPE)

    MaterialRequisition.objects.create(jo = jo_id)
    mr_id = MaterialRequisition.objects.last() 


    if LDPE != 0:
        MaterialRequisition.objects.create(matreq = mr_id, item = "LDPE", quantity = LDPE)
    if HDPE != 0:
        MaterialRequisition.objects.create(matreq = mr_id, item = "HDPE", quantity = HDPE)
    if PP != 0:
        MaterialRequisition.objects.create(matreq = mr_id, item = "PP", quantity = PP)
    if PET != 0:
        MaterialRequisition.objects.create(matreq = mr_id, item = "PET", quantity = PET)
    if LLDPE != 0:
        MaterialRequisition.objects.create(matreq = mr_id, item = "LLDPE", quantity = LLDPE)

    return redirect('production:job_order_details', id = jo_id.id)

#SCHEDULING
def production_schedule(request):

    plot_list = []
    machines = Machine.objects.all()

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
                             'Worker' : i.sked_op
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

        machines_in_production = []
        all_machines = Machine.objects.filter(state='OK')

        for q in range(len(plot_list)):
            machines_in_production.append(plot_list[q]['Machine'])

            #Machine breakdown.
            is_it_ok = plot_list[q]['Machine']

            if is_it_ok.state == 'OK':
                pass
            else:
                plot_list = sales_views.save_schedule(request)
                break

        # Machine recently deployed.
        yung_wala = set(all_machines).difference(machines_in_production)
        if yung_wala:
            plot_list = sales_views.save_schedule(request)
        else:
            pass

        '''
        #All machines of machine_type breakdown.
        em_count = 0
        cm_count = 0
        pm_count = 0
        lm_count = 0
        em_none = False
        cm_none = False
        pm_none = False
        lm_none = False
        extruders = Machine.objects.filter(machine_type='Extruder')
        cutters = Machine.objects.filter(machine_type='Cutting')
        printers = Machine.objects.filter(machine_type='Printing')
        laminators = Machine.objects.filter(machine_type='Laminating')
        for e in extruders:
            if e.state == 'OK':
                em_count += 1
        if em_count == 0:
            em_none = True
        for c in cutters:
            if c.state == 'OK':
                cm_count += 1
        if cm_count == 0:
            cm_none = True
        for p in printers:
            if p.state == 'OK':
                pm_count += 1
        if pm_count == 0:
            pm_none = True
        for l in laminators:
            if l.state == 'OK':
                lm_count += 1
        if lm_count == 0:
            lm_none = True

        if em_none:
            plot_list = None
        
        '''
    else:
        plot_list = sales_views.save_schedule(request)

    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=7)
    start_month = today.replace(day=1)
    week = []
    month = []
    for i in range(0,7):
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


    context = {
        'plot_list': plot_list,
        'machines' : machines,
        'this_week' : this_week,
        'this_month' : this_month,
        'week' : week,
        'month' : month,
        'today' : today
    }

    return render(request, 'production/production_schedule.html', context)

def extruder_machine_schedule(request):
    plot_list = []
    ex = []
    for x in ExtruderSchedule.objects.filter(ideal=True):
        job = x.job_order
        if job.status == 'Ready for delivery' or job.status == 'Delivered':
            pass
        else:
            ex.append(x)

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
                     'Worker' : i.sked_op
                         }
        plot_list.append(sked_dict)

    machines = Machine.objects.filter(machine_type='Extruder')
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

    context = {
        'plot_list': plot_list,
        'machines': machines,
        'this_week': this_week,
        'this_month': this_month,
        'week': week,
        'month': month,
        'today': today
    }

    return render(request, 'production/extruder_machine_schedule.html', context)

def printing_machine_schedule(request):
    plot_list = []
    pr = []
    for x in PrintingSchedule.objects.filter(ideal=True):
        job = x.job_order
        if job.status == 'Ready for delivery' or job.status == 'Delivered':
            pass
        else:
            pr.append(x)

    for i in pr:
        job = i.job_order_id
        item = ClientItem.objects.get(client_po_id=job)
        product = item.products
        mat = product.material_type

        sked_dict = {'ID': job,
                     'Task': 'Printing',
                     'Start': i.sked_in,
                     'Finish': i.sked_out,
                     'Resource': mat,
                     'Machine': i.sked_mach,
                     'Worker' : i.sked_op
                         }
        plot_list.append(sked_dict)

    machines = Machine.objects.filter(machine_type='Printing')
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

    context = {
        'plot_list': plot_list,
        'machines': machines,
        'this_week': this_week,
        'this_month': this_month,
        'week': week,
        'month': month,
        'today': today
    }

    return render(request, 'production/printing_machine_schedule.html', context)

def laminating_machine_schedule(request):
    plot_list = []
    la = []
    for x in LaminatingSchedule.objects.filter(ideal=True):
        job = x.job_order
        if job.status == 'Ready for delivery' or job.status == 'Delivered':
            pass
        else:
            la.append(x)

    for i in la:
        job = i.job_order_id
        item = ClientItem.objects.get(client_po_id=job)
        product = item.products
        mat = product.material_type

        sked_dict = {'ID': job,
                     'Task': 'Laminating',
                     'Start': i.sked_in,
                     'Finish': i.sked_out,
                     'Resource': mat,
                     'Machine': i.sked_mach,
                     'Worker' : i.sked_op
                         }
        plot_list.append(sked_dict)

    machines = Machine.objects.filter(machine_type='Laminating')
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

    context = {
        'plot_list': plot_list,
        'machines': machines,
        'this_week': this_week,
        'this_month': this_month,
        'week': week,
        'month': month,
        'today': today
    }

    return render(request, 'production/laminating_machine_schedule.html', context)

def cutting_machine_schedule(request):
    plot_list = []
    cu = []
    for x in CuttingSchedule.objects.filter(ideal=True):
        job = x.job_order
        if job.status == 'Ready for delivery' or job.status == 'Delivered':
            pass
        else:
            cu.append(x)

    for i in cu:
        job = i.job_order_id
        item = ClientItem.objects.get(client_po_id=job)
        product = item.products
        mat = product.material_type

        sked_dict = {'ID': job,
                     'Task': 'Cutting',
                     'Start': i.sked_in,
                     'Finish': i.sked_out,
                     'Resource': mat,
                     'Machine': i.sked_mach,
                     'Worker' : i.sked_op
                         }
        plot_list.append(sked_dict)

    machines = Machine.objects.filter(machine_type='Cutting')
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

    context = {
        'plot_list': plot_list,
        'machines': machines,
        'this_week': this_week,
        'this_month': this_month,
        'week': week,
        'month': month,
        'today': today
    }


    return render(request, 'production/cutting_machine_schedule.html', context)

def production_report(request):
    jo = JobOrder.objects.filter(~Q(status='Waiting') | ~Q(status='Ready for delivery') | ~Q(status='Delivered'))
    item = ClientItem.objects.all()
    ideal_ex = ExtruderSchedule.objects.filter(ideal=True)
    ideal_cu = CuttingSchedule.objects.filter(ideal=True)
    ideal_pr = PrintingSchedule.objects.filter(ideal=True)
    ideal_la = LaminatingSchedule.objects.filter(ideal=True)
    real_ex = ExtruderSchedule.objects.filter(ideal=False)
    real_cu = CuttingSchedule.objects.filter(ideal=False)
    real_pr = PrintingSchedule.objects.filter(ideal=False)
    real_la = LaminatingSchedule.objects.filter(ideal=False)

    context = {
        'jo' : jo,
        'ideal_cu': ideal_cu,
        'ideal_pr': ideal_pr,
        'ideal_la': ideal_la,
        'ideal_ex' : ideal_ex,
        'real_ex' : real_ex,
        'real_cu' : real_cu,
        'real_pr' : real_pr,
        'real_la' : real_la,
        'item' : item,
    }

    return render(request, 'production/production_report.html', context)

def shift_schedule(request):
    ex_schedule = []
    cu_schedule = []
    pr_schedule = []
    la_schedule = []
    start_time = None
    end_time = None
    today = date.today()
    e = ExtruderSchedule.objects.all()
    c = CuttingSchedule.objects.all()
    l = LaminatingSchedule.objects.all()
    p = PrintingSchedule.objects.all()

    if time(6, 0) <= datetime.now().time() <= time(14, 0):
        shift = 1
        for i in e:
            sked_in = i.sked_in
            if sked_in:
                if sked_in.year == today.year and sked_in.month == today.month and sked_in.day == today.day and sked_in.hour >= 6 and sked_in.hour <= 14:
                    ex_schedule.append(i)
        for j in c:
            sked_in = j.sked_in
            if sked_in:
                if sked_in.year == today.year and sked_in.month == today.month and sked_in.day == today.day and sked_in.hour >= 6 and sked_in.hour <= 14:
                    cu_schedule.append(j)
        for k in l:
            sked_in = k.sked_in
            if sked_in:
                if sked_in.year == today.year and sked_in.month == today.month and sked_in.day == today.day and sked_in.hour >= 6 and sked_in.hour <= 14:
                    la_schedule.append(k)
        for x in p:
            sked_in = x.sked_in
            if sked_in:
                if sked_in.year == today.year and sked_in.month == today.month and sked_in.day == today.day and sked_in.hour >= 6 and sked_in.hour <= 14:
                    pr_schedule.append(x)


    elif time(14, 0) <= datetime.now().time() <= time(22,0):
        shift = 2

        for i in e:
            sked_in = i.sked_in
            if sked_in:
                if sked_in.year == today.year and sked_in.month == today.month and sked_in.day == today.day and sked_in.hour >= 14 and sked_in.hour <= 22:
                    ex_schedule.append(i)
        for j in c:
            sked_in = j.sked_in
            if sked_in:
                if sked_in.year == today.year and sked_in.month == today.month and sked_in.day == today.day and sked_in.hour >= 14 and sked_in.hour <= 22:
                    cu_schedule.append(j)
        for k in l:
            sked_in = k.sked_in
            if sked_in:
                if sked_in.year == today.year and sked_in.month == today.month and sked_in.day == today.day and sked_in.hour >= 14 and sked_in.hour <= 22:
                    la_schedule.append(k)
        for x in p:
            sked_in = x.sked_in
            if sked_in:
                if sked_in.year == today.year and sked_in.month == today.month and sked_in.day == today.day and sked_in.hour >= 14 and sked_in.hour <= 122:
                    pr_schedule.append(x)

    elif datetime.now().time() >= time(22, 0):
        shift = 3
        for i in e:
            sked_in = i.sked_in
            if sked_in:
                if sked_in.year == today.year and sked_in.month == today.month and sked_in.day == today.day and sked_in.hour >= 22 and sked_in.hour <= 6:
                    ex_schedule.append(i)
        for j in c:
            sked_in = j.sked_in
            if sked_in:
                if sked_in.year == today.year and sked_in.month == today.month and sked_in.day == today.day and sked_in.hour >= 22 and sked_in.hour <= 6:
                    cu_schedule.append(j)
        for k in l:
            sked_in = k.sked_in
            if sked_in:
                if sked_in.year == today.year and sked_in.month == today.month and sked_in.day == today.day and sked_in.hour >= 22 and sked_in.hour <= 6:
                    la_schedule.append(k)
        for x in p:
            sked_in = x.sked_in
            if sked_in:
                if sked_in.year == today.year and sked_in.month == today.month and sked_in.day == today.day and sked_in.hour >= 22 and sked_in.hour <= 6:
                    pr_schedule.append(x)
    elif datetime.now().time() <= time(6, 0):
        shift = 3
        for i in e:
            sked_in = i.sked_in
            if sked_in:
                if sked_in.year == today.year and sked_in.month == today.month and sked_in.day == today.day and sked_in.hour >= 22 and sked_in.hour <= 6:
                    ex_schedule.append(i)
        for j in c:
            sked_in = j.sked_in
            if sked_in:
                if sked_in.year == today.year and sked_in.month == today.month and sked_in.day == today.day and sked_in.hour >= 22 and sked_in.hour <= 6:
                    cu_schedule.append(j)
        for k in l:
            sked_in = k.sked_in
            if sked_in:
                if sked_in.year == today.year and sked_in.month == today.month and sked_in.day == today.day and sked_in.hour >= 22 and sked_in.hour <= 6:
                    la_schedule.append(k)
        for x in p:
            sked_in = x.sked_in
            if sked_in:
                if sked_in.year == today.year and sked_in.month == today.month and sked_in.day == today.day and sked_in.hour >= 22 and sked_in.hour <= 6:
                    pr_schedule.append(x)
    else:
        shift = 0


    print('SHIFT SKED')
    print(shift)
    print(ex_schedule)

    now = datetime.now()

    context = {
        'ex_schedule' : ex_schedule,
        'cu_schedule' : cu_schedule,
        'la_schedule' : la_schedule,
        'pr_schedule' : pr_schedule,
        'shift' : shift,
        'now' : now

    }
    return render(request, 'production/shift_schedule.html', context)

def sched_test(request):
    cursor = connection.cursor()
    query = "SELECT j.id, i.laminate, i.printed, p.material_type FROM production_mgt_joborder j, sales_mgt_clientitem i, sales_mgt_product p " \
            "WHERE p.id = i.products_id and i.client_po_id = j.id and " \
            "NOT j.status=" + "'Waiting'" + " and NOT j.status=" + "'Ready for delivery'" + " and NOT j.status =" + "'Delivered'"
    cursor.execute(query)
    df = pd.read_sql(query, connection)


    plot_list = cpsatworkertest.flexible_jobshop(df)

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

    for i in range(len(plot_list)):
        if start_week <= plot_list[i]['Start'].date() <= end_week:
            this_week.append(plot_list[i])
        if plot_list[i]['Start'].month == today.month:
            this_month.append(plot_list[i])

    context = {

        'machines': machines,
        'this_week': this_week,
        'this_month': this_month,
        'week': week,
        'month': month,
        'today': today


    }

    return render(request, 'production/sched_test.html', context)