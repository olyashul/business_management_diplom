from django.contrib import admin
from .models import Employee, WorkShift, WorkTimeRecord

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'position', 'hire_date', 'phone', 'is_active')
    list_filter = ('position', 'is_active', 'hire_date')
    search_fields = ('first_name', 'last_name', 'middle_name', 'phone', 'email')
    ordering = ('last_name', 'first_name')
    fieldsets = (
        ('Основная информация', {
            'fields': ('first_name', 'last_name', 'middle_name', 'position', 'birth_date')
        }),
        ('Контакты', {
            'fields': ('phone', 'email', 'address')
        }),
        ('Работа', {
            'fields': ('hire_date', 'salary', 'is_active')
        }),
        ('Документы', {
            'fields': ('passport_data', 'notes')
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'ФИО'

@admin.register(WorkShift)
class WorkShiftAdmin(admin.ModelAdmin):
    list_display = ('date', 'get_person_name', 'start_time', 'end_time', 'get_position', 'is_active')
    list_filter = ('date', 'is_active', 'employee__position')
    search_fields = ('employee__first_name', 'employee__last_name', 'manager__first_name', 'manager__last_name')
    ordering = ('-date', 'start_time')
    fieldsets = (
        ('Основная информация', {
            'fields': ('date', 'start_time', 'end_time', 'is_active')
        }),
        ('Назначение', {
            'fields': ('employee', 'manager')
        }),
        ('Дополнительно', {
            'fields': ('notes',)
        }),
    )
    
    def get_person_name(self, obj):
        return obj.get_person_name()
    get_person_name.short_description = 'Сотрудник/Руководитель'
    
    def get_position(self, obj):
        return obj.get_position()
    get_position.short_description = 'Должность'

@admin.register(WorkTimeRecord)
class WorkTimeRecordAdmin(admin.ModelAdmin):
    list_display = ('work_shift', 'attendance_type', 'actual_start', 'actual_end', 'hours_worked', 'created_at')
    list_filter = ('attendance_type', 'work_shift__date')
    search_fields = ('work_shift__employee__first_name', 'work_shift__employee__last_name')
    ordering = ('-work_shift__date',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('work_shift', 'attendance_type')
        }),
        ('Фактическое время', {
            'fields': ('actual_start', 'actual_end', 'hours_worked', 'overtime_hours')
        }),
        ('Дополнительно', {
            'fields': ('notes',)
        }),
    )