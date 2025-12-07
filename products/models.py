from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from accounts.models import ManagementUser
import os

class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название поставщика")
    contact_person = models.CharField(max_length=100, verbose_name="Контактное лицо", blank=True)
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    email = models.EmailField(verbose_name="Email", blank=True)
    address = models.TextField(verbose_name="Адрес", blank=True)
    inn = models.CharField(max_length=12, verbose_name="ИНН", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL", blank=True)
    description = models.TextField(verbose_name="Описание", blank=True)
    image = models.ImageField(upload_to='categories/', verbose_name="Изображение", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    # Основная информация
    sku = models.CharField(max_length=50, unique=True, verbose_name="Артикул")
    name = models.CharField(max_length=200, verbose_name="Наименование товара")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL", blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name="Категория")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL,  null=True, blank=True, verbose_name="Поставщик")
    
    # Описание
    description = models.TextField(verbose_name="Описание", blank=True)
    short_description = models.TextField(max_length=500, verbose_name="Краткое описание", blank=True)
    
    # Цены
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Закупочная цена", validators=[MinValueValidator(0)], default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Розничная цена", validators=[MinValueValidator(0)], default=0)
    markup_percentage = models.DecimalField(max_digits=5, decimal_places=2,verbose_name="Наценка %", default=0)
    
    # Остатки
    quantity = models.IntegerField(default=0, verbose_name="Количество на складе")
    min_quantity = models.IntegerField(default=5, verbose_name="Минимальный остаток")
    is_active = models.BooleanField(default=True, verbose_name="Активный")
    
    # Системные поля
    created_by = models.ForeignKey(ManagementUser, on_delete=models.SET_NULL, null=True, verbose_name="Создал")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Автоматически генерируем slug
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.sku}")
        
        # Автоматически рассчитываем наценку при сохранении
        if self.purchase_price and self.selling_price and self.purchase_price > 0:
            self.markup_percentage = ((self.selling_price - self.purchase_price) / self.purchase_price) * 100
        
        super().save(*args, **kwargs)

    @property
    def total_value(self):
        return self.quantity * self.purchase_price

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_quantity

    def __str__(self):
        return f"{self.name} ({self.sku})"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Товар")
    image = models.ImageField(upload_to='products/', verbose_name="Изображение")
    is_main = models.BooleanField(default=False, verbose_name="Основное изображение")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товаров"
        ordering = ['order']

    def __str__(self):
        return f"Изображение для {self.product.name}"


class ProductAttribute(models.Model):
    """Дополнительные характеристики товаров"""
    name = models.CharField(max_length=100, verbose_name="Название характеристики")
    code = models.SlugField(max_length=50, unique=True, verbose_name="Код характеристики")
    unit = models.CharField(max_length=20, verbose_name="Единица измерения", blank=True)
    
    class Meta:
        verbose_name = "Характеристика товара"
        verbose_name_plural = "Характеристики товаров"

    def __str__(self):
        if self.unit:
            return f"{self.name} ({self.unit})"
        return self.name


class ProductAttributeValue(models.Model):
    """Значения характеристик для товаров"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes', verbose_name="Товар")
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE,  verbose_name="Характеристика")
    value = models.CharField(max_length=200, verbose_name="Значение")
    
    class Meta:
        verbose_name = "Значение характеристики"
        verbose_name_plural = "Значения характеристик"
        unique_together = ['product', 'attribute']

    def __str__(self):
        return f"{self.attribute.name}: {self.value} для {self.product.name}"


class StockMovement(models.Model):
    """Движение товаров на складе"""
    MOVEMENT_TYPES = [
        ('incoming', 'Приход'),
        ('outgoing', 'Расход'),
        ('adjustment', 'Корректировка'),
        ('return', 'Возврат'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements', verbose_name="Товар")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES, verbose_name="Тип движения")
    quantity = models.IntegerField(verbose_name="Количество")
    previous_quantity = models.IntegerField(verbose_name="Предыдущий остаток")
    new_quantity = models.IntegerField(verbose_name="Новый остаток")
    comment = models.TextField(verbose_name="Комментарий", blank=True)
    created_by = models.ForeignKey(ManagementUser, on_delete=models.SET_NULL, null=True, verbose_name="Кем создано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата движения")
    
    sale_item = models.ForeignKey('sales.SaleItem', on_delete=models.SET_NULL,  null=True, blank=True, verbose_name="Товар в чеке")
    class Meta:
        verbose_name = "Движение товара"
        verbose_name_plural = "Движения товаров"
        ordering = ['-created_at']
    def __str__(self):
        return f"{self.get_movement_type_display()} {self.product.name} ({self.quantity})"
