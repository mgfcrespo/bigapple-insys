from __future__ import print_function

import random
import datetime, calendar
from datetime import date, datetime, time, timedelta
from django.utils import timezone
import pytz
#import bigapple.utils

import pandas as pd
import math
from django.db import connection
from django.db.models import Q, Sum
from django.shortcuts import render, redirect

from django import forms
from django.forms import ModelForm, ValidationError, Form, widgets, DateTimeInput
from inventory.forms import MaterialRequisition
from inventory.forms import MaterialRequisitionForm
from sales.models import ClientItem, SalesInvoice, Product
from utilities import cpsat, cpsatworkertest
from sales import views as sales_views
from .forms import ExtruderScheduleForm, PrintingScheduleForm, CuttingScheduleForm, LaminatingScheduleForm
from .forms import JODetailsForm
from .models import JobOrder, ExtruderSchedule, PrintingSchedule, CuttingSchedule, LaminatingSchedule
from .models import Machine
from django.contrib import messages
from accounts.models import Employee
from django.http import HttpResponse
from django.views.generic import View
from utilities import shift_scheduling_sat

# Create your views here.
def production_details(request):
    context = {
        'title': 'Production Content'
    }

    return render(request, 'production/production_details.html', context)


def job_order_list(request):
    datas = JobOrder.objects.exclude(status='Waiting').exclude(status='Ready for Delivery').exclude(status='Delivered')
    items = []
    today = date.today()
    start_week = today - timedelta(today.weekday())
    end_week = start_week + timedelta(7)
    for every in ClientItem.objects.all():
        for a in datas:
            if every.client_po_id == a.id:
                items.append(every)
    ex_schedule = []
    cu_schedule = []
    pr_schedule = []
    la_schedule = []
    ex_late = 0
    cu_late = 0
    la_late = 0
    pr_late = 0

    e = ExtruderSchedule.objects.filter(ideal=True)
    c = CuttingSchedule.objects.filter(ideal=True)
    l = LaminatingSchedule.objects.filter(ideal=True)
    p = PrintingSchedule.objects.filter(ideal=True)
    ideal_end = CuttingSchedule.objects.filter(ideal=True)
    end_dates =[]
    for each in datas:
        ideal_scheds = []
        for every in ideal_end:
            if every.job_order_id == each.id:
                ideal_scheds.append(every)
        ideal_scheds.sort(key=lambda i: i.sked_out)
        if ideal_scheds:
            end_dates.append({'End': ideal_scheds[-1].sked_out.date(),
                              'PO': each.id})

    if time(6, 0) <= datetime.now().time() <= time(14, 0):
        for i in e:
            if datetime.combine(i.sked_in.date(), i.sked_in.time()) == datetime.combine(date.today(), time(6, 0)):
                ex_schedule.append(i.job_order_id)
        for j in c:
            if datetime.combine(j.sked_in.date(), j.sked_in.time()) == datetime.combine(date.today(), time(6, 0)):
                cu_schedule.append(j.job_order_id)
        for k in l:
            if datetime.combine(k.sked_in.date(), k.sked_in.time()) == datetime.combine(date.today(), time(6, 0)):
                la_schedule.append(k.job_order_id)
        for x in p:
            if datetime.combine(x.sked_in.date(), x.sked_in.time()) == datetime.combine(date.today(), time(6, 0)):
                pr_schedule.append(x.job_order_id)
    elif time(14, 0) <= datetime.now().time() <= time(22, 0):
        for i in e:
            if datetime.combine(i.sked_in.date(), i.sked_in.time()) == datetime.combine(date.today(), time(14, 0)):
                ex_schedule.append(i.job_order_id)
        for j in c:
            if datetime.combine(j.sked_in.date(), j.sked_in.time()) == datetime.combine(date.today(), time(14, 0)):
                cu_schedule.append(j.job_order_id)
        for k in l:
            if datetime.combine(k.sked_in.date(), k.sked_in.time()) == datetime.combine(date.today(), time(14, 0)):
                la_schedule.append(k.job_order_id)
        for x in p:
            if datetime.combine(x.sked_in.date(), x.sked_in.time()) == datetime.combine(date.today(), time(14, 0)):
                pr_schedule.append(x.job_order_id)
    elif datetime.now().time() >= time(22, 0):
        for i in e:
            if datetime.combine(i.sked_in.date(), i.sked_in.time()) == datetime.combine(date.today(), time(22, 0)):
                ex_schedule.append(i.job_order_id)
        for j in c:
            if datetime.combine(j.sked_in.date(), j.sked_in.time()) == datetime.combine(date.today(), time(22, 0)):
                cu_schedule.append(j.job_order_id)
        for k in l:
            if datetime.combine(k.sked_in.date(), k.sked_in.time()) == datetime.combine(date.today(), time(22, 0)):
                la_schedule.append(k.job_order_id)
        for x in p:
            if datetime.combine(x.sked_in.date(), x.sked_in.time()) == datetime.combine(date.today(), time(22, 0)):
                pr_schedule.append(x.job_order_id)
    elif datetime.now().time() <= time(6, 0):
        for i in e:
            if datetime.combine(i.sked_in.date(), i.sked_in.time()) == datetime.combine(date.today(), time(22, 0)):
                ex_schedule.append(i.job_order_id)
        for j in c:
            if datetime.combine(j.sked_in.date(), j.sked_in.time()) == datetime.combine(date.today(), time(22, 0)):
                cu_schedule.append(j.job_order_id)
        for k in l:
            if datetime.combine(k.sked_in.date(), k.sked_in.time()) == datetime.combine(date.today(), time(22, 0)):
                la_schedule.append(k.job_order_id)
        for x in p:
            if datetime.combine(x.sked_in.date(), x.sked_in.time()) == datetime.combine(date.today(), time(22, 0)):
                pr_schedule.append(x.job_order_id)

    for data in datas:
        extrusion = ExtruderSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False) & Q(datetime_in__range=[start_week, end_week])).order_by('datetime_in')
        printing = PrintingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False) & Q(datetime_in__range=[start_week, end_week])).order_by('datetime_in')
        cutting = CuttingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False) & Q(datetime_in__range=[start_week, end_week])).order_by('datetime_in')
        laminating = LaminatingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=False) & Q(datetime_in__range=[start_week, end_week])).order_by('datetime_in')
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

        last_ideal_cu = None
        last_ideal_pr = None
        last_ideal_la = None
        last_ideal_ex = None

        ideal_ex = list(ExtruderSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=True)))
        if ideal_ex:
            ideal_ex.sort(key=lambda i: i.sked_in)
            last_ideal_ex = ideal_ex[-1]
        ideal_cu = list(CuttingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=True)))
        if ideal_cu:
            ideal_cu.sort(key=lambda i: i.sked_in)
            last_ideal_cu = ideal_cu[-1]
        ideal_pr = list(PrintingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=True)))
        if ideal_pr:
            ideal_pr.sort(key=lambda i: i.sked_in)
            last_ideal_pr = ideal_pr[-1]
        ideal_la = list(LaminatingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=True)))
        if ideal_la:
            ideal_la.sort(key=lambda i: i.sked_in)
            last_ideal_la = ideal_la[-1]

        if ex_done:
            last_ex = list(extrusion)[-1]
            if last_ex.datetime_in.replace(tzinfo=None) > last_ideal_ex.sked_in.replace(tzinfo=None):
                ex_late += 1
        elif datetime.now().replace(tzinfo=None) > last_ideal_ex.sked_in.replace(tzinfo=None):
            ex_late += 1
        if cu_done:
            last_cu = list(cutting)[-1]
            if last_cu.datetime_in.replace(tzinfo=None) > last_ideal_cu.sked_in.replace(tzinfo=None):
                cu_late += 1
        elif datetime.now().replace(tzinfo=None) > last_ideal_cu.sked_in.replace(tzinfo=None):
            ex_late += 1
        if ClientItem.objects.get(client_po_id=data.id).printed == 1:
            if pr_done:
                last_pr = list(printing)[-1]
                if last_pr.datetime_in.replace(tzinfo=None) > last_ideal_pr.sked_in.replace(tzinfo=None):
                    pr_late += 1
            elif datetime.now().replace(tzinfo=None) > last_ideal_pr.sked_in.replace(tzinfo=None):
                pr_late += 1
        if ClientItem.objects.get(client_po_id=data.id).laminate == 1:
            if la_done:
                last_la = list(extrusion)[-1]
                if last_la.datetime_in.replace(tzinfo=None) > last_ideal_la.sked_in.replace(tzinfo=None):
                    la_late += 1
            elif datetime.now().replace(tzinfo=None) > last_ideal_la.sked_in.replace(tzinfo=None):
                la_late += 1

    if request.session['session_position'] == "General Manager":
        template = 'general_manager_page_ui.html'
    elif request.session['session_position'] == "Production Manager":
        template = 'production_manager_page_ui.html'
    else:
        template = 'line_leader_page_ui.html'
    context = {
        'items': items,
        'title': 'Job Order List',
        'data' : datas,
        'template' : template,
        'ex_schedule' : ex_schedule,
        'cu_schedule' : cu_schedule,
        'pr_schedule': pr_schedule,
        'la_schedule': la_schedule,
        'now': date.today(),
        'ideal_end' : end_dates,
        'ex_late' : ex_late,
        'cu_late' : cu_late,
        'pr_late' : pr_late,
        'la_late' : la_late
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

    first_ideal_cu = None
    first_ideal_pr = None
    first_ideal_la = None
    first_ideal_ex = None
    last_ideal_cu = None
    last_ideal_pr = None
    last_ideal_la = None
    last_ideal_ex = None

    ideal_ex = list(ExtruderSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=True)))
    if ideal_ex:
        ideal_ex.sort(key=lambda i: i.sked_in)
        first_ideal_ex = ideal_ex[0]
        last_ideal_ex = ideal_ex[-1]
    ideal_cu = list(CuttingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=True)))
    if ideal_cu:
        ideal_cu.sort(key=lambda i: i.sked_in)
        first_ideal_cu = ideal_cu[0]
        last_ideal_cu = ideal_cu[-1]
    ideal_pr = list(PrintingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=True)))
    if ideal_pr:
        ideal_pr.sort(key=lambda i: i.sked_in)
        first_ideal_pr = ideal_pr[0]
        last_ideal_pr = ideal_pr[-1]
    ideal_la = list(LaminatingSchedule.objects.filter(Q(job_order=data.id) & Q(ideal=True)))
    if ideal_la:
        ideal_la.sort(key=lambda i: i.sked_in)
        first_ideal_la = ideal_la[0]
        last_ideal_la = ideal_la[-1]

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
      'first_ideal_cu': first_ideal_cu,
      'first_ideal_pr': first_ideal_pr,
      'first_ideal_la': first_ideal_la,
      'first_ideal_ex': first_ideal_ex,
      'last_ideal_cu': last_ideal_cu,
      'last_ideal_pr': last_ideal_pr,
      'last_ideal_la': last_ideal_la,
      'last_ideal_ex': last_ideal_ex,
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
    items = []
    ex_output_kg = []
    ex_output_nr = []
    prt = []
    prt_output = []
    cut = []
    cut_output = []
    ex_scrap = []
    pr_scrap = []
    cu_scrap = []

    items = []
    for a in object_list:
        for x in ClientItem.objects.all():
            if x.client_po_id == a.id:
                items.append(x)

        try:
            e = ExtruderSchedule.objects.filter(job_order_id=a.id)
            try:
                ex_output_kg.append(float(e.aggregate(Sum('output_kilos'))['output_kilos__sum']))
                ex_output_nr.append(float(e.aggregate(Sum('number_rolls'))['number_rolls__sum']))
                ex_scrap.append(float(e.aggregate(Sum('extruder_scrap'))['extruder_scrap__sum']))
            except TypeError:
                ex_output_kg.append(None)
                ex_output_nr.append(None)
                ex_scrap.append(None)
        except ExtruderSchedule.DoesNotExist:
            ex_output_kg.append(None)
            ex_output_nr.append(None)
            ex_scrap.append(None)

        try:
            prts = PrintingSchedule.objects.filter(job_order_id=a.id).latest('datetime_out')
            prt.append(prts)
        except PrintingSchedule.DoesNotExist:
            prts = None

        try:
            p = PrintingSchedule.objects.filter(job_order_id=a.id)
            try:
                prt_output.append(float(p.aggregate(Sum('output_kilos'))['output_kilos__sum']))
                pr_scrap.append(float(p.aggregate(Sum('printing_scrap'))['printing_scrap__sum']))
            except TypeError:
                prt_output.append(None)
                pr_scrap.append(None)
        except ExtruderSchedule.DoesNotExist:
            prt_output.append(None)
            pr_scrap.append(None)

        try:
            cuts = CuttingSchedule.objects.filter(job_order_id=a.id).latest('datetime_out')
            cut.append(cuts)
        except CuttingSchedule.DoesNotExist:
            cuts = None

        try:
            c = CuttingSchedule.objects.filter(job_order_id=a.id)
            try:
                cut_output.append(float(c.aggregate(Sum('quantity'))['quantity__sum']))
                cu_scrap.append(float(c.aggregate(Sum('cutting_scrap'))['cutting_scrap__sum']))
            except TypeError:
                cut_output.append(None)
                cu_scrap.append(None)
        except ExtruderSchedule.DoesNotExist:
            cut_output.append(None)
            cu_scrap.append(None)

    for b in object_list:
        if str(b.id) in request.POST:
            b.status = "Delivered"
            b.date_delivered = date.today()
            b.save()

    #Cutting finish, Total output (m - kg)
    # SCRAP (extruder, printing, cutting), Remarks

    context = {
        'object_list': object_list,
        'invoice' : invoice,
        'items' : items,
        'ex_output_kg' : ex_output_kg,
        'ex_output_nr' : ex_output_nr,
        'prt' : prt,
        'cut' : cut,
        'prt_output' : prt_output,
        'cut_output' : cut_output,
        'ex_scrap' : ex_scrap,
        'cu_scrap' : cu_scrap,
        'pr_scrap' : pr_scrap
    }

    return render(request, 'production/finished_job_order_list.html', context)

