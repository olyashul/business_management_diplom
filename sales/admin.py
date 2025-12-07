from django.contrib import admin
from .models import Sale, SaleItem, DailyStats


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    fields = ('product', 'quantity', 'selling_price', 'total_price')
    readonly_fields = ('total_price',)

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('sale_number', 'total_amount', 'final_amount', 
                   'payment_method', 'created_at', 'is_return')
    list_filter = ('is_return', 'payment_method', 'created_at', 'is_completed')
    search_fields = ('sale_number', 'notes')
    ordering = ('-created_at',)
    inlines = [SaleItemInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('sale_number', 'created_by')
        }),
        ('Финансы', {
            'fields': ('total_amount', 'discount', 'final_amount', 'payment_method')
        }),
        ('Статус', {
            'fields': ('is_completed', 'is_return')
        }),
        ('Дополнительно', {
            'fields': ('notes', 'created_at')
        }),
    )
    readonly_fields = ('created_at', 'total_amount', 'final_amount')

@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_sales', 'total_amount', 'average_check', 'total_profit')
    list_filter = ('date',)
    readonly_fields = ('date', 'total_sales', 'total_amount', 'average_check', 'total_profit')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False