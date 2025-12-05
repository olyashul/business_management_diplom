from django.db import models
from accounts.models import ManagementUser  # Импорт твоей кастомной модели пользователя из accounts

class Task(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название задачи", help_text="Описание задачи, например: 'Подготовить отчет'.")
    is_completed = models.BooleanField(default=False, verbose_name="Выполнена", help_text="Отметьте, если задача завершена.")
    date = models.DateField(auto_now_add=True, verbose_name="Дата создания", help_text="Дата автоматом ставится сегодняшняя; задачи необязательно привязывать к смене.")
    user = models.ForeignKey(ManagementUser, on_delete=models.CASCADE, related_name='tasks', verbose_name="Пользователь", help_text="Задачи личные для каждого пользователя.")

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ['-date', 'is_completed', 'title']  # Сортировка: свежие задачи сверху, незавершённые первыми

    def __str__(self):
        return f"{self.title} ({'Выполнена' if self.is_completed else 'Не выполнена'})"

class Shift(models.Model):
    date = models.DateField(verbose_name="Дата смены", help_text="Дата смены, выбираемая пользователем.")
    start_time = models.TimeField(default='09:00', editable=False, verbose_name="Время начала", help_text="Фиксированное: 09:00.")
    end_time = models.TimeField(default='20:00', editable=False, verbose_name="Время окончания", help_text="Фиксированное: 20:00.")
    user = models.ForeignKey(ManagementUser, on_delete=models.CASCADE, related_name='shifts', verbose_name="Пользователь", help_text="Смена привязана к директору/сотруднику.")

    class Meta:
        verbose_name = "Смена"
        verbose_name_plural = "Смены"
        unique_together = ('date', 'user')  \

    def __str__(self):
        return f"Смена {self.user} на {self.date} ({self.start_time}-{self.end_time})"
