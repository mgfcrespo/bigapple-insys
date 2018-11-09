from django.db import models
from decimal import Decimal
# Create your models here.
from django.db import models
from accounts.models import Employee
#from sales.models import ClientItem

from django.apps import apps

#ClientItem = apps.get_model('sales', 'ClientItem')
#Employee = apps.get_model('accounts', 'Employee')

class Machine(models.Model):
    MACHINE_TYPE = (
        ('Cutting', 'Cutting'),
        ('Printing', 'Printing'),
        ('Extruder', 'Extruder')
    )

    machine_type = models.CharField('machine_type', choices=MACHINE_TYPE, max_length=200, default='not specified')
    machine_id = models.IntegerField(primary_key=True)
    state = models.CharField(max_length=45)

    class Meta:
        db_table = 'production_mgt_machine'

    def __str__(self):
        return str(self.machine_id)

    '''
    def machine_name(self):
        return str(self.machine_type + " Machine #" + self.machine_number)
    '''

'''
class MachineState(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='machine')
    state = models.IntegerField('state', default=0)

'''
# class WorkerSchedule(models.Model):
#     worker = models.ForeignKey(Employee, on_delete=models.CASCADE)
#     shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
#     machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
#     working_date = models.DateTimeField('working_date', auto_now_add=True, blank=True)
#
#     def __str__(self):
#         return self.worker.full_name
#
# class MachineSchedule(models.Model):
#     machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
#     job_task = models.CharField('job_task', max_length=200, default='none', blank=True)
#     client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE, null=True)
#     shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
#     working_date = models.DateField('working_date', auto_now_add=True, blank=True)


#    def __str__(self):
#        return self.machine.machine_type +' M'+ str(self.machine.machine_number) +' : ' + str(self.client_po)


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


    status = models.CharField('status', choices=STATUS, max_length=200, default="Waiting")
    job_order = models.IntegerField(primary_key=True)
    remarks = models.CharField(max_length=45, blank=True, null=True)
    is_laminate = models.IntegerField()
    rush_order = models.IntegerField()
    date_issued = models.DateTimeField()
    date_required = models.DateTimeField()
    client = models.CharField(max_length=45)
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

class MachineSchedule(models.Model):
    job_order = models.ForeignKey(JobOrder, on_delete=models.CASCADE, null=True, related_name='machineschedule_job_order')
    job_task = models.CharField('job_task', max_length=200, default='Extruder', blank=True)
    duration = models.DurationField()
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='machineschedule_machine')

    def __str__(self):
        return str(self.id)

class ExtruderSchedule(models.Model):
    index = models.IntegerField(primary_key=True)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, db_column='machine')
    operator = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift = models.IntegerField()
    job_order = models.ForeignKey(JobOrder, on_delete=models.CASCADE, db_column='job_order')
    datetime_in = models.DateTimeField()
    datetime_out = models.DateTimeField()
    weight_rolls = models.FloatField()
    core_weight = models.FloatField()
    output_kilos = models.FloatField()
    number_rolls = models.FloatField()
    starting_scrap = models.FloatField()
    extruder_scrap = models.FloatField()
    remarks = models.CharField(max_length=45, blank=True, null=True)
    #item = models.ForeignKey(ClientItem, on_delete=models.CASCADE)

    class Meta:

        db_table = 'production_mgt_extruderschedule'


    def __str__(self):
        data = str(self.job_order) + ' : ' + str(self.id)
        return data + ' : ' + str(self.date)

    def save(self, *args, **kwargs):
        self.balance = self.weight_rolls* Decimal(4.74) 
        super(ExtruderSchedule, self).save(*args, **kwargs)

class PrintingSchedule(models.Model):
    index = models.IntegerField(primary_key=True)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, db_column='machine')
    operator = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift = models.IntegerField()
    job_order = models.ForeignKey(JobOrder, on_delete=models.CASCADE, db_column='job_order')
    datetime_in = models.DateTimeField()
    datetime_out = models.DateTimeField()
    weight_rolls = models.FloatField()
    core_weight = models.FloatField()
    output_kilos = models.FloatField()
    number_rolls = models.FloatField()
    starting_scrap = models.FloatField()
    printing_scrap = models.FloatField()
    remarks = models.CharField(max_length=45, blank=True, null=True)
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
    index = models.IntegerField(primary_key=True)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, db_column='machine')
    operator = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift = models.IntegerField()
    job_order = models.ForeignKey(JobOrder, on_delete=models.CASCADE, db_column='job_order')
    datetime_in = models.DateTimeField()
    datetime_out = models.DateTimeField()
    weight_rolls = models.FloatField()
    core_weight = models.FloatField()
    output_kilos = models.FloatField()
    number_rolls = models.FloatField()
    starting_scrap = models.FloatField()
    cutting_scrap = models.FloatField()
    remarks = models.CharField(max_length=45, blank=True, null=True)
    quantity = models.IntegerField()
    line = models.IntegerField()
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
    index = models.IntegerField(primary_key=True)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, db_column='machine')
    operator = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift = models.IntegerField()
    job_order = models.ForeignKey(JobOrder, on_delete=models.CASCADE, db_column='job_order')
    datetime_in = models.DateTimeField()
    datetime_out = models.DateTimeField()
    starting_scrap = models.FloatField()
    laminating_scrap = models.FloatField()
    remarks = models.CharField(max_length=45, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    #item = models.ForeignKey(ClientItem, on_delete=models.CASCADE)

    class Meta:

        db_table = 'production_mgt_laminatingschedule'
