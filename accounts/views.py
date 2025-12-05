# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.contrib import messages
from .forms import (
    ManagementUserCreationForm, 
    ManagementUserLoginForm, 
    ManagementUserUpdateForm,
    ManagementUserPasswordChangeForm
)
from .models import ManagementUser

# Регистрация нового пользователя с автоматическим логином и поддержкой HTMX
def register(request):
    # Если пользователь уже авторизован, перенаправляем на профиль
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        form = ManagementUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Автоматически логиним пользователя после регистрации
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            if request.headers.get('HX-Request'):
                return HttpResponse(headers={'HX-Redirect': reverse('home')})
            return redirect('accounts:profile')
    else:
        form = ManagementUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

# Вход в систему с поддержкой HTMX
def login_view(request):
    # Если пользователь уже авторизован, перенаправляем на главную
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = ManagementUserLoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            if request.headers.get('HX-Request'):
                return HttpResponse(headers={'HX-Redirect': reverse('home')})
            return redirect('home')
    else:
        form = ManagementUserLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

# Выход из системы с поддержкой HTMX
def logout_view(request):
    logout(request)
    if request.headers.get('HX-Request'):
        return HttpResponse(headers={'HX-Redirect': reverse('accounts:login')})
    return redirect('accounts:login')

# Главная страница: перенаправление на профиль для авторизованных пользователей
def home_view(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    return redirect('accounts:profile')

# Профиль пользователя с возможностью обновления данных и поддержкой HTMX
@login_required(login_url='/accounts/login/')
def profile_view(request):
    if request.method == 'POST':
        form = ManagementUserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен')
            
            if request.headers.get('HX-Request'):
                return HttpResponse(headers={'HX-Redirect': reverse('accounts:profile')})
            return redirect('accounts:profile')
    else:
        form = ManagementUserUpdateForm(instance=request.user)
    
    return TemplateResponse(request, 'accounts/profile.html', {
        'form': form,
        'user': request.user,
    })

# Детали профиля (только чтение) для HTMX - отображение данных пользователя
@login_required(login_url='/accounts/login/')
def account_details(request):
    user = request.user  # Используем request.user напрямую для простоты
    return TemplateResponse(request, 'accounts/partials/account_details.html', {'user': user})

# Форма редактирования профиля для HTMX - показ формы редактирования
@login_required(login_url='/accounts/login/')
def edit_account_details(request):
    form = ManagementUserUpdateForm(instance=request.user)
    return TemplateResponse(request, 'accounts/partials/edit_account_details.html', {
        'user': request.user,
        'form': form
    })

# Обновление данных профиля для HTMX - обработка формы и возврат обновлённых данных
@login_required(login_url='/accounts/login/')
def update_account_details(request):
    if request.method == 'POST':
        form = ManagementUserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            updated_user = user  # Нет необходимости в дополнительном запросе, если save возвращает объект
            
            if request.headers.get('HX-Request'):
                return TemplateResponse(request, 'accounts/partials/account_details.html', {
                    'user': updated_user
                })
            return redirect('accounts:profile')
        else:
            return TemplateResponse(request, 'accounts/partials/edit_account_details.html', {
                'user': request.user,
                'form': form
            })
    
    if request.headers.get('HX-Request'):
        return HttpResponse(headers={'HX-Redirect': reverse('accounts:profile')})
    return redirect('accounts:profile')

# Смена пароля с поддержкой HTMX
@login_required(login_url='/accounts/login/')
def change_password(request):
    if request.method == 'POST':
        form = ManagementUserPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Пароль успешно изменен!')
            
            if request.headers.get('HX-Request'):
                return HttpResponse(headers={'HX-Redirect': reverse('accounts:profile')})
            return redirect('accounts:profile')
    else:
        form = ManagementUserPasswordChangeForm(user=request.user)
    return render(request, 'accounts/change_password.html', {'form': form})

# Список пользователей (только для администраторов)
@login_required(login_url='/accounts/login/')
def user_list(request):
    # Только суперпользователь может видеть список всех пользователей
    if not request.user.is_superuser:
        messages.error(request, 'У вас нет прав для просмотра этого раздела.')
        return redirect('home')
    users = ManagementUser.objects.all().order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users})