def late_phase_count(phase, extrusion_late, cutting_late, laminating_late, printing_late):
    if date.today().weekday() == 0:
        extrusion_late = 0
        cutting_late = 0
        laminating_late = 0
        printing_late = 0
    else:
        if phase == 1:
            extrusion_late += 1
        elif phase == 2:
            printing_late += 1
        elif phase == 3:
            laminating_late += 1
        elif phase == 4:
            cutting_late += 1

    late_count = {'Extrusion' : extrusion_late,
                  'Cutting' : cutting_late,
                  'Printing' : laminating_late,
                  'Laminating' : printing_late}

    return late_count

# EXTRUDER 
def add_extruder_schedule(request, id):
    data = JobOrder.objects.get(id=id)
    item = ClientItem.objects.get(client_po_id=id)
    e = ExtruderSchedule.objects.filter(Q(job_order_id=id) & Q(ideal=False))
    e.job_order = id
    form = ExtruderScheduleForm(request.POST)
    ideal = ExtruderSchedule.objects.filter(Q(job_order_id=id) & Q(ideal=True)).order_by('sked_in')
    printed = False
    if item.printed == 1:
        printed = True

    if request.method == 'POST':
        data.status = 'Under Extrusion'
        data.save()
        if form.is_valid():
            x = request.POST.get("weight_rolls")
            y = float(x) * float(4.74)
            form = form.save(commit=False)
            form.balance = float(y)
            form.ideal = False
            new_schedule = form.save()
            pasok = request.POST.get('datetime_in')
            pasok = datetime.strptime(pasok, "%Y-%m-%d %H:%M")
            labas = request.POST.get('datetime_out')
            labas = datetime.strptime(labas, "%Y-%m-%d %H:%M")
            all_ideal = ExtruderSchedule.objects.filter(
                Q(ideal=True) & Q(sked_mach_id=request.POST.get('machine')) &
                ~Q(job_order_id=id)).order_by('sked_in')
            final = request.POST.get('final')
            if all_ideal:
                for xy in all_ideal:
                    sked_in_1 = xy.sked_in - timedelta(hours=3)
                    sked_in_2 = xy.sked_in + timedelta(hours=3)
                    sked_out_1 = xy.sked_out - timedelta(hours=3)
                    sked_out_2 = xy.sked_out + timedelta(hours=3)
                    sked_in_1 = sked_in_1.replace(tzinfo=None)
                    sked_in_2 = sked_in_2.replace(tzinfo=None)
                    sked_out_1 = sked_out_1.replace(tzinfo=None)
                    sked_out_2 = sked_out_2.replace(tzinfo=None)
                    if sked_in_1 <= pasok <= sked_in_2 or \
                            sked_out_1 <= labas <= sked_out_2:
                        if final == 1:
                            in_production = JobOrder.objects.filter(
                                ~Q(status='On Queue') & ~Q(status='Ready for delivery') & ~Q(status='Delivered') & ~Q(status='Waiting'))
                            sales_views.save_schedule(request, None, labas, id, False, True, True, True, in_production, False)
                            print('resched, final')
                        else:
                            in_production = JobOrder.objects.filter(
                                ~Q(status='On Queue') & ~Q(status='Ready for delivery') & ~Q(status='Delivered') & ~Q(status='Waiting'))
                            sales_views.save_schedule(request, None, labas, id, True, True, True, True, in_production, False)
                            print('resched, not final')
            if form.final:
                if printed:
                    data.status = 'Under Printing'
                    data.save()
                else:
                    data.status = 'Under Cutting'
                    data.save()
            else:
                data.save()
        return redirect('production:job_order_details', id=id)

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

    if ideal and not e:
        sked_in = ideal.first().sked_in
        sked_out = ideal.first().sked_out
        sked_op = ideal.first().sked_op
        sked_mach = ideal.first().sked_mach
    elif e:
        exists = len(e)
        if ideal[exists]:
            sked_in = ideal[exists].sked_in
            sked_out = ideal[exists].sked_out
        else:
            sked_in = datetime.now()
            sked_out = datetime.now() + timedelta(days=int((item.quantity * 80) / 70000))
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

    form.fields["machine"].queryset = Machine.objects.filter(Q(machine_type='Extruder') & Q(state='OK'))
    form.fields["operator"].queryset = Employee.objects.filter(Q(position='Extruder') | Q(position='Cutting') | Q(position='Laminating') | Q(position='Printing'))
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
    ideal = PrintingSchedule.objects.filter(Q(job_order_id=id) & Q(ideal=True)).order_by('sked_in')
    p = PrintingSchedule.objects.filter(Q(job_order_id=id) & Q(ideal=False))
    p.job_order = id
    items = ClientItem.objects.filter(client_po=id)
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
            pasok = request.POST.get('datetime_in')
            pasok = datetime.strptime(pasok, "%Y-%m-%d %H:%M")
            labas = request.POST.get('datetime_out')
            labas = datetime.strptime(labas, "%Y-%m-%d %H:%M")
            all_ideal = PrintingSchedule.objects.filter(
                Q(ideal=True) & Q(sked_mach_id=request.POST.get('machine')) &
                ~Q(job_order_id=id)).order_by('sked_in')
            final = request.POST.get('final')
            if all_ideal:
                for x in all_ideal:
                    sked_in_1 = x.sked_in - timedelta(hours=3)
                    sked_in_2 = x.sked_in + timedelta(hours=3)
                    sked_out_1 = x.sked_out - timedelta(hours=3)
                    sked_out_2 = x.sked_out + timedelta(hours=3)
                    sked_in_1 = sked_in_1.replace(tzinfo=None)
                    sked_in_2 = sked_in_2.replace(tzinfo=None)
                    sked_out_1 = sked_out_1.replace(tzinfo=None)
                    sked_out_2 = sked_out_2.replace(tzinfo=None)
                    if sked_in_1 <= pasok <= sked_in_2 or \
                            sked_out_1 <= labas <= sked_out_2:
                        if final == 1:
                            in_production = JobOrder.objects.filter(
                                ~Q(status='On Queue') & ~Q(status='Ready for delivery') & ~Q(status='Delivered') & ~Q(status='Waiting'))
                            sales_views.save_schedule(request, None, labas, id, True, True, False, True, in_production, False)
                            print('resched, final')
                        else:
                            in_production = JobOrder.objects.filter(
                                ~Q(status='On Queue') & ~Q(status='Ready for delivery') & ~Q(status='Delivered') & ~Q(status='Waiting'))
                            sales_views.save_schedule(request, None, labas, id, True, True, True, True, in_production, False)
                            print('resched, not final')
            if form.final:
                if laminate:
                    data.status = 'Under Laminating'
                    data.save()
                else:
                    data.status = 'Under Cutting'
                    data.save()
            else:
                data.save()
        return redirect('production:job_order_details', id=data.id)

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

    if ideal and not p:
        sked_in = ideal.first().sked_in
        sked_out = ideal.first().sked_out
        sked_op = ideal.first().sked_op
        sked_mach = ideal.first().sked_mach
    elif p:
        exists = len(p)
        if ideal[exists]:
            sked_in = ideal[exists].sked_in
            sked_out = ideal[exists].sked_out
        else:
            sked_in = datetime.now()
            sked_out = datetime.now() + timedelta(days=int((item.quantity * 100) / 70000))
    else:
        sked_in = datetime.now()
        sked_out = datetime.now() + timedelta(days=int((item.quantity * 100) / 70000))

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
    form.fields["operator"].queryset = Employee.objects.filter(
        Q(position='Extruder') | Q(position='Cutting') | Q(position='Laminating') | Q(position='Printing'))
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

    return render(request, 'production/add_printing_schedule.html', context)

