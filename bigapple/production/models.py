from django.db import models
from accounts.models import Employee
from sales.models import ClientPO

# from sales.models import OrderSheet
# Create your models here.


SHIFTS = (
    ('1', 'shift 1'),
    ('2', 'shift 2'),
    ('3', 'shift 3')
)


class Machine(models.Model):
    MACHINE_TYPE = (
        ('C', 'Cutting'),
        ('P', 'Printing'),
        ('E', 'Extruder')
    )

    machine_type = models.CharField('machine_type', choices=MACHINE_TYPE, max_length=200, default='not specified')
    machine_number = models.CharField('machine_number', max_length=10)

# might be transferred to sales
class SalesInvoice(models.Model):
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    article = models.CharField('article', max_length=200, default='none', blank=True)
    vat = models.DecimalField('vat', default=0.0, blank=True, decimal_places=3, max_digits=12)
    date_paid = models.DateField('date_paid', auto_now_add=True, blank=True)
    payment_type = models.CharField('payment_type', max_length=200, default='none')


class WorkerSchedule(models.Model):
    worker = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    working_date = models.DateField('working_date')


class MachineSchedule(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    job_task = models.CharField('job_task', max_length=200, default='none', blank=True)
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE, null=True)
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    working_date = models.DateField('working_date', auto_now_add=True, blank=True)
    operator = models.ForeignKey(WorkerSchedule, on_delete=models.CASCADE)


'''    
class MaterialSchedule(models.Model):
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    rm_name = models.CharField('rm_name')
    rm_type = models.CharField('rm_type')
    quantity = models.IntegerField('quantity')
'''


class PrintingSchedule(models.Model):
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    operator = models.ForeignKey(WorkerSchedule, on_delete=models.CASCADE)
    date = models.DateField('date')
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    time_in = models.TimeField('time_in')
    time_out = models.TimeField('time_out')
    repeat_order = models.BooleanField('repeat_order', default=True)
    output_kilos = models.DecimalField('output_kilos', decimal_places=3, max_digits=12)
    number_rolls = models.DecimalField('number_rolls', decimal_places=3, max_digits=12)
    starting_scrap = models.DecimalField('starting_scrap', decimal_places=3, max_digits=12)
    printing_scrap = models.DecimalField('printing_scrap', decimal_places=3, max_digits=12)
    remarks = models.CharField('remarks', max_length=1000)


class CuttingSchedule(models.Model):
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    operator = models.ForeignKey(WorkerSchedule, on_delete=models.CASCADE)
    print_name = models.CharField('print_name', max_length=200)
    sealing = models.CharField('sealing', max_length=200)
    handle = models.CharField('handle', max_length=200)
    date = models.DateField('date', auto_now_add=True, blank=True)
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    time_in = models.TimeField('time_in', auto_now_add=True, blank=True)
    time_out = models.TimeField('time_out', auto_now_add=True, blank=True)
    line = models.CharField('line', default='1', max_length=200)
    quantity = models.DecimalField('quantity', decimal_places=3, max_digits=12)
    output_kilos = models.DecimalField('output_kilos', decimal_places=3, max_digits=12)
    number_rolls = models.DecimalField('number_rolls', decimal_places=3, max_digits=12)
    starting_scrap = models.DecimalField('starting_scrap', decimal_places=3, max_digits=12)
    cutting_scrap = models.DecimalField('cutting_scrap', decimal_places=3, max_digits=12)
    remarks = models.CharField('remarks', max_length=1000)


class ExtruderSchedule(models.Model):
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    operator = models.ForeignKey(WorkerSchedule, on_delete=models.CASCADE)
    stock_kind = models.CharField('stock_kind', max_length=250)
    material = models.CharField('material', max_length=200)
    treating = models.CharField('treating', max_length=200)
    date = models.DateField('date', auto_now_add=True, blank=True)
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    time_in = models.TimeField('time_in', auto_now_add=True, blank=True)
    time_out = models.TimeField('time_out', auto_now_add=True, blank=True)
    weight_rolls = models.DecimalField('weight_rolls', decimal_places=3, max_digits=12)
    core_weight = models.DecimalField('core_weight', decimal_places=3, max_digits=12)
    net_weight = models.DecimalField('net_weight', decimal_places=3, max_digits=12)  # idk if necessary
    output_kilos = models.DecimalField('output_kilos', decimal_places=3, max_digits=12)
    number_rolls = models.DecimalField('number_rolls', decimal_places=3, max_digits=12)
    starting_scrap = models.DecimalField('starting_scrap', decimal_places=3, max_digits=12)
    extruder_scrap = models.DecimalField('extruder_scrap', decimal_places=3, max_digits=12)
    remarks = models.CharField('remarks', max_length=1000)


class JobOrder(models.Model):
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    status = models.CharField('status', max_length=100)
    remarks = models.CharField('remarks', max_length=250)
    extruder_schedule = models.ForeignKey(ExtruderSchedule, on_delete=models.CASCADE)
    printing_schedule = models.ForeignKey(PrintingSchedule, on_delete=models.CASCADE)
    cutting_schedule = models.ForeignKey(CuttingSchedule, on_delete=models.CASCADE)