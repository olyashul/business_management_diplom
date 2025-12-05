from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth import get_user_model, authenticate
from django.utils.html import strip_tags
from datetime import date
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm
from .models import ManagementUser

User = get_user_model()

# Базовый класс для общих атрибутов полей форм. Определяет стандартные атрибуты ввода и метод для генерации атрибутов полей с плейсхолдерами.
class BaseForm:
    input_attrs = {
        'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500'
    }
    
    # Метод для получения атрибутов поля с добавленным плейсхолдером на основе базовых атрибутов.
    def get_field_attrs(self, placeholder):
        attrs = self.input_attrs.copy()
        attrs['placeholder'] = placeholder
        return attrs

# Форма для создания нового пользователя (регистрации). Наследуется от UserCreationForm и включает настройки полей, валидацию email, возраста и пароля.
class ManagementUserCreationForm(BaseForm, UserCreationForm):
    # Инициализация формы: настраивает виджеты полей, метки, плейсхолдеры и добавляет поле birth_date с валидацией возраста (минимум 18 лет).
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Настройка полей регистрации
        fields_config = {
            'email': ('EMAIL', forms.EmailInput),
            'first_name': ('ИМЯ', forms.TextInput),
            'last_name': ('ФАМИЛИЯ', forms.TextInput),
            'password1': ('ПАРОЛЬ', forms.PasswordInput),
            'password2': ('ПОДТВЕРДИТЕ ПАРОЛЬ', forms.PasswordInput),
        }
        
        for field_name, (placeholder, widget_class) in fields_config.items():
            self.fields[field_name].widget = widget_class(attrs=self.get_field_attrs(placeholder))
            self.fields[field_name].required = True
        
        # Labels и help_text
        self.fields['first_name'].label = "Имя"
        self.fields['last_name'].label = "Фамилия"
        self.fields['password1'].label = "Пароль"
        self.fields['password2'].label = "Подтверждение пароля"
        self.fields['password1'].help_text = None
        
        # Особое поле birth_date
        self.fields['birth_date'] = forms.DateField(
            required=True,
            widget=forms.DateInput(attrs={
                **self.input_attrs,
                'placeholder': 'ДАТА РОЖДЕНИЯ (ГГГГ-ММ-ДД)',
                'type': 'date'
            })
        )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'birth_date')

    # Валидация поля email: проверяет обязательность, уникальность и нормализует значение (нижний регистр).
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('Поле Email обязательно для заполнения')
        
        email = email.lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Этот email уже используется')
        
        return email

    # Валидация поля birth_date: проверяет обязательность, что дата не в будущем и возраст не менее 18 лет.
    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if not birth_date:
            raise forms.ValidationError('Поле Дата рождения обязательно для заполнения')
        if birth_date > date.today():
            raise forms.ValidationError('Дата рождения не может быть в будущем')
        
        age = date.today().year - birth_date.year
        if (date.today().month, date.today().day) < (birth_date.month, birth_date.day):
            age -= 1
        if age < 18:
            raise forms.ValidationError('Пользователь должен быть старше 18 лет')
        return birth_date

    # Валидация поля password1: проверяет обязательность, минимальную длину (8 символов), что пароль не состоит только из цифр и не является распространённым паролем.
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if not password1:
            raise ValidationError('Поле Пароль обязательно для заполнения')
        
        errors = []
        if len(password1) < 8:
            errors.append('Пароль слишком короткий. Минимум 8 символов.')
        if password1.isdigit():
            errors.append('Пароль не может состоять только из цифр.')
        # Проверка на общие пароли (расширьте список по необходимости)
        common_passwords = ['password', '12345678', 'qwerty', 'admin', 'letmein']
        if password1.lower() in common_passwords:
            errors.append('Пароль слишком простой.')
        
        if errors:
            raise ValidationError(' '.join(errors))
        return password1

    # Валидация поля password2: проверяет обязательность и совпадение с password1.
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if not password2:
            raise ValidationError("Поле Подтверждение пароля обязательно для заполнения")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Пароли не совпадают")
        return password2

