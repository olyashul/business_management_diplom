from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.html import strip_tags
from datetime import date

# Создаем кастомный менеджер пользователей
class ManagementUserManager(BaseUserManager):

    # Метод для создания обычного пользователя
    def create_user(self, email, first_name, last_name, birth_date, password=None, **extra_fields):
        # Проверяем обязательные поля
        if not email:
            raise ValueError("Email обязателен для заполнения.")
        if not first_name:
            raise ValueError("Имя обязательно для заполнения.")
        if not last_name:
            raise ValueError("Фамилия обязательна для заполнения.")
        email = self.normalize_email(email)
        user = self.model(
            email=email, 
            first_name=first_name, 
            last_name=last_name,
            birth_date=birth_date,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    # Метод для создания суперпользователя
    def create_superuser(self, email, password=None, **extra_fields):
        # Устанавливаем флаги
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        # Проверяем флаги
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')
        
        # Для суперпользователя используем дефолтные значения
        return self.create_user(
            email=email,
            password=password,
            **extra_fields
        )


class ManagementUser(AbstractUser):

    # Обязательные поля для всех пользователей
    email = models.EmailField(unique=True, max_length=254)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birth_date = models.DateField()
    
    # Необязательные поля
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    position = models.CharField(max_length=100, default='Руководитель')
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Убираем username, используем email
    username = None
    
    # Используем наш менеджер
    objects = ManagementUserManager()
    
    # Настройки авторизации
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'birth_date']
    
    # Строковое представление
    def __str__(self):
        return self.email
    
    # Очистка от HTML-тегов (как в шаблоне)
    def clean(self):
        # Список полей для очистки
        fields_to_clean = ['first_name', 'last_name', 'middle_name', 'position', 'phone']
        for field in fields_to_clean:
            value = getattr(self, field)
            if value:
                setattr(self, field, strip_tags(value))