# CUTTING
def add_cutting_schedule(request, id):
    data = JobOrder.objects.get(id=id)
    item = ClientItem.objects.get(client_po_id=id)
    form = CuttingScheduleForm(request.POST)
    invoice = SalesInvoice.objects.get(client_po=data)
    client = data.client
    ideal = CuttingSchedule.objects.filter(Q(job_order_id=id) & Q(ideal=True)).order_by('sked_in')

    c = CuttingSchedule.objects.filter(Q(job_order_id=id) & Q(ideal=False))
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
            pasok = request.POST.get('datetime_in')
            pasok = datetime.strptime(pasok, "%Y-%m-%d %H:%M")
            labas = request.POST.get('datetime_out')
            labas = datetime.strptime(labas, "%Y-%m-%d %H:%M")
            all_ideal = CuttingSchedule.objects.filter(
                Q(ideal=True) & Q(sked_mach_id=request.POST.get('machine')) &
                ~Q(job_order_id=id)).order_by('sked_in')
            final = request.POST.get('final')
            if all_ideal:
                for x in all_ideal:
                    sked_in_1 = x.sked_in - timedelta(hours=3)
                    sked_in_2 = x.sked_in + timedelta(hours=3)
                    sked_out_1 = x.sked_out - timedelta(hours=3)
                    sked_out_2 = x.sked_out + timedelta(hours=3)
                    sked_in_1 = sked_in_1.replace(tzinfo=None)
                    sked_in_2 = sked_in_2.replace(tzinfo=None)
                    sked_out_1 = sked_out_1.replace(tzinfo=None)
                    sked_out_2 = sked_out_2.replace(tzinfo=None)
                    if sked_in_1 <= pasok <= sked_in_2 or \
                            sked_out_1 <= labas <= sked_out_2:
                        if final == 1:
                            in_production = JobOrder.objects.filter(
                                ~Q(status='On Queue') & ~Q(status='Ready for delivery') & ~Q(status='Delivered') & ~Q(status='Waiting'))
                            sales_views.save_schedule(request, None, labas, id, True, False, True, True, in_production, False)
                            print('resched, final')
                        else:
                            in_production = JobOrder.objects.filter(~Q(status='On Queue') & ~Q(status='Ready for delivery') & ~Q(status='Delivered') & ~Q(status='Waiting'))
                            sales_views.save_schedule(request, None, labas, id, True, True, True, True, in_production, False)
                            print('resched, not final')
        if form.final:
            data.status = 'Ready for delivery'
            data.save()
            invoice.date_issued = date.today()
            invoice.date_due = invoice.calculate_date_due()
            invoice.total_paid = 0
            invoice.save()

            client.outstanding_balance += invoice.total_amount_computed
            client.save()
        return redirect('production:job_order_details', id=data.id)

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

    if ideal and not c:
        sked_in = ideal.first().sked_in
        sked_out = ideal.first().sked_out
        sked_op = ideal.first().sked_op
        sked_mach = ideal.first().sked_mach
    elif c:
        exists = len(c)
        if ideal[exists]:
            sked_in = ideal[exists].sked_in
            sked_out = ideal[exists].sked_out
        else:
            sked_in = datetime.now()
            sked_out = datetime.now() + timedelta(days=int((item.quantity * 60) / 70000))
    else:
        sked_in = datetime.now()
        sked_out = datetime.now() + timedelta(days=int((quantity * 60) / 70000))

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

    form.fields["machine"].queryset = Machine.objects.filter(Q(machine_type='Cutting') & Q(state='OK'))
    form.fields["operator"].queryset = Employee.objects.filter(
        Q(position='Extruder') | Q(position='Cutting') | Q(position='Laminating') | Q(position='Printing'))
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
        'id': id
    }

    return render(request, 'production/add_cutting_schedule.html', context)


