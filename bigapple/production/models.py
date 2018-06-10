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


class WorkerSchedule(models.Model):
    SHIFTS = (
        ('1', 'shift 1'),
        ('2', 'shift 2'),
        ('3', 'shift 3')
    )
    workers = models.ForeignKey(Employee, on_delete=models.CASCADE)
    shift = models.CharField('shift', choices=SHIFTS, max_length=200, default='not specified')
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    working_date = models.DateField('working_date')

#might be transferred to sales
class SalesInvoice(models.Model):
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    article = models.CharField('article', max_length=200, default='none', blank=True)
    vat = models.DecimalField('vat', default=0, blank=True, decimal_places=3, max_digits=12)
    date_paid = models.DateField('date_paid')
    payment_type = models.CharField('payment_type', max_length=200, default='none')

'''    
class MachineSchedule(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)

class CuttingSchedule(models.Model):
    
    
class PrintingSchedule(models.Model):
'''

class ExtruderSchedule(models.Model):
    client_po = models.ForeignKey(ClientPO, on_delete=models.CASCADE)
    jo_number = models.IntegerField('jo_number', min_length=6)
    stock_kind = models.CharField('stock_kind', max_length=250)
    kilos = models.FloatField('kilos')
    treating = models.CharField('treating', max_length=200);
    operator = models.CharField('operator', max_length=200)
    date = models.DateField('date')
    number_rolls = models.FloatField('number_rolls')
    weight_rolls = models.FloatField('weight_rolls')
    #core_weight, net_weight, str_scrap, ext_scrap, bal, remarks










