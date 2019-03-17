from __future__ import print_function

from datetime import date, datetime, time, timedelta

import pandas as pd
from django.db import connection
from django.db.models import Q
from django.shortcuts import render, redirect

from django import forms
from django.forms import ModelForm, ValidationError, Form, widgets, DateTimeInput
from inventory.forms import MaterialRequisition
from inventory.forms import MaterialRequisitionForm
from sales.models import ClientItem, SalesInvoice
from utilities import final_gantt
from .forms import ExtruderScheduleForm, PrintingScheduleForm, CuttingScheduleForm, LaminatingScheduleForm
from .forms import JODetailsForm
from .models import JobOrder, ExtruderSchedule, PrintingSchedule, CuttingSchedule, LaminatingSchedule
from .models import Machine
from django.contrib import messages
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
    form = JODetailsForm(request.POST or None)
    extrusion = ExtruderSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False)).order_by('datetime_in')
    printing = PrintingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False)).order_by('datetime_in')
    cutting = CuttingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False)).order_by('datetime_in')
    laminating = LaminatingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False)).order_by('datetime_in')

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
      'items' : items
    }
    return render(request, 'production/job_order_details.html', context)

def finished_job_order_list_view(request):
    object_list = JobOrder.objects.filter(Q(status='Ready for delivery') | Q(status='Delivered'))
    invoice = SalesInvoice.objects.all()

    for x in object_list:
        if request.method == "POST":
            x.status = "Delivered"
            x.date_delivered = date.today()
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
    e = ExtruderSchedule.objects.filter(job_order_id = id)
    e.job_order = id
    form = ExtruderScheduleForm(request.POST)
    ideal = ExtruderSchedule.objects.filter(Q(job_order_id = id) & Q(ideal=True)).first() #TODO Sinsinin
    printed = False
    if item.printed == 1:
        printed == True

    #if e.count == 0:
    #    ideal = ExtruderSchedule.objects.filter(Q(job_order_id = id) & Q(ideal=True)).first() #TODO kung di siya first

    if request.method == 'POST':
        data.status = 'Under Extrusion'
        data.save()
        if form.is_valid():
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
            else:
                data.save()
        return redirect('production:job_order_details', id = id)

    #TODO quantity calculations/balance
    #if e.count == 0:
    number_rolls = float(item.quantity/10000)
    weight_rolls = number_rolls*5
    core_weight = weight_rolls/1.5
    output_kilos = weight_rolls
    '''
    else:
        number_rolls = float(item.quantity / 10000)
        weight_rolls = number_rolls * 5
        core_weight = weight_rolls / 1.5
        output_kilos = weight_rolls
    '''

    if ideal is not None:
        sked_in = ideal.sked_in
        sked_out = ideal.sked_out
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

    form.fields["machine"].queryset = Machine.objects.filter(machine_type='Extruder')
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
      'id' : id
    }
    
    return render (request, 'production/add_extruder_schedule.html', context)

