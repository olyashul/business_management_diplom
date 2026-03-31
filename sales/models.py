from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import ManagementUser
from products.models import Product
from django.utils import timezone
from products.models import Product, StockMovement

class Sale(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Наличные'),
        ('card', 'Карта'),
        ('transfer', 'Перевод'),
        ('mixed', 'Смешанная оплата'),
    ]
    
    # Информация о продаже
    sale_number = models.CharField(max_length=20, unique=True, verbose_name="Номер чека")
    
    # Финансы
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Сумма чека", default=0, validators=[MinValueValidator(0)])
    discount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Скидка", default=0)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Итоговая сумма", default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash', verbose_name="Способ оплаты")
    
    # Статус
    is_completed = models.BooleanField(default=True, verbose_name="Завершена")
    is_return = models.BooleanField(default=False, verbose_name="Возврат")
    
    # Системные поля
    created_by = models.ForeignKey(ManagementUser, on_delete=models.SET_NULL, null=True, verbose_name="Кем создана")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата продажи")
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(verbose_name="Примечания", blank=True)
    
    class Meta:
        verbose_name = "Продажа"
        verbose_name_plural = "Продажи"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sale_number']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Автоматическая генерация номера чека
        if not self.sale_number:
            date_str = timezone.now().strftime('%Y%m%d')
            last_sale = Sale.objects.filter(sale_number__startswith=date_str).order_by('sale_number').last()
            if last_sale:
                last_num = int(last_sale.sale_number[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.sale_number = f"{date_str}{new_num:04d}"
        
        # Рассчитываем final_amount перед сохранением
        # Приводим к Decimal для корректного вычитания
        from decimal import Decimal
        total_amount = Decimal(str(self.total_amount)) if self.total_amount else Decimal('0')
        discount = Decimal(str(self.discount)) if self.discount else Decimal('0')
        self.final_amount = total_amount - discount
        
        super().save(*args, **kwargs)
    
    def update_totals(self):
        """Обновить суммы продажи из товаров"""
        from django.db.models import Sum
        from decimal import Decimal
        
        # Считаем сумму всех товаров в чеке
        total = self.items.aggregate(
            total=Sum('total_price')
        )['total'] or Decimal('0')
        
        # Обновляем объект
        self.total_amount = total
        # Приводим discount к Decimal
        discount_decimal = Decimal(str(self.discount)) if self.discount else Decimal('0')
        self.final_amount = total - discount_decimal
        
        # Сохраняем только нужные поля, чтобы не вызывать полный save()
        Sale.objects.filter(id=self.id).update(
            total_amount=self.total_amount,
            final_amount=self.final_amount
        )
    
    def __str__(self):
        status = "Возврат" if self.is_return else "Продажа"
        return f"Чек #{self.sale_number} - {self.final_amount} ₽ ({status})"
    
    @property
    def item_count(self):
        return self.items.count()
    
    @property
    def profit(self):
        profit = 0
        for item in self.items.all():
            if item.product:
                profit += (item.selling_price - item.product.purchase_price) * item.quantity
        return profit
    
    @property
    def date_only(self):
        return self.created_at.date()
    
    @property
    def time_only(self):
        return self.created_at.time()
    
    
class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items', verbose_name="Продажа")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sale_items', verbose_name="Товар")
    quantity = models.IntegerField(verbose_name="Количество") 
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена продажи", validators=[MinValueValidator(0)])
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Закупочная цена", validators=[MinValueValidator(0)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма", default=0)
    
    class Meta:
        verbose_name = "Товар в чеке"
        verbose_name_plural = "Товары в чеке"

    def save(self, *args, **kwargs):
        # Определяем, новая ли запись
        is_new = self.pk is None
        
        # Рассчитываем общую сумму (используем абсолютное значение)
        self.total_price = self.selling_price * abs(self.quantity)
        
        # Сохраняем закупочную цену из товара
        if self.product and not self.purchase_price:
            self.purchase_price = self.product.purchase_price
        
        # Сохраняем объект
        super().save(*args, **kwargs)
        
        # Обновляем остатки товара ТОЛЬКО для новых записей
        if self.product and is_new:
            # Для продажи (не возврат) уменьшаем количество
            if not self.sale.is_return:
                self.product.quantity -= abs(self.quantity)
                movement_type = 'outgoing'
                comment = f"Продажа #{self.sale.sale_number}"
            # Для возврата увеличиваем количество
            else:
                self.product.quantity += abs(self.quantity)
                movement_type = 'return'
                comment = f"Возврат #{self.sale.sale_number}"
            
            self.product.save()
            
            # Создаем запись о движении товара
            StockMovement.objects.create(
                product=self.product,
                movement_type=movement_type,
                quantity=abs(self.quantity),
                previous_quantity=self.product.quantity + (abs(self.quantity) if movement_type == 'outgoing' else -abs(self.quantity)),
                new_quantity=self.product.quantity,
                comment=comment,
                created_by=self.sale.created_by
            )

    def delete(self, *args, **kwargs):
        # При удалении товара из чека возвращаем товар на склад
        if self.product:
            if not self.sale.is_return:
                self.product.quantity += abs(self.quantity)
                movement_type = 'return'
                comment = f"Отмена продажи #{self.sale.sale_number}"
            else:
                self.product.quantity -= abs(self.quantity)
                movement_type = 'outgoing'
                comment = f"Отмена возврата #{self.sale.sale_number}"
            
            self.product.save()
            
            StockMovement.objects.create(
                product=self.product,
                movement_type=movement_type,
                quantity=abs(self.quantity),
                previous_quantity=self.product.quantity - (abs(self.quantity) if movement_type == 'return' else -abs(self.quantity)),
                new_quantity=self.product.quantity,
                comment=comment,
                created_by=self.sale.created_by
            )

        super().delete(*args, **kwargs)
        
class DailyStats(models.Model):
    date = models.DateField(unique=True, verbose_name="Дата")
    total_sales = models.IntegerField(default=0, verbose_name="Количество чеков")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Общая выручка")
    average_check = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Средний чек")
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0,verbose_name="Прибыль")
    
    class Meta:
        verbose_name = "Статистика за день"
        verbose_name_plural = "Статистика по дням"
        ordering = ['-date']
    
    def __str__(self):
        return f"Статистика за {self.date}: {self.total_amount} ₽"
    
    def update_stats(self):
        from django.db.models import Sum, Count
        
        sales = Sale.objects.filter(
            created_at__date=self.date,
            is_completed=True,
            is_return=False
        )
        
        self.total_sales = sales.count()
        self.total_amount = sales.aggregate(total=Sum('final_amount'))['total'] or 0
        
        if self.total_sales > 0:
            self.average_check = self.total_amount / self.total_sales
        
        profit = 0
        for sale in sales:
            profit += sale.profit
        self.total_profit = profit
        
        self.save()