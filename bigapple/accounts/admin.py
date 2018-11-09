from django.contrib import admin

from .models import Client, Employee, AgentClientRel
# Register your models here.

admin.site.register(Client)
admin.site.register(Employee)
admin.site.register(AgentClientRel)