# PRINTING
def add_printing_schedule(request, id):
		
    data = JobOrder.objects.get(id=id)
    form = PrintingScheduleForm(request.POST)
    item = ClientItem.objects.get(client_po_id=id)
    ideal = PrintingSchedule.objects.filter(Q(job_order_id = id) & Q(ideal=True)).first() #TODO Sinsinin
    p = PrintingSchedule.objects.filter(job_order_id = data.id)
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

      # TODO quantity calculations/balance
      number_rolls = float(item.quantity / 10000)
      weight_rolls = number_rolls * 5
      core_weight = weight_rolls / 1.5
      output_kilos = weight_rolls

      if ideal is not None:
          sked_in = ideal.sked_in
          sked_out = ideal.sked_out
      else:
          sked_in = datetime.now()
          sked_out = datetime.now() + timedelta(days=int((quantity * 100)/70000))

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

    form.fields["machine"].queryset = Machine.objects.filter(machine_type='Printing')
    form.fields["job_order"].queryset = JobOrder.objects.filter(id=id)
    form.fields["datetime_in"] = forms.DateTimeField(input_formats=['%d-%m-%Y %H:%M'], label='datetime_in',
                                                     widget=forms.DateTimeInput(
                                                         attrs={'value': str(sked_in)[:16]}))
    form.fields["datetime_out"] = forms.DateTimeField(input_formats=['%d-%m-%Y %H:%M'], label='datetime_out',
                                                      widget=forms.DateTimeInput(
                                                          attrs={'value': str(sked_out)[:16]}))
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
    ideal = CuttingSchedule.objects.filter(Q(job_order_id=id) & Q(ideal=True)).first()  # TODO Sinsinin

    c = CuttingSchedule.objects.filter(job_order_id = data.id)
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

    # TODO quantity calculations/balance
    number_rolls = float(item.quantity / 10000)
    output_kilos = number_rolls * 5
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

    if time(6,0) <= datetime.now().time() <= time(14,0):
        shift = 1
    elif time(14,0) <= datetime.now().time() <= time(22,0):
        shift = 2
    elif time(22,0) <= datetime.now().time() <= time(6,0):
        shift = 3
    else:
        shift = 0

    form.fields["machine"].queryset = Machine.objects.filter(machine_type='Cutting')
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
    l = LaminatingSchedule.objects.filter(job_order_id=data.id)
    item = ClientItem.objects.get(client_po_id=id)
    ideal = LaminatingSchedule.objects.filter(Q(job_order_id=id) & Q(ideal=True)).first()  # TODO Sinsinin
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

    form.fields["machine"].queryset = Machine.objects.filter(machine_type='Laminating')
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
    ideal = []
    ex = ExtruderSchedule.objects.filter(ideal=True)
    ex_list = list(ex)
    ideal.append(ex_list)
    cu = CuttingSchedule.objects.filter(ideal=True)
    cu_list = list(cu)
    ideal.append(cu_list)
    pr = PrintingSchedule.objects.filter(ideal=True)
    pr_list = list(pr)
    ideal.append(pr_list)
    la = LaminatingSchedule.objects.filter(ideal=True)
    la_list = list(la)
    print('la list:')
    print(la_list)
    ideal.append(la_list)

    if ideal:
        if ex.exists():
            for i in ex:
                job = i.job_order_id
                item = ClientItem.objects.get(client_po_id=job)
                product = item.products
                mat = product.material_type

                sked_dict = {'Task': 'Extruder',
                             'Start': str(i.sked_in),
                             'Finish': str(i.sked_out),
                             'Resource': i.job_order_id,
                             'Description': mat
                             }
                plot_list.append(sked_dict)

        if cu.exists():
            for j in cu:
                job = j.job_order_id
                item = ClientItem.objects.get(client_po_id=job)
                product = item.products
                mat = product.material_type

                sked_dict = {'Task': 'Cutting',
                             'Start': str(j.sked_in),
                             'Finish': str(j.sked_out),
                             'Resource': j.job_order_id,
                             'Description': mat
                             }
                plot_list.append(sked_dict)
        if pr.exists():
            for k in pr:
                job = k.job_order_id
                item = ClientItem.objects.get(client_po_id=job)
                product = item.products
                mat = product.material_type

                sked_dict = {'Task': 'Printing',
                             'Start': str(k.sked_in),
                             'Finish': str(k.sked_out),
                             'Resource': k.job_order_id,
                             'Description': mat
                             }
                plot_list.append(sked_dict)
        if la.exists():
            for l in la:
                job = l.job_order_id
                item = ClientItem.objects.get(client_po_id=job)
                product = item.products
                mat = product.material_type

                sked_dict = {'Task': 'Laminating',
                             'Start': str(l.sked_in),
                             'Finish': str(l.sked_out),
                             'Resource': l.job_order_id,
                             'Description': mat
                             }
                plot_list.append(sked_dict)

        print('plot_list:')
        print(plot_list)
        df1 = pd.DataFrame(plot_list)
        print('df1:')
        print(df1)
        gantt = final_gantt.chart(df1, '/production_schedule.html')

    else:
        cursor = connection.cursor()
        query = "SELECT j.id, i.laminate, i.printed, p.material_type FROM production_mgt_joborder j, sales_mgt_clientitem i, sales_mgt_product p WHERE p.id = i.products_id and i.client_po_id = j.id and NOT j.status="+"'Waiting'"+" and NOT j.status="+"'Ready for delivery'"+" and NOT j.status ="+"'Delivered'"
        cursor.execute(query)
        df = pd.read_sql(query, connection)
        gantt = final_gantt.generate_overview_gantt_chart(df)


        #TODO Save sked_op, sked_mach
        if 'save_btn' in request.POST:
            ideal_sched = final_gantt.get_sched_data(df)
            messages.success(request, 'Production schedule saved.')
            print('ideal sched:')
            print(ideal_sched)

            for i in range(0, len(ideal_sched)):
                if ideal_sched[i]['Task'] == 'Extruder':
                   new_ex = ExtruderSchedule(job_order_id=ideal_sched[i]['Resource'], ideal=True, sked_in=ideal_sched[i]['Start'],
                                             sked_out=ideal_sched[i]['Finish'])
                   new_ex.save()
                   print('saved new_ex')
                elif ideal_sched[i]['Task'] == 'Cutting':
                    new_cu = CuttingSchedule(job_order_id=ideal_sched[i]['Resource'], ideal=True,
                                              sked_in=ideal_sched[i]['Start'],
                                              sked_out=ideal_sched[i]['Finish'])
                    new_cu.save()
                    print('saved new_cu')
                elif ideal_sched[i]['Task'] == 'Printing':
                    new_pr = PrintingSchedule(job_order_id=ideal_sched[i]['Resource'], ideal=True,
                                              sked_in=ideal_sched[i]['Start'],
                                              sked_out=ideal_sched[i]['Finish'])
                    new_pr.save()
                    print('saved new_pr')
                elif ideal_sched[i]['Task'] == 'Laminating':
                    new_la = LaminatingSchedule(job_order_id=ideal_sched[i]['Resource'], ideal=True,
                                              sked_in=ideal_sched[i]['Start'],
                                              sked_out=ideal_sched[i]['Finish'])
                    new_la.save()
                    print('saved new_la')


    context = {
        'final_gantt': gantt
    }

    return render(request, 'production/production_schedule.html', context)

