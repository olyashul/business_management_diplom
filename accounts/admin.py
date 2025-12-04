from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import ManagementUser


class ManagementUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'position', 'phone')
    list_filter = ('position', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'phone', 'position')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {
            'fields': ('first_name', 'last_name', 'middle_name', 'birth_date', 'phone')
        }),
        ('Рабочая информация', {
            'fields': ('position',)
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser',
                       'groups', 'user_permissions')
        }),
        ('Важные даты', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'birth_date',
                       'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Если вдруг появится поле username (наследуется от AbstractUser), отключаем его
        if 'username' in form.base_fields:
            form.base_fields['username'].disabled = True
        return form


admin.site.register(ManagementUser, ManagementUserAdmin)