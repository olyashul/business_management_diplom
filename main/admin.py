from django.contrib import admin
from .models import Task, Shift

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_completed', 'date', 'user')
    list_filter = ('is_completed', 'user')

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'start_time', 'end_time')
    list_filter = ('date', 'user')
