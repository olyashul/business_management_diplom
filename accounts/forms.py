from django import forms 
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model, authenticate
from django.utils.html import strip_tags
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from datetime import date

User = get_user_model()  # Получаем модель ManagementUser


# Форма для регистрации нового руководства (директор/замы)
class ManagementUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        max_length=254, 
        widget=forms.EmailInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 
            'placeholder': 'EMAIL'
        })
    )
    
    first_name = forms.CharField(
        required=True, 
        max_length=50, 
        widget=forms.TextInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 
            'placeholder': 'ИМЯ'
        })
    )
    
    last_name = forms.CharField(
        required=True, 
        max_length=50, 
        widget=forms.TextInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 
            'placeholder': 'ФАМИЛИЯ'
        })
    )
    
    birth_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500',
            'placeholder': 'ДАТА РОЖДЕНИЯ (ГГГГ-ММ-ДД)',
            'type': 'date'
        })
    )
    
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 
            'placeholder': 'ПАРОЛЬ'
        })
    )
    
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 
            'placeholder': 'ПОДТВЕРДИТЕ ПАРОЛЬ'
        })
    )

    # Класс Meta для связи с моделью
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'birth_date', 'password1', 'password2')

    # Кастомная валидация email
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Этот email уже используется')
        return email
    
    # Валидация даты рождения
    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            # Проверяем, что дата не в будущем
            if birth_date > date.today():
                raise forms.ValidationError('Дата рождения не может быть в будущем')
            
            # Проверяем возраст (не младше 18 лет)
            age = date.today().year - birth_date.year
            if (date.today().month, date.today().day) < (birth_date.month, birth_date.day):
                age -= 1
            
            if age < 18:
                raise forms.ValidationError('Пользователь должен быть старше 18 лет')
        
        return birth_date

    # Метод сохранения пользователя
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = None  # Устанавливаем username в None
        if commit:
            user.save()
        return user


# Форма для входа (авторизации) пользователя
class ManagementUserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Email",
        widget=forms.TextInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 
            'placeholder': 'EMAIL'
        })
    )
    
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 
            'placeholder': 'ПАРОЛЬ'
        })
    )

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            # Используем email для аутентификации
            self.user_cache = authenticate(
                self.request, 
                email=email, 
                password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError('Неверный email или пароль.')
            elif not self.user_cache.is_active:
                raise forms.ValidationError('Этот аккаунт неактивен.')
        
        return self.cleaned_data


# Форма для обновления данных пользователя (профиль)
class ManagementUserUpdateForm(forms.ModelForm):
    phone = forms.CharField(
        required=False,
        validators=[
            RegexValidator(
                r'^\+?1?\d{9,15}$', 
                "Введите корректный номер телефона."
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 
            'placeholder': 'ТЕЛЕФОН'
        })
    )
    
    first_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 
            'placeholder': 'ИМЯ'
        })
    )
    
    last_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 
            'placeholder': 'ФАМИЛИЯ'
        })
    )
    
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 
            'placeholder': 'EMAIL'
        })
    )
    
    middle_name = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 
            'placeholder': 'ОТЧЕСТВО (необязательно)'
        })
    )
    
    position = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 
            'placeholder': 'ДОЛЖНОСТЬ'
        })
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'middle_name', 'email', 
                  'birth_date', 'position', 'phone')
        
        widgets = {
            'birth_date': forms.DateInput(attrs={
                'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500',
                'placeholder': 'ДАТА РОЖДЕНИЯ',
                'type': 'date'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('Этот email уже используется.')
        return email
    
    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            if birth_date > date.today():
                raise forms.ValidationError('Дата рождения не может быть в будущем')
            
            age = date.today().year - birth_date.year
            if (date.today().month, date.today().day) < (birth_date.month, birth_date.day):
                age -= 1
            
            if age < 18:
                raise forms.ValidationError('Пользователь должен быть старше 18 лет')
        
        return birth_date
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Очистка от HTML-тегов (как в модели)
        fields_to_clean = ['first_name', 'last_name', 'middle_name', 'position', 'phone']
        for field in fields_to_clean:
            if cleaned_data.get(field):
                cleaned_data[field] = strip_tags(cleaned_data[field])
        
        # Если email не указан, используем существующий
        if not cleaned_data.get('email'):
            cleaned_data['email'] = self.instance.email
        
        return cleaned_data


# Форма для смены пароля
class ManagementUserPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 
            'placeholder': 'СТАРЫЙ ПАРОЛЬ'
        })
    )
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 
            'placeholder': 'НОВЫЙ ПАРОЛЬ'
        })
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 
            'placeholder': 'ПОВТОРИТЕ НОВЫЙ ПАРОЛЬ'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError('Пароли не совпадают')
        
        return cleaned_data
    
    def save(self):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()