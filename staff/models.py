from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import ManagementUser
from django.core.exceptions import ValidationError

class Employee(models.Model):
    POSITIONS = [
        ('manager', 'Менеджер'),
        ('seller', 'Продавец'),
        ('consultant', 'Консультант'),
        ('storekeeper', 'Кладовщик'),
        ('driver', 'Водитель'),
        ('accountant', 'Бухгалтер'),
        ('technician', 'Техник'),
        ('cleaner', 'Уборщик'),
    ]
    
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    middle_name = models.CharField(max_length=50, verbose_name="Отчество", blank=True)
    position = models.CharField(
        max_length=50, 
        choices=POSITIONS,
        verbose_name="Должность"
    )
    hire_date = models.DateField(verbose_name="Дата приема на работу")
    salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Оклад",
        validators=[MinValueValidator(0)]
    )
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    email = models.EmailField(verbose_name="Email", blank=True)
    address = models.TextField(verbose_name="Адрес", blank=True)
    passport_data = models.CharField(
        max_length=100, 
        verbose_name="Паспортные данные",
        blank=True
    )
    birth_date = models.DateField(verbose_name="Дата рождения", null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Активный")
    notes = models.TextField(verbose_name="Примечания", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name or ''}".strip()
    
    def get_full_name(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)
    
    def get_short_name(self):
        result = self.last_name
        if self.first_name:
            result += f" {self.first_name[0]}."
        if self.middle_name:
            result += f"{self.middle_name[0]}."
        return result

class WorkShift(models.Model):
    # Убрали SHIFT_TYPES, оставили просто смену
    date = models.DateField(verbose_name="Дата смены")
    start_time = models.TimeField(verbose_name="Время начала", default='08:00')
    end_time = models.TimeField(verbose_name="Время окончания", default='16:00')
    
    manager = models.ForeignKey(
        ManagementUser, 
        on_delete=models.CASCADE,
        verbose_name="Руководитель",
        null=True,
        blank=True,
        related_name='work_shifts'
    )
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        verbose_name="Сотрудник",
        null=True,
        blank=True,
        related_name='work_shifts'
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Активная смена")
    notes = models.TextField(verbose_name="Примечания", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Рабочая смена"
        verbose_name_plural = "Рабочие смены"
        ordering = ['-date', 'start_time']
        constraints = [
            models.UniqueConstraint(
                fields=['date', 'manager'],
                name='unique_manager_shift',
                condition=models.Q(manager__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['date', 'employee'],
                name='unique_employee_shift',
                condition=models.Q(employee__isnull=False)
            ),
        ]
    
    def clean(self):
        if not self.manager and not self.employee:
            raise ValidationError('Должен быть выбран либо руководитель, либо сотрудник')
        if self.manager and self.employee:
            raise ValidationError('Можно выбрать только руководителя ИЛИ сотрудника, не оба сразу')
        
        # Проверка времени
        if self.start_time >= self.end_time:
            raise ValidationError('Время окончания должно быть позже времени начала')
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Вызываем валидацию
        super().save(*args, **kwargs)
    
    def __str__(self):
        person = self.get_person_name()
        return f"Смена {person} на {self.date} ({self.start_time}-{self.end_time})"
    
    def get_person_name(self):
        if self.manager:
            return self.manager.get_full_name()
        return self.employee.get_full_name() if self.employee else "Не назначен"
    
    def get_person_short_name(self):
        if self.manager:
            return self.manager.get_short_name()
        return self.employee.get_short_name() if self.employee else "??"
    
    def get_position(self):
        if self.manager:
            return self.manager.position or "Руководитель"
        return self.employee.get_position_display() if self.employee else "Не назначен"
    
    def get_person_type(self):
        if self.manager:
            return 'manager'
        return 'employee' if self.employee else 'empty'
    
    def get_person_id(self):
        if self.manager:
            return self.manager_id
        return self.employee_id if self.employee else None
    
    def get_shift_duration(self):
        from datetime import datetime, date
        start_dt = datetime.combine(date.today(), self.start_time)
        end_dt = datetime.combine(date.today(), self.end_time)
        duration = (end_dt - start_dt).seconds / 3600
        return f"{duration:.1f} ч."
    
    def remove_person(self):
        """Удаляет сотрудника или руководителя из смены"""
        if self.manager:
            self.manager = None
        elif self.employee:
            self.employee = None
        self.save()
        return True


class WorkTimeRecord(models.Model):
    ATTENDANCE_TYPES = [
        ('present', 'Явка'),
        ('absent', 'Неявка'),
        ('sick', 'Больничный'),
        ('vacation', 'Отпуск'),
        ('day_off', 'Выходной'),
        ('late', 'Опоздание'),
        ('early', 'Уход раньше'),
    ]
    
    work_shift = models.ForeignKey(
        WorkShift,
        on_delete=models.CASCADE,
        verbose_name="Смена",
        related_name='time_records'
    )
    attendance_type = models.CharField(
        max_length=20,
        choices=ATTENDANCE_TYPES,
        verbose_name="Тип явки"
    )
    actual_start = models.TimeField(verbose_name="Фактическое начало", null=True, blank=True)
    actual_end = models.TimeField(verbose_name="Фактический конец", null=True, blank=True)
    hours_worked = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        verbose_name="Отработано часов",
        default=0
    )
    overtime_hours = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        verbose_name="Сверхурочные часы",
        default=0
    )
    notes = models.TextField(verbose_name="Примечания", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Учет рабочего времени"
        verbose_name_plural = "Учет рабочего времени"
        ordering = ['-work_shift__date']
    
    def __str__(self):
        return f"{self.work_shift.get_person_name()} - {self.work_shift.date} ({self.get_attendance_type_display()})"