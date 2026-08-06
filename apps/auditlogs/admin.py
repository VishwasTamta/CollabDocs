from django.contrib import admin
from .models import AuditLog


class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'actor', 'action', 'model_name', 'object_id', 'timestamp')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('actor__first_name', 'actor__last_name', 'action', 'model_name', 'object_id')

admin.site.register(AuditLog, AuditLogAdmin)
