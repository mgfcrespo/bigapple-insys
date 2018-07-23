from django.db import models

# Create your models here.
from django.db import models
from accounts.models import Employee
from sales.models import ClientPO, SalesInvoice
from inventory.models import SupplierRawMaterials

# from sales.models import OrderSheet
# Create your models here.


SHIFTS = (
    ('Shift 1', 'shift 1'),
    ('Shift 2', 'shift 2'),
    ('Shift 3', 'shift 3')
)


class Machine(models.Model):
    MACHINE_TYPE = (
        ('Cutting', 'Cutting'),
        ('Printing', 'Printing'),
        ('Extruder', 'Extruder')
    )

    machine_type = models.CharField('machine_type', choices=MACHINE_TYPE, max_length=200, default='not specified')
    machine_number = models.CharField('machine_number', max_length=10)

    def __str__(self):
        return self.machine_number

    def machine_name(self):
        return self.machine_number +' : ' + str(self.machine_type)

class WorkerSchedule(models.Model):
    worker = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    working_date = models.DateTimeField('working_date', auto_now_add=True, blank=True)

    def __str__(self):
        return self.worker.full_name

class MachineSchedule(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    job_task = models.CharField('job_task', max_length=200, default='none', blank=True)
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE, null=True)
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    working_date = models.DateField('working_date', auto_now_add=True, blank=True)
    operator = models.ForeignKey(WorkerSchedule, on_delete=models.CASCADE)

    def __str__(self):
        return self.machine.machine_type +' M'+ str(self.machine.machine_number) +' : ' + str(self.client_po)
    
class JobOrder(models.Model):
    STATUS = (
        ('Waiting', 'Waiting'),
        ('On Queue', 'On Queue'),
        ('Under Cutting', 'Under Cutting'),
        ('Under Extrusion', 'Under Extrusion'),
        ('Under Printing', 'Under Printing'),
        ('Under Packaging', 'Under Packaging'),
        ('Ready for delivery', 'Ready for delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled')
    )

    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    rush_order = models.BooleanField(default=False)
    status = models.CharField('status', choices=STATUS, max_length=200, default="Waiting")
    remarks = models.CharField('remarks', max_length=250, default="", blank=True)

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        jo_number = 'JO_%s' % (lead_zero)
        return jo_number

    def job_order(self):
        jo = str(self.id).zfill(5)
        return jo

class ExtruderSchedule(models.Model):
    SHIFTS = (
        ('Shift 1', 'shift 1'),
        ('Shift 2', 'shift 2'),
        ('Shift 3', 'shift 3')
    )
    
    DAY = (
        ('a.m.', 'a.m.'),
        ('p.m.', 'p.m.')
    )

    job_order = models.ForeignKey(JobOrder, on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    operator = models.ForeignKey(Employee, on_delete=models.CASCADE)
    #stock_kind = models.CharField('stock_kind',choices=STOCK_KIND, max_length=250, default='not specified')
    #material = models.CharField('material', max_length=200)
    #treating = models.CharField('treating', max_length=200)
    date = models.DateField('date', auto_now_add=True, blank=True)
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    day = models.CharField('day', choices=DAY, max_length=200, default='a.m.')
    time_in = models.TimeField('time_in', blank=True)
    time_out = models.TimeField('time_out', auto_now_add=True, blank=True)
    weight_rolls = models.DecimalField('weight_rolls', decimal_places=2, max_digits=12, null=True, blank=True)
    core_weight = models.DecimalField('core_weight', decimal_places=2, max_digits=12, null=True, blank=True)
    net_weight = models.DecimalField('net_weight', decimal_places=2, max_digits=12, null=True, blank=True)  # idk if necessary
    output_kilos = models.DecimalField('output_kilos', decimal_places=2, max_digits=12, null=True, blank=True)
    number_rolls = models.DecimalField('number_rolls', decimal_places=2, max_digits=12, null=True, blank=True)
    starting_scrap = models.DecimalField('starting_scrap', decimal_places=2, max_digits=12, null=True, blank=True)
    extruder_scrap = models.DecimalField('extruder_scrap', decimal_places=2, max_digits=12, null=True, blank=True)
    balance = models.DecimalField('balance', decimal_places=2, max_digits=12, null=True, blank=True)
    remarks = models.CharField('remarks', max_length=1000, null=True, blank=True)

    def __str__(self):
        data = str(self.job_order) + ' : ' + str(self.id) + ' : ' + str(self.operator.full_name)
        return data + ' : ' + str(self.date)

    def time_in_day(self):
        return str(self.time_in) + ' : ' + str(self.day)


class PrintingSchedule(models.Model):
    SHIFTS = (
        ('Shift 1', 'shift 1'),
        ('Shift 2', 'shift 2'),
        ('Shift 3', 'shift 3')
    )
    
    DAY = (
        ('a.m.', 'a.m.'),
        ('p.m.', 'p.m.')
    )

    job_order = models.ForeignKey(JobOrder, on_delete=models.CASCADE, null=True)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    operator = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField('date', auto_now_add=True, blank=True)
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    day = models.CharField('day', choices=DAY, max_length=200, default='a.m.')
    time_in = models.TimeField('time_in', blank=True)
    time_out = models.TimeField('time_out', auto_now_add=True, blank=True)
    #repeat_order = models.BooleanField('repeat_order', default=False)
    #output_kilos = models.DecimalField('output_kilos', decimal_places=2, max_digits=12)
    number_rolls = models.DecimalField('number_rolls', decimal_places=2, max_digits=12)
    exit_scrap = models.DecimalField('exit_scrap', decimal_places=2, max_digits=12)
    printing_scrap = models.DecimalField('printing_scrap', decimal_places=2, max_digits=12)
    remarks = models.CharField('remarks', max_length=1000, null=True, blank=True)

    def __str__(self):
        data = str(self.job_order) + ' : ' + str(self.id) + ' : ' + str(self.operator.full_name)
        return data + ' : ' + str(self.date)

    def time_in_day(self):
        return str(self.time_in) + ' : ' + str(self.day)

class CuttingSchedule(models.Model):
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

    job_order = models.ForeignKey(JobOrder, on_delete=models.CASCADE, null=True)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    operator = models.ForeignKey(Employee, on_delete=models.CASCADE)
    #print_name = models.CharField('print_name', max_length=200)
    #sealing = models.CharField('sealing', max_length=200)
    #handle = models.CharField('handle', max_length=200)
    date = models.DateField('date', auto_now_add=True, blank=True)
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    day = models.CharField('day', choices=DAY, max_length=200, default='a.m.')
    time_in = models.TimeField('time_in', blank=True)
    time_out = models.TimeField('time_out', auto_now_add=True, blank=True)
    line = models.CharField('line', choices=LINE, default='1', max_length=200)
    quantity = models.DecimalField('quantity', decimal_places=2, max_digits=12)
    output_kilos = models.DecimalField('output_kilos', decimal_places=2, max_digits=12, null=True, blank=True)
    number_rolls = models.DecimalField('number_rolls', decimal_places=2, max_digits=12, null=True, blank=True)
    exit_scrap = models.DecimalField('exit_scrap', decimal_places=2, max_digits=12, null=True, blank=True)
    cutting_scrap = models.DecimalField('cutting_scrap', decimal_places=2, max_digits=12, null=True, blank=True)
    remarks = models.CharField('remarks', max_length=1000, null=True, blank=True)

    def __str__(self):
        data = str(self.job_order) + ' : ' + str(self.id) + ' : ' + str(self.operator.full_name)
        return data + ' : ' + str(self.date)

    def time_in_day(self):
        return str(self.time_in) + ' : ' + str(self.day)
