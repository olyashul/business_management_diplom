from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import datetime, date, timedelta
from accounts.models import ManagementUser
from products.models import Product, Category
from staff.models import Employee, WorkShift
from sales.models import Sale, SaleItem


class Report(models.Model):
    """Базовая модель отчета"""
    REPORT_TYPES = [
        ('financial', 'Финансовый отчет'),
        ('products', 'Отчет по товарам'),
        ('work_schedule', 'График работы'),
        ('daily', 'Отчет за день'),
    ]
    
    FORMATS = [
        ('excel', 'Excel'),
        # PDF и HTML убираем - слишком сложно для MVP
    ]
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, verbose_name="Тип отчета")
    start_date = models.DateField(verbose_name="Дата с")
    end_date = models.DateField(verbose_name="Дата по")
    format = models.CharField(max_length=10, choices=FORMATS, default='excel', verbose_name="Формат")
    
    # Параметры фильтрации
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Категория товаров")
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Сотрудник")
    
    # Результаты
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name="Время генерации")
    generated_by = models.ForeignKey(ManagementUser, on_delete=models.SET_NULL, null=True, verbose_name="Кем сгенерирован")
    
    class Meta:
        verbose_name = "Отчет"
        verbose_name_plural = "Отчеты"
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.get_report_type_display()} ({self.start_date} - {self.end_date})"
    
    def generate_data(self):
        """Генерация данных отчета"""
        if self.report_type == 'financial':
            return self._generate_financial_data()
        elif self.report_type == 'products':
            return self._generate_products_data()
        elif self.report_type == 'work_schedule':
            return self._generate_work_schedule_data()
        elif self.report_type == 'daily':
            return self._generate_daily_data()
        return {}
    
    def _generate_financial_data(self):
        """Генерация финансового отчета"""
        sales = Sale.objects.filter(
            created_at__date__range=[self.start_date, self.end_date],
            is_return=False
        )
        
        returns = Sale.objects.filter(
            created_at__date__range=[self.start_date, self.end_date],
            is_return=True
        )
        
        data = {
            'report_type': 'financial',
            'period': f"{self.start_date} - {self.end_date}",
            'generated_date': timezone.now().date(),
            'total_sales': sales.count(),
            'total_amount': float(sum(sale.final_amount for sale in sales)),
            'total_returns': returns.count(),
            'return_amount': float(sum(ret.final_amount for ret in returns)),
            'net_amount': float(sum(sale.final_amount for sale in sales) - sum(ret.final_amount for ret in returns)),
            'total_profit': float(sum(sale.profit for sale in sales)),
            'average_check': float(sum(sale.final_amount for sale in sales) / sales.count()) if sales.count() > 0 else 0,
        }
        
        return data
    
    def _generate_products_data(self):
        """Генерация отчета по товарам"""
        sale_items = SaleItem.objects.filter(
            sale__created_at__date__range=[self.start_date, self.end_date],
            sale__is_return=False
        ).select_related('product', 'product__category')
        
        # Фильтрация по категории если выбрана
        if self.category:
            sale_items = sale_items.filter(product__category=self.category)
        
        products_data = {}
        for item in sale_items:
            product = item.product
            if product.id not in products_data:
                products_data[product.id] = {
                    'product': product,
                    'quantity_sold': 0,
                    'revenue': 0,
                    'profit': 0,
                }
            
            products_data[product.id]['quantity_sold'] += item.quantity
            products_data[product.id]['revenue'] += float(item.total_price)
            products_data[product.id]['profit'] += float((item.selling_price - item.purchase_price) * item.quantity)
        
        # Формируем список товаров
        products_list = []
        for product_data in products_data.values():
            product = product_data['product']
            products_list.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'category': product.category.name if product.category else 'Без категории',
                'quantity_sold': product_data['quantity_sold'],
                'revenue': product_data['revenue'],
                'profit': product_data['profit'],
                'current_stock': product.quantity,
                'is_low_stock': product.quantity <= product.min_quantity,
            })
        
        # Сортируем по количеству продаж
        products_list.sort(key=lambda x: x['quantity_sold'], reverse=True)
        
        data = {
            'report_type': 'products',
            'period': f"{self.start_date} - {self.end_date}",
            'generated_date': timezone.now().date(),
            'category': self.category.name if self.category else 'Все категории',
            'total_products': len(products_list),
            'total_products_sold': sum(item['quantity_sold'] for item in products_list),
            'total_revenue': sum(item['revenue'] for item in products_list),
            'total_profit': sum(item['profit'] for item in products_list),
            'products': products_list[:20],  # Ограничим 20 товарами
        }
        
        return data
    
    def _generate_work_schedule_data(self):
        """Генерация отчета по графику работы"""
        shifts = WorkShift.objects.filter(
            date__range=[self.start_date, self.end_date],
            is_active=True
        ).select_related('employee', 'manager')
        
        # Фильтрация по сотруднику если выбран
        if self.employee:
            shifts = shifts.filter(employee=self.employee)
        
        employees_data = {}
        for shift in shifts:
            if shift.employee:
                employee = shift.employee
                if employee.id not in employees_data:
                    employees_data[employee.id] = {
                        'employee': employee,
                        'shifts_count': 0,
                        'total_hours': 0,
                    }
                
                # Рассчитываем продолжительность смены
                start_dt = datetime.combine(shift.date, shift.start_time)
                end_dt = datetime.combine(shift.date, shift.end_time)
                duration = (end_dt - start_dt).seconds / 3600
                
                employees_data[employee.id]['shifts_count'] += 1
                employees_data[employee.id]['total_hours'] += duration
        
        # Формируем список сотрудников
        employees_list = []
        for emp_data in employees_data.values():
            employee = emp_data['employee']
            employees_list.append({
                'id': employee.id,
                'full_name': employee.get_full_name(),
                'position': employee.get_position_display(),
                'shifts_count': emp_data['shifts_count'],
                'total_hours': emp_data['total_hours'],
            })
        
        # Сортируем по количеству смен
        employees_list.sort(key=lambda x: x['shifts_count'], reverse=True)
        
        data = {
            'report_type': 'work_schedule',
            'period': f"{self.start_date} - {self.end_date}",
            'generated_date': timezone.now().date(),
            'employee': self.employee.get_full_name() if self.employee else 'Все сотрудники',
            'total_employees': len(employees_list),
            'total_shifts': sum(emp['shifts_count'] for emp in employees_list),
            'total_hours': sum(emp['total_hours'] for emp in employees_list),
            'employees': employees_list,
        }
        
        return data
    
    def _generate_daily_data(self):
        """Генерация отчета за день"""
        # Используем финансовый отчет за один день
        return self._generate_financial_data()