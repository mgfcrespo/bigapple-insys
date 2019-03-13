from django import forms
from django.forms import ModelForm, ValidationError, Form, widgets, DateTimeInput
from decimal import Decimal
from django.contrib.admin.widgets import AdminDateWidget
from django.utils import formats
from datetime import date, datetime
from datetimepicker.widgets import DateTimePicker

from .models import ExtruderSchedule, PrintingSchedule, CuttingSchedule, LaminatingSchedule, Machine, Employee, JobOrder


class DateInput(forms.DateInput):
    input_type = 'date'


class ClientPOForm(forms.ModelForm):
    class Meta:
        model = JobOrder
        fields = ('date_required', 'remarks')
        widgets = {
            'date_required': DateInput(),
        }

        def __init__(self, *args, **kwargs):
            super(ClientPOForm, self).__init__(*args, **kwargs)
            self.fields['date_required'].required = True
            self.fields['date_required'].label = "Date Required"


class ExtruderScheduleForm(forms.ModelForm):
    SHIFTS = (
        (1, 1),
        (2, 2),
        (3, 3)
    )

    class Meta:
        model = ExtruderSchedule
        fields = ('job_order', 'machine', 'operator', 'weight_rolls', 'datetime_in', 'datetime_out', 'shift',
                  'core_weight', 'output_kilos', 'number_rolls', 'starting_scrap', 'extruder_scrap', 'remarks',
                  'final',)
        widgets = {
            'datetime_in': DateTimeInput(),
            'datetime_out': DateTimeInput(),
        }


    final = forms.BooleanField(initial=False, required=False)
    operator = forms.ModelChoiceField(queryset=Employee.objects.filter(position="Extruder"))

    def __init__(self, *args, **kwargs):
        super(ExtruderScheduleForm, self).__init__(*args, **kwargs)
        self.fields['remarks'].required = False

class PrintingScheduleForm(forms.ModelForm):
    SHIFTS = (
        (1, 1),
        (2, 2),
        (3, 3)
    )
    final = forms.BooleanField(initial=False, required=False)

    class Meta:
        model = PrintingSchedule
        fields = ('job_order', 'machine', 'operator', 'number_rolls', 'weight_rolls', 'core_weight', 'output_kilos',
        'datetime_in', 'datetime_out', 'shift',
        'starting_scrap', 'printing_scrap', 'remarks', 'final',)
        widgets = {
            'datetime_in': DateTimeInput(),
            'datetime_out': DateTimeInput()
        }

    operator = forms.ModelChoiceField(queryset=Employee.objects.filter(position="Printing"))

    def __init__(self, *args, **kwargs):
        super(PrintingScheduleForm, self).__init__(*args, **kwargs)
        self.fields['remarks'].required = False


class CuttingScheduleForm(forms.ModelForm):
    SHIFTS = (
        (1, 1),
        (2, 2),
        (3, 3)
    )

    LINE = (
        (1, 'Line 1'),
        (2, 'Line 2'),
        (3, 'Line 3')
    )

    final = forms.BooleanField(initial=False, required=False)
    operator = forms.ModelChoiceField(queryset=Employee.objects.filter(position="Cutting"))

    class Meta:
        model = CuttingSchedule
        fields = ('job_order', 'machine', 'operator', 'line', 'datetime_in', 'datetime_out', 'shift',
                  'quantity', 'output_kilos', 'number_rolls', 'starting_scrap', 'cutting_scrap', 'remarks', 'final',)
        widgets = {
            'datetime_in': DateTimeInput(),
            'datetime_out': DateTimeInput()
        }

    def __init__(self, *args, **kwargs):
        super(CuttingScheduleForm, self).__init__(*args, **kwargs)
        self.fields['remarks'].required = False


class LaminatingScheduleForm(forms.ModelForm):
    SHIFTS = (
        (1, 1),
        (2, 2),
        (3, 3)
    )

    final = forms.BooleanField(initial=False, required=False)
    operator = forms.ModelChoiceField(queryset=Employee.objects.filter(position="Cutting"))

    class Meta:
        model = LaminatingSchedule
        fields = ('job_order', 'machine', 'operator', 'datetime_in', 'datetime_out', 'shift', 'quantity',
        'starting_scrap', 'laminating_scrap', 'remarks', 'final')
        widgets = {
            'datetime_in': DateTimeInput(),
            'datetime_out': DateTimeInput()
        }


    def __init__(self, *args, **kwargs):
        super(LaminatingScheduleForm, self).__init__(*args, **kwargs)
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
        fields = ('remarks', 'status')

    remarks = forms.CharField(widget=forms.Textarea(attrs={'rows': '3'}))
