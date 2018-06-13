from django.db import models
from accounts.models import Employee
from sales.models import ClientPO
#from sales.models import OrderSheet
# Create your models here.


class Machine(models.Model):
    MACHINE_TYPE = (
        ('C', 'Cutting'),
        ('P', 'Printing'),
        ('E', 'Extruder')
    )

    machine_type =  models.CharField('machine_type', choices=MACHINE_TYPE, max_length=200, default='not specified')
    machine_number = models.CharField('machine_number', max_length=10)

#might be transferred to sales
class SalesInvoice(models.Model):
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    article = models.CharField('article', max_length=200, default='none', blank=True)
    vat = models.DecimalField('vat', default=0, blank=True, decimal_places=3, max_digits=12)
    date_paid = models.DateField('date_paid')
    payment_type = models.CharField('payment_type', max_length=200, default='none')


class WorkerSchedule(models.Model):
    SHIFTS = (
        ('1', 'shift 1'),
        ('2', 'shift 2'),
        ('3', 'shift 3')
    )

    worker = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    working_date = models.DateField('working_date')

class MachineSchedule(models.Model):
    SHIFTS = (
        ('1', 'shift 1'),
        ('2', 'shift 2'),
        ('3', 'shift 3')
    )
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    job_task = models.CharField('job_task')
    client_po = models.CharField('client_po')
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    working_date = models.DateField('working_date')
    operator = models.CharField('operator', max_length=200)

'''    
class MaterialSchedule(models.Model):
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    rm_name = models.CharField('rm_name')
    rm_type = models.CharField('rm_type')
    quantity = models.IntegerField('quantity')
'''

class PrintingSchedule(models.Model):
    SHIFTS = (
        ('1', 'shift 1'),
        ('2', 'shift 2'),
        ('3', 'shift 3')
    )

    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    machine = models.IntegerField('machine')
    operator = models.CharField('operator', max_length=200)
    date = models.DateField('date')
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    time_in = models.TimeField('time_in')
    time_out = models.TimeField('time_out')
    repeat_order = models.BooleanField('repeat_order', default='true')
    output_kilos = models.FloatField('output_kilos')
    number_rolls = models.FloatField('number_rolls')
    starting_scrap = models.FloatField('starting_scrap')
    printing_scrap = models.FloatField('printing_scrap')
    remarks = models.CharField('remarks', max_length=1000)

class CuttingSchedule(models.Model):
    SHIFTS = (
        ('1', 'shift 1'),
        ('2', 'shift 2'),
        ('3', 'shift 3')
    )

    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    print_name = models.CharField('print_name')
    sealing = models.CharField('sealing')
    handle = models.CharField('handle')
    machine = models.IntegerField('machine')
    operator = models.CharField('operator', max_length=200)
    date = models.DateField('date')
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    time_in = models.TimeField('time_in')
    time_out = models.TimeField('time_out')
    line = models.IntegerField('line', min_length=1)
    quantity = models.FloatField('quantity')
    output_kilos = models.FloatField('output_kilos')
    number_rolls = models.FloatField('number_rolls')
    starting_scrap = models.FloatField('starting_scrap')
    cutting_scrap = models.FloatField('cutting_scrap')
    remarks = models.CharField('remarks', max_length=1000)

class ExtruderSchedule(models.Model):
    SHIFTS = (
        ('1', 'shift 1'),
        ('2', 'shift 2'),
        ('3', 'shift 3')
    )

    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    stock_kind = models.CharField('stock_kind', max_length=250)
    material = models.CharField('material', max_length=200)
    treating = models.CharField('treating', max_length=200)
    machine = models.IntegerField('machine')
    operator = models.CharField('operator', max_length=200)
    date = models.DateField('date')
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    time_in = models.TimeField('time_in')
    time_out = models.TimeField('time_out')
    output_kilos = models.FloatField('output_kilos')
    number_rolls = models.FloatField('number_rolls')
    weight_rolls = models.FloatField('weight_rolls')
    core_weight = models.FloatField('core_weight')
    net_weight = models.FloatField('net_weight') # idk if necessary
    starting_scrap = models.FloatField('starting_scrap')
    extruder_scrap = models.FloatField('extruder_scrap')
    remarks = models.CharField('remarks', max_length=1000)










