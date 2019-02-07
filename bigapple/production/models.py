from django.db import models
from decimal import Decimal
# Create your models here.
from django.db import models
from accounts.models import Employee, Client
#from sales.models import ClientItem
from datetime import date, timedelta, datetime

from django.apps import apps

#ClientItem = apps.get_model('sales', 'ClientItem')
#Employee = apps.get_model('accounts', 'Employee')

class Machine(models.Model):
    MACHINE_TYPE = (
        ('Cutting', 'Cutting'),
        ('Printing', 'Printing'),
        ('Extruder', 'Extruder'),
        ('Laminating', 'Laminating')
    )

    MACHINE_STATE = (
        ('OK', 'OK'),
        ('Defective', 'Defective'),
        ('Under Maintenance', 'Under Maintenance')

    )

    machine_type = models.CharField('machine_type', choices=MACHINE_TYPE, max_length=200, default='not specified')
    machine_id = models.IntegerField(primary_key=True)
    state = models.CharField('machine_type', choices=MACHINE_STATE, max_length=200, default='not specified')

    class Meta:
        db_table = 'production_mgt_machine'

    def __str__(self):
        return str(self.machine_id)

class JobOrder(models.Model):
    STATUS = (
        ('Waiting', 'Waiting'),
        ('On Queue', 'On Queue'),
        ('Under Cutting', 'Under Cutting'),
        ('Under Extrusion', 'Under Extrusion'),
        ('Under Printing', 'Under Printing'),
        ('Under Laminating', 'Under Laminating'),
        ('Under Packaging', 'Under Packaging'),
        ('Ready for delivery', 'Ready for delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled')
    )

    status = models.CharField('status', choices=STATUS, max_length=200, default="Waiting")
    job_order = models.IntegerField(primary_key=True)
    remarks = models.CharField(max_length=45, blank=True, null=True)
    rush_order = models.IntegerField()
    date_issued = models.DateField('date_issued', auto_now_add=True)
    date_required = models.DateField()
    client = models.ForeignKey(Client, on_delete= models.CASCADE)
    total_amount = models.FloatField()

    class Meta:

        db_table = 'production_mgt_joborder'

    def __str__(self):
        lead_zero = str(self.id).zfill(5)
        jo_number = 'JO_%s' % (lead_zero)
        return jo_number

    def job_order(self):
        jo = str(self.id).zfill(5)
        return jo

    def calculate_leadtime(self):
        date1 = date.today()
        date2 = self.date_required
        days = (date2 - date1).days
        return days

    def rush_order_determinant(self):
        if self.calculate_leadtime() <= 12:
            self.rush_order = True
        else:
            self.rush_order = False

        return self.rush_order

    def save(self, *args, **kwargs):
        rush_order = self.rush_order_determinant()
        self.rush_order = rush_order
        super(JobOrder, self).save(*args, **kwargs)

'''
class MachineSchedule(models.Model):
    job_order = models.ForeignKey(JobOrder, on_delete=models.CASCADE, null=True, related_name='machineschedule_job_order')
    job_task = models.CharField('job_task', max_length=200, default='Extruder', blank=True)
    duration = models.DurationField()
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='machineschedule_machine')

    def __str__(self):
        return str(self.id)
'''

class ExtruderSchedule(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    operator = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift = models.IntegerField(blank=True, null=True)
    job_order = models.ForeignKey(JobOrder, on_delete=models.CASCADE)
    datetime_in = models.DateTimeField()
    datetime_out = models.DateTimeField()
    weight_rolls = models.FloatField()
    core_weight = models.FloatField()
    output_kilos = models.FloatField()
    number_rolls = models.FloatField()
    starting_scrap = models.FloatField()
    extruder_scrap = models.FloatField()
    balance = models.FloatField
    remarks = models.CharField(max_length=45, blank=True, null=True)
    final = models.BooleanField(blank=True, null=True)
    #item = models.ForeignKey(ClientItem, on_delete=models.CASCADE)

    class Meta:
        db_table = 'production_mgt_extruderschedule'


    def __str__(self):
        data = str(self.job_order) + ' : ' + str(self.id)
        return data + ' : ' + str(self.date)

    def save(self, *args, **kwargs):
        self.balance = self.weight_rolls* float(4.74)
        super(ExtruderSchedule, self).save(*args, **kwargs)

class PrintingSchedule(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    operator = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift = models.IntegerField(blank=True, null=True)
    job_order = models.ForeignKey(JobOrder, on_delete=models.CASCADE)
    datetime_in = models.DateTimeField()
    datetime_out = models.DateTimeField()
    weight_rolls = models.FloatField()
    core_weight = models.FloatField()
    output_kilos = models.FloatField()
    number_rolls = models.FloatField()
    starting_scrap = models.FloatField()
    printing_scrap = models.FloatField()
    remarks = models.CharField(max_length=45, blank=True, null=True)
    final = models.BooleanField(blank=True, null=True)
   #item = models.ForeignKey(ClientItem, on_delete=models.CASCADE)

    class Meta:

        db_table = 'production_mgt_printingschedule'
    def __str__(self):
        data = str(self.job_order) + ' : ' + str(self.id)
        return data + ' : ' + str(self.date)

    def time_in_day(self):
        return str(self.time_in) + ' : ' + str(self.day_in)

    def time_out_day(self):
        return str(self.time_out) + ' : ' + str(self.day_out)

class CuttingSchedule(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    operator = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift = models.IntegerField(blank=True, null=True)
    job_order = models.ForeignKey(JobOrder, on_delete=models.CASCADE)
    datetime_in = models.DateTimeField()
    datetime_out = models.DateTimeField()
    output_kilos = models.FloatField()
    number_rolls = models.FloatField()
    starting_scrap = models.FloatField()
    cutting_scrap = models.FloatField()
    remarks = models.CharField(max_length=45, blank=True, null=True)
    quantity = models.IntegerField()
    line = models.IntegerField()
    final = models.BooleanField(blank=True, null=True)
    #item = models.ForeignKey(ClientItem, on_delete=models.CASCADE)

    class Meta:
        db_table = 'production_mgt_cuttingschedule'

    def __str__(self):
        data = str(self.job_order) + ' : ' + str(self.id)
        return data + ' : ' + str(self.date)

    def time_in_day(self):
        return str(self.time_in) + ' : ' + str(self.day_in)

    def time_out_day(self):
        return str(self.time_out) + ' : ' + str(self.day_out)

class LaminatingSchedule(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    operator = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift = models.IntegerField(blank=True, null=True)
    job_order = models.ForeignKey(JobOrder, on_delete=models.CASCADE)
    datetime_in = models.DateTimeField()
    datetime_out = models.DateTimeField()
    starting_scrap = models.FloatField()
    laminating_scrap = models.FloatField()
    remarks = models.CharField(max_length=45, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    final = models.BooleanField(blank=True, null=True)
    #item = models.ForeignKey(ClientItem, on_delete=models.CASCADE)

    class Meta:
        db_table = 'production_mgt_laminatingschedule'
