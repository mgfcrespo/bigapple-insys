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
        fields = ('job_order', 'machine', 'weight_rolls', 'time_in','day_in', 'time_out','day_out',
        'core_weight', 'net_weight', 'output_kilos', 'number_rolls', 'starting_scrap', 'extruder_scrap','remarks')
        # widgets = {
        #     'time_in': TimeInput(),
        #     'time_out': TimeInput()
        # }

    day_in = forms.CharField(widget = forms.Select(choices=DAY))
    time_in = forms.TimeField(widget = forms.TimeInput(format=['%H:%M']))
    day_out = forms.CharField(widget = forms.Select(choices=DAY))
    time_out = forms.TimeField(widget = forms.TimeInput(format=['%H:%M']))
    remarks = forms.CharField(widget = forms.Textarea(attrs={'rows':'3'}))
    machine = forms.ModelChoiceField(queryset=Machine.objects.all())
    
    def __init__(self, *args, **kwargs):
        super(ExtruderScheduleForm, self).__init__(*args, **kwargs)
        self.fields['remarks'].required = False

class PrintingScheduleForm(forms.ModelForm):
    
    DAY = (
        ('a.m.', 'a.m.'),
        ('p.m.', 'p.m.')
    )

    class Meta:
        model = PrintingSchedule
        fields = ('job_order', 'machine', 'number_rolls', 'time_in','day_in', 'time_out','day_out',
        'exit_scrap','printing_scrap', 'remarks')
        # widgets = {
        # 'time_in': TimeInput(),
        # 'time_out': TimeInput()
        # }

    day_in = forms.CharField(widget = forms.Select(choices=DAY))
    time_in = forms.TimeField(widget = forms.TimeInput(format=['%H:%M']))
    day_out = forms.CharField(widget = forms.Select(choices=DAY))
    time_out = forms.TimeField(widget = forms.TimeInput(format=['%H:%M']))
    remarks = forms.CharField(widget = forms.Textarea(attrs={'rows':'3'}))
    machine = forms.ModelChoiceField(queryset=Machine.objects.all())

    def __init__(self, *args, **kwargs):
        super(PrintingScheduleForm, self).__init__(*args, **kwargs)
        self.fields['remarks'].required = False

class CuttingScheduleForm(forms.ModelForm):
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
        fields = ('job_order', 'machine', 'line', 'time_in','day_in', 'time_out','day_out',
        'quantity', 'output_kilos', 'number_rolls', 'exit_scrap', 'cutting_scrap', 'remarks')
        # widgets = {
        #     'time_in': TimeInput(),
        #     'time_out': TimeInput()
        # }

    day_in = forms.CharField(widget = forms.Select(choices=DAY))
    time_in = forms.TimeField(widget = forms.TimeInput(format=['%H:%M']))
    day_out = forms.CharField(widget = forms.Select(choices=DAY))
    time_out = forms.TimeField(widget = forms.TimeInput(format=['%H:%M']))
    line = forms.CharField(max_length=200, label = 'line', widget = forms.Select(choices=LINE))
    remarks = forms.CharField(widget = forms.Textarea(attrs={'rows':'3'}))
    machine = forms.ModelChoiceField(queryset=Machine.objects.all())

    def __init__(self, *args, **kwargs):
        super(CuttingScheduleForm, self).__init__(*args, **kwargs)
        self.fields['remarks'].required = False
	
class JODetailsForm(forms.ModelForm):
    STATUS = (
        ('Waiting', 'Waiting'),
        ('On Queue', 'On Queue'),
        ('Under Cutting', 'Cutting'),
        ('Under Extrusion', 'Under Extrusion'),
        ('Under Printing', 'Under Printing'),
        ('Under Packaging', 'Under Packaging'),
        ('Ready for delivery', 'Ready for delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled')
    )
    
    class Meta:
        model = JobOrder
        fields = ('remarks',)

    remarks = forms.CharField(widget = forms.Textarea(attrs={'rows':'3'}))