def extruder_machine_schedule(request):
    plot_list = []
    ex = ExtruderSchedule.objects.filter(ideal=True)

    if ex.exists():
        for i in ex:
            job = i.job_order_id
            item = ClientItem.objects.get(client_po_id=job)
            product = item.products
            mat = product.material_type

            sked_dict = {'Task': 'Extruder',
                             'Start': str(i.sked_in),
                             'Finish': str(i.sked_out),
                             'Resource': i.job_order_id,
                             'Description': mat
                             }
            plot_list.append(sked_dict)

        #print('plot_list:')
        #print(plot_list)
        df1 = pd.DataFrame(plot_list)

    machines = Machine.objects.filter(machine_type='Extruder').values('machine_id')

    extruder_gantt = final_gantt.chart(df1, '/extruder-machine-schedule.html')

    context = {
        'extruder_gantt': extruder_gantt
    }

    return render(request, 'production/extruder_machine_schedule.html', context)

def printing_machine_schedule(request):
    plot_list = []
    pr = PrintingSchedule.objects.filter(ideal=True)

    if pr.exists():
        for i in pr:
            job = i.job_order_id
            item = ClientItem.objects.get(client_po_id=job)
            product = item.products
            mat = product.material_type

            sked_dict = {'Task': 'Extruder',
                         'Start': str(i.sked_in),
                         'Finish': str(i.sked_out),
                         'Resource': i.job_order_id,
                         'Description': mat
                         }
            plot_list.append(sked_dict)

        # print('plot_list:')
        # print(plot_list)
        df1 = pd.DataFrame(plot_list)
    printing_gantt = final_gantt.chart(df1, '/printing-machine-schedule.html')

    context = {
        'printing_gantt': printing_gantt
    }

    return render(request, 'production/printing_machine_schedule.html', context)

def laminating_machine_schedule(request):
    cursor = connection.cursor()
    query = "SELECT j.id, i.laminate, i.printed, p.material_type FROM production_mgt_joborder j, sales_mgt_clientitem i, sales_mgt_product p WHERE p.id = i.products_id and i.client_po_id = j.id and NOT j.status="+"'Waiting'"+" and NOT j.status="+"'Ready for delivery'"+" and NOT j.status ="+"'Delivered'"
    cursor.execute(query)
    df = pd.read_sql(query, connection)
    machines = Machine.objects.filter(machine_type='Laminating').values('machine_id')

    laminating_gantt = final_gantt.generate_specific_gantt_chart(df, machines, machine_type='Laminating')

    context = {
        'laminating_gantt': laminating_gantt
    }

    return render(request, 'production/laminating_machine_schedule.html', context)

def cutting_machine_schedule(request):
    cursor = connection.cursor()
    query = "SELECT j.id, i.laminate, i.printed, p.material_type FROM production_mgt_joborder j, sales_mgt_clientitem i, sales_mgt_product p WHERE p.id = i.products_id and i.client_po_id = j.id and NOT j.status="+"'Waiting'"+" and NOT j.status="+"'Ready for delivery'"+" and NOT j.status ="+"'Delivered'"
    cursor.execute(query)
    df = pd.read_sql(query, connection)
    machines = Machine.objects.filter(machine_type='Cutting').values('machine_id')

    cutting_gantt = final_gantt.generate_specific_gantt_chart(df, machines, machine_type='Cutting')

    context = {
        'cutting_gantt': cutting_gantt
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
