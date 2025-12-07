from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'start_date', 'end_date', 'format', 'generated_at', 'generated_by')
    list_filter = ('report_type', 'generated_at')
    search_fields = ('report_type', 'generated_by__email')
    ordering = ('-generated_at',)
    fieldsets = (
        ('Основные параметры', {
            'fields': ('report_type', 'start_date', 'end_date', 'format')
        }),
        ('Дополнительные фильтры', {
            'fields': ('category', 'employee')
        }),
        ('Информация о генерации', {
            'fields': ('generated_by', 'generated_at')
        }),
    )
    
    def get_report_type_display(self, obj):
        return obj.get_report_type_display()
    get_report_type_display.short_description = 'Тип отчета'