# Форма для входа в систему (AuthenticationForm). Настраивает виджеты полей и переопределяет валидацию для использования email вместо username.
class ManagementUserLoginForm(AuthenticationForm):
    # Инициализация формы: устанавливает лейблы и атрибуты для полей username (email) и password.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['username'].label = "Email"
        self.fields['username'].widget.attrs.update(BaseForm().get_field_attrs('EMAIL'))
        self.fields['password'].widget.attrs.update(BaseForm().get_field_attrs('ПАРОЛЬ'))

    # Переопределённая валидация формы: пытается аутентифицировать пользователя по email и паролю, поднимает ошибки при неверных данных или неактивном аккаунте.
    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if email and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError('Неверный email или пароль.')
            if not self.user_cache.is_active:
                raise forms.ValidationError('Этот аккаунт неактивен.')
        return self.cleaned_data

# Форма для обновления профиля пользователя (ModelForm). Настраивает виджеты полей, валидирует email и birth_date, очищает HTML из текстовых полей.
class ManagementUserUpdateForm(BaseForm, forms.ModelForm):
    # Инициализация формы: настраивает виджеты и обязательность полей профиля.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        field_configs = {
            'phone': ('ТЕЛЕФОН', forms.TextInput),
            'first_name': ('ИМЯ', forms.TextInput),
            'last_name': ('ФАМИЛИЯ', forms.TextInput),
            'email': ('EMAIL', forms.EmailInput),
            'middle_name': ('ОТЧЕСТВО', forms.TextInput),
            'position': ('ДОЛЖНОСТЬ', forms.TextInput),
        }
        
        for field_name, (placeholder, widget_class) in field_configs.items():
            if field_name in self.fields:
                self.fields[field_name].widget = widget_class(attrs=self.get_field_attrs(placeholder))
                self.fields[field_name].required = (field_name in ['first_name', 'last_name'])
        
        self.fields['birth_date'].widget = forms.DateInput(attrs={
            **self.input_attrs,
            'placeholder': 'ДАТА РОЖДЕНИЯ',
            'type': 'date'
        })

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'middle_name', 'email', 'birth_date', 'position', 'phone')

    # Валидация поля email: проверяет уникальность (исключая текущего пользователя) и нормализует значение.
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            if User.objects.filter(email=email).exclude(id=self.instance.id).exists():
                raise forms.ValidationError('Этот email уже используется.')
        return email or self.instance.email

    # Общая валидация формы: проверяет birth_date на возраст и не в будущем, очищает HTML из текстовых полей, проверяет обязательность имени и фамилии.
    def clean(self):
        cleaned_data = super().clean()
        birth_date = cleaned_data.get('birth_date')
        if birth_date:
            if birth_date > date.today():
                raise forms.ValidationError({'birth_date': 'Дата рождения не может быть в будущем'})
            age = date.today().year - birth_date.year
            if (date.today().month, date.today().day) < (birth_date.month, birth_date.day):
                age -= 1
            if age < 18:
                raise forms.ValidationError({'birth_date': 'Пользователь должен быть старше 18 лет'})
        
        # Очистка HTML
        text_fields = ['first_name', 'last_name', 'middle_name', 'position', 'phone']
        for field in text_fields:
            if cleaned_data.get(field):
                cleaned_data[field] = strip_tags(str(cleaned_data[field])).strip()
        if not cleaned_data.get('first_name') or not cleaned_data.get('last_name'):
            raise forms.ValidationError('Имя и фамилия обязательны для заполнения')
        return cleaned_data

# Форма для изменения пароля пользователя. Переопределяет PasswordChangeForm, добавляя проверку, что новый пароль отличается от старого.
class ManagementUserPasswordChangeForm(PasswordChangeForm):
    class Meta:
        model = ManagementUser
        fields = ['old_password', 'new_password1', 'new_password2']

    # Инициализация формы: может использоваться для дополнительных настроек полей в будущем.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Дополнительные настройки полей, если нужно

    # Валидация поля new_password1: проверяет, что новый пароль не совпадает с текущим паролем пользователя.
    def clean_new_password1(self):
        new_password = self.cleaned_data.get('new_password1')
        old_password = self.cleaned_data.get('old_password')
        
        # Проверяем, что новый пароль не совпадает со старым
        if new_password and old_password and self.user.check_password(new_password):
            raise ValidationError('Новый пароль должен отличаться от текущего.')
        
        return new_password
