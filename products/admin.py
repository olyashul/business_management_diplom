# products/admin.py
from django.contrib import admin
from .models import (
    Category, Supplier, Product, 
    ProductImage, ProductAttribute, 
    ProductAttributeValue, StockMovement
)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'is_main', 'order']
    readonly_fields = ['created_at']

class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1
    fields = ['attribute', 'value']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_count', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ['name']}
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Количество товаров'

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'email']
    search_fields = ['name', 'contact_person', 'phone']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'selling_price', 'quantity', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['sku', 'name', 'description']
    readonly_fields = ['markup_percentage', 'created_at', 'updated_at']
    inlines = [ProductImageInline, ProductAttributeValueInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('sku', 'name', 'category', 'supplier', 'is_active')
        }),
        ('Описание', {
            'fields': ('description', 'short_description')
        }),
        ('Цены и остатки', {
            'fields': ('purchase_price', 'selling_price', 'markup_percentage', 'quantity', 'min_quantity')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at', 'created_by')
        }),
    )

@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'unit']
    search_fields = ['name', 'code']
    prepopulated_fields = {'code': ['name']}

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'created_at', 'created_by']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'product__sku']
    readonly_fields = ['created_at']