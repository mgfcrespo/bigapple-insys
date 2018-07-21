from django.contrib import admin

from .models import Machine, WorkerSchedule, MachineSchedule, JobOrder
from .models import ExtruderSchedule, PrintingSchedule, CuttingSchedule

# Register your models here.

#production
admin.site.register(Machine)
admin.site.register(WorkerSchedule)
admin.site.register(MachineSchedule)
admin.site.register(JobOrder)
admin.site.register(ExtruderSchedule)
admin.site.register(PrintingSchedule)
admin.site.register(CuttingSchedule)
