from django import forms
from django.forms import ModelForm, ValidationError, Form, widgets
from decimal import Decimal
from django.contrib.admin.widgets import AdminDateWidget
from django.utils import formats
from datetime import date

from .models import ExtruderSchedule, PrintingSchedule, CuttingSchedule, Machine, Employee, JobOrder

class ExtruderScheduleForm(forms.ModelForm):
    SHIFTS = (
        ('Shift 1', 'shift 1'),
        ('Shift 2', 'shift 2'),
        ('Shift 3', 'shift 3')
    )

    DAY = (
        ('a.m.', 'a.m.'),
        ('p.m.', 'p.m.')
    )

    class Meta:
        model = ExtruderSchedule
        fields = ('job_order', 'machine', 'operator', 'shift', 'weight_rolls', 'time_in','day',
        'core_weight', 'net_weight', 'output_kilos', 'number_rolls', 'starting_scrap', 'extruder_scrap',
        'balance', 'remarks')

    day = forms.CharField(widget = forms.Select(choices=DAY))
    time_in = forms.TimeField(widget = forms.TimeInput(format=['%H:%M']))
    shift = forms.CharField(max_length=200, label = 'shift', widget = forms.Select(choices=SHIFTS))
    remarks = forms.CharField(widget = forms.Textarea(attrs={'rows':'3'}))
    machine = forms.ModelChoiceField(queryset=Machine.objects.all())
    operator = forms.ModelChoiceField(queryset=Employee.objects.all())

class PrintingScheduleForm(forms.ModelForm):
    SHIFTS = (
        ('Shift 1', 'shift 1'),
        ('Shift 2', 'shift 2'),
        ('Shift 3', 'shift 3')
    )


    DAY = (
        ('a.m.', 'a.m.'),
        ('p.m.', 'p.m.')
    )

    class Meta:
        model = PrintingSchedule
        fields = ('job_order', 'machine', 'operator', 'shift', 'number_rolls', 'day', 'time_in',
        'exit_scrap','printing_scrap', 'remarks')

    day = forms.CharField(widget = forms.Select(choices=DAY))
    time_in = forms.TimeField(widget = forms.TimeInput(format=['%H:%M']))
    shift = forms.CharField(max_length=200, label = 'shift', widget = forms.Select(choices=SHIFTS))
    remarks = forms.CharField(widget = forms.Textarea(attrs={'rows':'3'}))
    machine = forms.ModelChoiceField(queryset=Machine.objects.all())
    operator = forms.ModelChoiceField(queryset=Employee.objects.all())

class CuttingScheduleForm(forms.ModelForm):
    SHIFTS = (
        ('Shift 1', 'shift 1'),
        ('Shift 2', 'shift 2'),
        ('Shift 3', 'shift 3')
    )

    LINE = (
        ('Line 1', 'Line 1'),
        ('Line 2', 'Line 2'),
        ('Line 3', 'Line 3')
    )
    
    DAY = (
        ('a.m.', 'a.m.'),
        ('p.m.', 'p.m.')
    )

    class Meta:
        model = CuttingSchedule
        fields = ('job_order', 'machine', 'operator', 'shift', 'line', 'day', 'time_in',
        'quantity', 'output_kilos', 'number_rolls', 'exit_scrap', 'cutting_scrap', 'remarks')

    day = forms.CharField(widget = forms.Select(choices=DAY))
    time_in = forms.TimeField(widget = forms.TimeInput(format=['%H:%M']))
    line = forms.CharField(max_length=200, label = 'line', widget = forms.Select(choices=LINE))
    shift = forms.CharField(max_length=200, label = 'shift', widget = forms.Select(choices=SHIFTS))
    remarks = forms.CharField(widget = forms.Textarea(attrs={'rows':'3'}))
    machine = forms.ModelChoiceField(queryset=Machine.objects.all())
    operator = forms.ModelChoiceField(queryset=Employee.objects.all())