def add_laminating_schedule(request, id):
    data = JobOrder.objects.get(id=id)
    form = LaminatingScheduleForm(request.POST)
    l = LaminatingSchedule.objects.filter(Q(job_order_id = id) & Q(ideal=False))
    item = ClientItem.objects.get(client_po_id=id)
    ideal = LaminatingSchedule.objects.filter(Q(job_order_id=id) & Q(ideal=True)).order_by('sked_in')
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
            pasok = request.POST.get('datetime_in')
            pasok = datetime.strptime(pasok, "%Y-%m-%d %H:%M")
            labas = request.POST.get('datetime_out')
            labas = datetime.strptime(labas, "%Y-%m-%d %H:%M")
            all_ideal = LaminatingSchedule.objects.filter(
                Q(ideal=True) & Q(sked_mach_id=request.POST.get('machine')) &
                ~Q(job_order_id=id)).order_by('sked_in')
            final = request.POST.get('final')
            if all_ideal:
                for x in all_ideal:
                    sked_in_1 = x.sked_in - timedelta(hours=3)
                    sked_in_2 = x.sked_in + timedelta(hours=3)
                    sked_out_1 = x.sked_out - timedelta(hours=3)
                    sked_out_2 = x.sked_out + timedelta(hours=3)
                    sked_in_1 = sked_in_1.replace(tzinfo=None)
                    sked_in_2 = sked_in_2.replace(tzinfo=None)
                    sked_out_1 = sked_out_1.replace(tzinfo=None)
                    sked_out_2 = sked_out_2.replace(tzinfo=None)
                    if sked_in_1 <= pasok <= sked_in_2 or \
                            sked_out_1 <= labas <= sked_out_2:
                        if final == 1:
                            in_production = JobOrder.objects.filter(
                                ~Q(status='On Queue') & ~Q(status='Ready for delivery') & ~Q(status='Delivered') & ~Q(status='Waiting'))
                            sales_views.save_schedule(request, None, labas, id, True, True, True, False, in_production, False)
                            print('resched, final')
                        else:
                            in_production = JobOrder.objects.filter(
                                ~Q(status='On Queue') & ~Q(status='Ready for delivery') & ~Q(status='Delivered') & ~Q(status='Waiting'))
                            sales_views.save_schedule(request, None, labas, id, True, True, True, True, in_production, False)
                            print('resched, not final')
            if form.final:
                data.status = 'Under Cutting'
                data.save()
        return redirect('production:job_order_details', id=data.id)

    quantity = item.quantity

    if ideal and not l:
        sked_in = ideal.first().sked_in
        sked_out = ideal.first().sked_out
        sked_op = ideal.first().sked_op
        sked_mach = ideal.first().sked_mach
    elif l:
        exists = len(l)
        if ideal[exists]:
            sked_in = ideal[exists].sked_in
            sked_out = ideal[exists].sked_out
        else:
            sked_in = datetime.now()
            sked_out = datetime.now() + timedelta(days=int((item.quantity * 60) / 70000))
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
    form.fields["operator"].queryset = Employee.objects.filter(
        Q(position='Extruder') | Q(position='Cutting') | Q(position='Laminating') | Q(position='Printing'))
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
    if ex_list:
        ideal.append(ex_list)
    cu = []
    for y in CuttingSchedule.objects.filter(ideal=True):
        job = y.job_order
        if job.status == 'Ready for delivery' or job.status == 'Delivered':
            pass
        else:
            cu.append(y)
    cu_list = list(cu)
    if cu_list:
        ideal.append(cu_list)
    pr = []
    for z in PrintingSchedule.objects.filter(ideal=True):
        job = z.job_order
        if job.status == 'Ready for delivery' or job.status == 'Delivered':
            pass
        else:
            pr.append(z)
    pr_list = list(pr)
    if pr_list:
        ideal.append(pr_list)
    la = []
    for a in LaminatingSchedule.objects.filter(ideal=True):
        job = a.job_order
        if job.status == 'Ready for delivery' or job.status == 'Delivered':
            pass
        else:
            la.append(a)
    la_list = list(la)
    if la_list:
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

        machines_in_production = []
        all_machines = Machine.objects.filter(state='OK')

        for q in range(len(plot_list)):
            if plot_list[q]['Machine'] not in machines_in_production:
                if plot_list[q]['Machine'] not in machines_in_production:
                    machines_in_production.append(plot_list[q]['Machine'])

            # Machine breakdown.
            is_it_ok = plot_list[q]['Machine']

            if is_it_ok.state == 'OK':
                pass
            else:
                print('MACHINE BREAKDOWN')
                in_production = JobOrder.objects.filter(
                    ~Q(status='On Queue') & ~Q(status='Ready for delivery') & ~Q(status='Delivered'))
                plot_list = sales_views.save_schedule(request, None, None, None, True, True, True, True, in_production, False)
                break

        # Machine recently deployed.
        yung_wala = set(all_machines).difference(machines_in_production)
        print(yung_wala)
        yes_deployed = False
        for x in yung_wala:
            for y in range(len(plot_list)):
                if x.machine_type == plot_list[y]['Task'] or x.machine_type == 'Extruder':
                    yes_deployed = True
        if yung_wala and yes_deployed:
            print('MACHINE RECENTLY DEPLOYED')
            in_production = JobOrder.objects.filter(
                ~Q(status='On Queue') & ~Q(status='Ready for delivery') & ~Q(status='Delivered'))
            plot_list = sales_views.save_schedule(request, None, None, None, True, True, True, True, in_production, False)

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
        print('NO IDEAL')
        in_production = JobOrder.objects.filter(
            ~Q(status='On Queue') & ~Q(status='Ready for delivery') & ~Q(status='Delivered') & ~Q(status='Waiting'))
        plot_list = sales_views.save_schedule(request, None, None, None, True, True, True, True, in_production, False)

    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=7)
    start_month = today.replace(day=1)
    day = []
    week = []
    month = []
    start_day = time(6, 0)
    day.append(start_day)
    mid_day = time(14, 0)
    day.append(mid_day)
    end_day = time(22, 0)
    day.append(end_day)
    for i in range(0,7):
        week.append(start_week)
        start_week += timedelta(days=1)
    for i in range(0, calendar.monthrange(today.year, today.month)[1]):
        month.append(start_month)
        start_month += timedelta(days=1)
    start_week = today - timedelta(days=today.weekday())
    this_day = []
    this_week = []
    this_month = []

    for i in range(len(plot_list)):
        if start_week <= plot_list[i]['Start'].date() <= end_week:
            this_week.append(plot_list[i])
        if plot_list[i]['Start'].month == today.month:
            this_month.append(plot_list[i])

    for x in this_month:
        for y in month:
            if x['Start'].date() == y:
                this_day.append(x)

    shift_list = []

    shift1_str = '6::00::00'
    shift2_str = '14::00::00'
    shift3_str = '22::00::00'

    shifts = {
        'shift1': datetime.strptime(shift1_str, '%H::%M::%S').time(),
        'shift2': datetime.strptime(shift2_str, '%H::%M::%S').time(),
        'shift3': datetime.strptime(shift3_str, '%H::%M::%S').time()
    }

    shift_list.append(shifts)

    items = []
    products = []

    for x in ClientItem.objects.all():
        items.append(x)

    for y in Product.objects.all():
        products.append(y)

    context = {
        'products': products,
        'items': items,
        'shifts': shift_list,
        'ideal': ideal,
        'plot_list': plot_list,
        'machines': machines,
        'this_day': this_day,
        'this_week': this_week,
        'this_month': this_month,
        'week': week,
        'month': month,
        'today': today,
        'day': day
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
    day = []
    week = []
    month = []
    start_day = time(6, 0)
    day.append(start_day)
    mid_day = time(14, 0)
    day.append(mid_day)
    end_day = time(22, 0)
    day.append(end_day)

    for i in range(0, 7):
        week.append(start_week)
        start_week += timedelta(days=1)
    for i in range(0, calendar.monthrange(today.year, today.month)[1]):
        month.append(start_month)
        start_month += timedelta(days=1)
    start_week = today - timedelta(days=today.weekday())

    this_day = []
    this_week = []
    this_month = []

    for i in range(len(plot_list)):
        if start_week <= plot_list[i]['Start'].date() <= end_week:
            this_week.append(plot_list[i])
        if plot_list[i]['Start'].month == today.month:
            this_month.append(plot_list[i])

    for x in this_month:
        for y in month:
            if x['Start'].date() == y:
                this_day.append(x)

    shift_list = []

    shift1_str = '6::00::00'
    shift2_str = '14::00::00'
    shift3_str = '22::00::00'

    shifts = {
        'shift1': datetime.strptime(shift1_str, '%H::%M::%S').time(),
        'shift2': datetime.strptime(shift2_str, '%H::%M::%S').time(),
        'shift3': datetime.strptime(shift3_str, '%H::%M::%S').time()
    }

    shift_list.append(shifts)
    print(this_day)
    for x in day:
        for b in range(len(this_day)):
            if this_day[b]['Start'].hour == x.hour:
                print('pass')

    items = []
    products = []

    for x in ClientItem.objects.all():
        items.append(x)

    for y in Product.objects.all():
        products.append(y)

    context = {
        'day': day,
        'products': products,
        'items': items,
        'shifts': shift_list,
        'this_day': this_day,
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
    day = []
    week = []
    month = []
    start_day = time(6, 0)
    day.append(start_day)
    mid_day = time(14, 0)
    day.append(mid_day)
    end_day = time(22, 0)
    day.append(end_day)

    for i in range(0, 7):
        week.append(start_week)
        start_week += timedelta(days=1)
    for i in range(0, calendar.monthrange(today.year, today.month)[1]):
        month.append(start_month)
        start_month += timedelta(days=1)
    start_week = today - timedelta(days=today.weekday())

    this_day = []
    this_week = []
    this_month = []

    for i in range(len(plot_list)):
        if start_week <= plot_list[i]['Start'].date() <= end_week:
            this_week.append(plot_list[i])
        if plot_list[i]['Start'].month == today.month:
            this_month.append(plot_list[i])

    for x in this_month:
        for y in month:
            if x['Start'].date() == y:
                this_day.append(x)

    shift_list = []

    shift1_str = '6::00::00'
    shift2_str = '14::00::00'
    shift3_str = '22::00::00'

    shifts = {
        'shift1': datetime.strptime(shift1_str, '%H::%M::%S').time(),
        'shift2': datetime.strptime(shift2_str, '%H::%M::%S').time(),
        'shift3': datetime.strptime(shift3_str, '%H::%M::%S').time()
    }

    shift_list.append(shifts)
    print(this_day)
    for x in day:
        for b in range(len(this_day)):
            if this_day[b]['Start'].hour == x.hour:
                print('pass')

    items = []
    products = []

    for x in ClientItem.objects.all():
        items.append(x)

    for y in Product.objects.all():
        products.append(y)

    context = {
        'day': day,
        'products': products,
        'items': items,
        'shifts': shift_list,
        'this_day': this_day,
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
    day = []
    week = []
    month = []
    start_day = time(6, 0)
    day.append(start_day)
    mid_day = time(14, 0)
    day.append(mid_day)
    end_day = time(22, 0)
    day.append(end_day)

    for i in range(0, 7):
        week.append(start_week)
        start_week += timedelta(days=1)
    for i in range(0, calendar.monthrange(today.year, today.month)[1]):
        month.append(start_month)
        start_month += timedelta(days=1)
    start_week = today - timedelta(days=today.weekday())

    this_day = []
    this_week = []
    this_month = []

    for i in range(len(plot_list)):
        if start_week <= plot_list[i]['Start'].date() <= end_week:
            this_week.append(plot_list[i])
        if plot_list[i]['Start'].month == today.month:
            this_month.append(plot_list[i])

    for x in this_month:
        for y in month:
            if x['Start'].date() == y:
                this_day.append(x)

    shift_list = []

    shift1_str = '6::00::00'
    shift2_str = '14::00::00'
    shift3_str = '22::00::00'

    shifts = {
        'shift1': datetime.strptime(shift1_str, '%H::%M::%S').time(),
        'shift2': datetime.strptime(shift2_str, '%H::%M::%S').time(),
        'shift3': datetime.strptime(shift3_str, '%H::%M::%S').time()
    }

    shift_list.append(shifts)
    print(this_day)
    for x in day:
        for b in range(len(this_day)):
            if this_day[b]['Start'].hour == x.hour:
                print('pass')

    items = []
    products = []

    for x in ClientItem.objects.all():
        items.append(x)

    for y in Product.objects.all():
        products.append(y)

    context = {
        'day': day,
        'products': products,
        'items': items,
        'shifts': shift_list,
        'this_day': this_day,
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
    day = []
    week = []
    month = []
    start_day = time(6, 0)
    day.append(start_day)
    mid_day = time(14, 0)
    day.append(mid_day)
    end_day = time(22, 0)
    day.append(end_day)

    for i in range(0, 7):
        week.append(start_week)
        start_week += timedelta(days=1)
    for i in range(0, calendar.monthrange(today.year, today.month)[1]):
        month.append(start_month)
        start_month += timedelta(days=1)
    start_week = today - timedelta(days=today.weekday())

    this_day = []
    this_week = []
    this_month = []

    for i in range(len(plot_list)):
        if start_week <= plot_list[i]['Start'].date() <= end_week:
            this_week.append(plot_list[i])
        if plot_list[i]['Start'].month == today.month:
            this_month.append(plot_list[i])

    for x in this_month:
        for y in month:
            if x['Start'].date() == y:
                this_day.append(x)

    shift_list = []

    shift1_str = '6::00::00'
    shift2_str = '14::00::00'
    shift3_str = '22::00::00'

    shifts = {
        'shift1': datetime.strptime(shift1_str, '%H::%M::%S').time(),
        'shift2': datetime.strptime(shift2_str, '%H::%M::%S').time(),
        'shift3': datetime.strptime(shift3_str, '%H::%M::%S').time()
    }

    shift_list.append(shifts)
    print(this_day)
    for x in day:
        for b in range(len(this_day)):
            if this_day[b]['Start'].hour == x.hour:
                print('pass')

    items = []
    products = []

    for x in ClientItem.objects.all():
        items.append(x)

    for y in Product.objects.all():
        products.append(y)

    context = {
        'day': day,
        'products': products,
        'items': items,
        'shifts': shift_list,
        'this_day': this_day,
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
    e = ExtruderSchedule.objects.filter(ideal=True)
    c = CuttingSchedule.objects.filter(ideal=True)
    l = LaminatingSchedule.objects.filter(ideal=True)
    p = PrintingSchedule.objects.filter(ideal=True)

    if time(6, 0) <= datetime.now().time() < time(14, 0):
        shift = 1
        for i in e:
            if datetime.combine(i.sked_in.date(), i.sked_in.time()) == datetime.combine(today, time(6, 0)):
                ex_schedule.append(i)
        for j in c:
            if datetime.combine(j.sked_in.date(), j.sked_in.time()) == datetime.combine(today, time(6, 0)):
                cu_schedule.append(j)
        for k in l:
            if datetime.combine(k.sked_in.date(), k.sked_in.time()) == datetime.combine(today, time(6, 0)):
                la_schedule.append(k)
        for x in p:
            if datetime.combine(x.sked_in.date(), x.sked_in.time()) == datetime.combine(today, time(6, 0)):
                pr_schedule.append(x)

    elif time(14, 0) <= datetime.now().time() < time(22,0):
        shift = 2
        for i in e:
            if datetime.combine(i.sked_in.date(), i.sked_in.time()) == datetime.combine(today, time(14, 0)):
                ex_schedule.append(i)
        for j in c:
            if datetime.combine(j.sked_in.date(), j.sked_in.time()) == datetime.combine(today, time(14, 0)):
                cu_schedule.append(j)
        for k in l:
            if datetime.combine(k.sked_in.date(), k.sked_in.time()) == datetime.combine(today, time(14, 0)):
                la_schedule.append(k)
        for x in p:
            if datetime.combine(x.sked_in.date(), x.sked_in.time()) == datetime.combine(today, time(14, 0)):
                pr_schedule.append(x)

    elif datetime.now().time() >= time(22, 0) or datetime.now().time() < time(6, 0):
        shift = 3
        for i in e:
            if datetime.combine(i.sked_in.date(), i.sked_in.time()) == datetime.combine(today, time(22, 0)):
                ex_schedule.append(i)
        for j in c:
            if datetime.combine(j.sked_in.date(), j.sked_in.time()) == datetime.combine(today, time(22, 0)):
                cu_schedule.append(j)
        for k in l:
            if datetime.combine(k.sked_in.date(), k.sked_in.time()) == datetime.combine(today, time(22, 0)):
                la_schedule.append(k)
        for x in p:
            if datetime.combine(x.sked_in.date(), x.sked_in.time()) == datetime.combine(today, time(22, 0)):
                pr_schedule.append(x)

    else:
        shift = 0

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

def weekly_schedule(request):
    ex_schedule = []
    cu_schedule = []
    pr_schedule = []
    la_schedule = []
    today = date.today()
    e = ExtruderSchedule.objects.all()
    c = CuttingSchedule.objects.all()
    l = LaminatingSchedule.objects.all()
    p = PrintingSchedule.objects.all()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=7)
    week = []

    for i in range(0, 7):
        week.append(start_week)
        start_week += timedelta(days=1)
    start_week = today - timedelta(days=today.weekday())

    for i in e:
        sked_in = i.sked_in
        if sked_in:
            if start_week <= sked_in.date() < end_week:
                ex_schedule.append(i)
    for j in c:
        sked_in = j.sked_in
        if sked_in:
            if start_week <= sked_in.date() < end_week:
                cu_schedule.append(j)
    for k in l:
        sked_in = k.sked_in
        if sked_in:
            if start_week <= sked_in.date() < end_week:
                la_schedule.append(k)
    for x in p:
        sked_in = x.sked_in
        if sked_in:
            if start_week <= sked_in.date() < end_week:
                pr_schedule.append(x)


    context = {
        'ex_schedule' : ex_schedule,
        'cu_schedule' : cu_schedule,
        'la_schedule' : la_schedule,
        'pr_schedule' : pr_schedule,
        'now' : today,
        'week' : week

    }
    return render(request, 'production/weekly_schedule.html', context)

def sched_test(request):
    cursor = connection.cursor()
    query = "SELECT j.id, i.laminate, i.printed, p.material_type FROM production_mgt_joborder j, sales_mgt_clientitem i, sales_mgt_product p " \
            "WHERE p.id = i.products_id and i.client_po_id = j.id and " \
            "NOT j.status=" + "'Waiting'" + " and NOT j.status=" + "'Ready for delivery'" + " and NOT j.status =" + "'Delivered'"
    cursor.execute(query)
    df = pd.read_sql(query, connection)

    ideal_sched = cpsatworkertest.flexible_jobshop(df, None, None, True, True, True, True, None)

    context = {}

    return render(request, 'production/sched_test.html', context)

def sched_test_2(request):
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
            print('DELETED EX: '+str(job))
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
    pk = None
    if pk is not None:
        item = ClientItem.objects.get(client_po_id=pk)
        mat = item.products.material_type

        data = {'id': pk,
                'laminate': item.laminate,
                'printed': item.printed,
                'material_type': mat}
        df2 = pd.DataFrame(data, index=[0])
        df = df.append(df2, ignore_index=True)
    else:
        pass

    ideal_sched = cpsat.flexible_jobshop(df, None, None, True, True, True, True, None)

    [print("%s %s %s %s %s %s %s\n" % (item['ID'], item['Machine'], item['Task'], item['Start'], item['Finish'], item['Resource'], item['Worker']))
    for item in ideal_sched]

    shift1 = [] #0600-1400
    shift2 = [] #1400-2200
    shift3 = [] #2200-0600'
    new_ideal_sched = []
    ideal_sched.sort(key=lambda i: i['Start'])

    for x in range(len(ideal_sched)):
        '''
        if 2 <= ideal_sched[x]['Start'].hour < 10:
            print('JOB: '+str(ideal_sched[x]['ID']))
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
                other_workers = Employee.objects.filter(Q(position='Cutting') | Q(position='Printing') | Q(position='Laminating'))
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
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout, skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)
            elif ideal_sched[x]['Task'] == 'Cutting':
                ideal_workers = Employee.objects.filter(position='Cutting')
                other_workers = Employee.objects.filter(Q(position='Extruder') | Q(position='Printing') | Q(position='Laminating'))
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
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout, skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)
            elif ideal_sched[x]['Task'] == 'Printing':
                ideal_workers = Employee.objects.filter(position='Printing')
                other_workers = Employee.objects.filter(Q(position='Extruder') | Q(position='Cutting') | Q(position='Laminating'))
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
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout, skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

            elif ideal_sched[x]['Task'] == 'Laminating':
                ideal_workers = Employee.objects.filter(position='Laminating')
                other_workers = Employee.objects.filter(Q(position='Extruder') | Q(position='Cutting') | Q(position='Printing'))
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
                    divide_task_1(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout, skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

        elif 10 <= ideal_sched[x]['Start'].hour < 18 :
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
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout, skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

            elif ideal_sched[x]['Task'] == 'Cutting':
                ideal_workers = Employee.objects.filter(position='Cutting')
                other_workers = Employee.objects.filter(Q(position='Extruder') | Q(position='Printing') | Q(position='Laminating'))
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
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout, skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

            elif ideal_sched[x]['Task'] == 'Printing':
                ideal_workers = Employee.objects.filter(position='Printing')
                other_workers = Employee.objects.filter(Q(position='Extruder') | Q(position='Cutting') | Q(position='Laminating'))
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
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout, skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

            elif ideal_sched[x]['Task'] == 'Laminating':
                ideal_workers = Employee.objects.filter(position='Laminating')
                other_workers = Employee.objects.filter(Q(position='Extruder') | Q(position='Cutting') | Q(position='Printing'))
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
                    divide_task_2(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout, skedindate,
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
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout, skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

            elif ideal_sched[x]['Task'] == 'Cutting':
                ideal_workers = Employee.objects.filter(position='Cutting')
                other_workers = Employee.objects.filter(Q(position='Extruder') | Q(position='Printing') | Q(position='Laminating'))
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
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout, skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

            elif ideal_sched[x]['Task'] == 'Printing':
                ideal_workers = Employee.objects.filter(position='Printing')
                other_workers = Employee.objects.filter(Q(position='Extruder') | Q(position='Cutting') | Q(position='Laminating'))
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
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout, skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)

            elif ideal_sched[x]['Task'] == 'Laminating':
                ideal_workers = Employee.objects.filter(position='Laminating')
                other_workers = Employee.objects.filter(Q(position='Extruder') | Q(position='Cutting') | Q(position='Printing'))
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
                    divide_task_3(ideal_workers, other_workers, all_skeds, ideal_sched, x, job, skedin, skedout, skedindate,
                                  shift1, shift2, shift3, new_ideal_sched)
        '''

    context = {}

    return render(request, 'production/sched_test.html', context)
