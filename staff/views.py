from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from datetime import timedelta
from .models import Employee, WorkShift
from .forms import EmployeeForm, WorkShiftForm, QuickShiftForm


@login_required
def staff_dashboard(request):
    now = timezone.now()
    current_time = now.time()
    today = now.date()

    # Смены на сегодня
    today_shifts = WorkShift.objects.filter(date=today, is_active=True).order_by('start_time')
    
    # Считаем только активные СЕЙЧАС смены
    active_now = 0
    for shift in today_shifts:
        if shift.start_time <= current_time <= shift.end_time:
            active_now += 1
    
    # Все активные сотрудники
    employees = Employee.objects.filter(is_active=True)
    
    # Смены на завтра
    tomorrow = today + timedelta(days=1)
    tomorrow_shifts = WorkShift.objects.filter(date=tomorrow, is_active=True)[:5]
    
    # Статистика
    total_employees = employees.count()
    
    # Ближайшие дни рождения
    upcoming_birthdays = Employee.objects.filter(
        birth_date__isnull=False,
        is_active=True
    ).filter(
        Q(birth_date__month=today.month, birth_date__day__gte=today.day) |
        Q(birth_date__month=(today.month % 12) + 1)
    ).order_by('birth_date__month', 'birth_date__day')[:5]
    
    # Форма для быстрого добавления смены
    quick_form = QuickShiftForm(initial={'date': today})
    
    context = {
        'today': today,
        'today_shifts': today_shifts,
        'tomorrow_shifts': tomorrow_shifts,
        'total_employees': total_employees,
        'on_duty_today': active_now,
        'upcoming_birthdays': upcoming_birthdays,
        'quick_form': quick_form,
    }
    return render(request, 'staff/dashboard.html', context)


@login_required
def add_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            messages.success(request, 
                f'Сотрудник {employee.get_full_name()} успешно добавлен!'
            )
            return redirect('staff:employee_list')
    else:
        form = EmployeeForm()
    
    return render(request, 'staff/add_employee.html', {'form': form})


@login_required
def delete_employee(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        employee.is_active = False
        employee.save()
        messages.success(request, 
            f'Сотрудник {employee.get_full_name()} деактивирован!'
        )
        return redirect('staff:employee_list')
    
    return render(request, 'staff/delete_employee.html', {'employee': employee})


@login_required
def quick_add_shift(request):
    if request.method == 'POST':
        form = QuickShiftForm(request.POST)
        if form.is_valid():
            shift = form.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'shift_id': shift.id,
                    'employee_name': shift.employee.get_full_name() if shift.employee else "Не назначен",
                    'date': shift.date.strftime('%d.%m.%Y'),
                    'start_time': shift.start_time.strftime('%H:%M'),
                    'end_time': shift.end_time.strftime('%H:%M'),
                })
            return redirect('staff:staff_dashboard')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors,
                })
    
    messages.error(request, 'Ошибка при добавлении смены')
    return redirect('staff:staff_dashboard')


@login_required
def employee_list(request):
    employees = Employee.objects.all().order_by('last_name', 'first_name')
    
    context = {
        'employees': employees,
    }
    return render(request, 'staff/employee_list.html', context)


@login_required
def create_schedule(request):
    today = timezone.now().date()
    
    # Получаем год и месяц из параметров
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    if year and month:
        try:
            year = int(year)
            month = int(month)
        except ValueError:
            year = today.year
            month = today.month
    else:
        year = today.year
        month = today.month
    
    # Обработка POST-запроса для добавления смены
    if request.method == 'POST':
        form = WorkShiftForm(request.POST)
        if form.is_valid():
            try:
                shift = form.save(commit=False)
                shift.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                    })
                return redirect('staff:create_schedule')
            
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': str(e),
                    })
                messages.error(request, f'Ошибка: {str(e)}')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Ошибка валидации формы',
                    'errors': form.errors
                })
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    
    # GET запрос - отображение календаря
    # Получаем смены на месяц
    shifts = WorkShift.objects.filter(
        date__year=year,
        date__month=month,
        is_active=True
    ).select_related('employee', 'manager').order_by('date', 'start_time')
    
    # Создаем календарь
    import calendar
    cal_obj = calendar.Calendar(firstweekday=0)  # 0 = Monday
    
    # Получаем недели месяца
    weeks = cal_obj.monthdatescalendar(year, month)
    
    calendar_weeks = []
    
    for week in weeks:
        week_days = []
        for date_obj in week:
            is_today = date_obj == today
            is_other_month = date_obj.month != month
            
            # Получаем смены на эту дату
            day_shifts = []
            if not is_other_month:
                for shift in shifts:
                    if shift.date == date_obj:
                        day_shifts.append({
                            'id': shift.id,
                            'person_name': shift.get_person_name(),
                            'person_short': shift.get_person_short_name(),
                            'start_time': shift.start_time,
                            'end_time': shift.end_time,
                        })
            
            week_days.append({
                'date': date_obj,
                'day': date_obj.day,
                'is_today': is_today,
                'is_other_month': is_other_month,
                'shifts': day_shifts,
                'has_shifts': len(day_shifts) > 0,
            })
        calendar_weeks.append(week_days)
    
    # Навигация
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    month_names = [
        'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
    ]
    
    context = {
        'current_year': year,
        'current_month': month,
        'current_month_name': month_names[month - 1],
        'prev_year': prev_year,
        'prev_month': prev_month,
        'prev_month_name': month_names[prev_month - 1],
        'next_year': next_year,
        'next_month': next_month,
        'next_month_name': month_names[next_month - 1],
        'calendar_weeks': calendar_weeks,
        'employees': Employee.objects.filter(is_active=True),
        'form': WorkShiftForm(),
    }
    return render(request, 'staff/create_schedule.html', context)


@login_required
def delete_shift_ajax(request, pk):
    shift = get_object_or_404(WorkShift, pk=pk)
    
    if request.method == 'DELETE':
        try:
            employee_name = shift.get_person_name()
            date = shift.date
            shift.delete()
            
            return JsonResponse({
                'success': True,
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Ошибка при удалении: {str(e)}'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'Метод не разрешен'
    }, status=405)


@login_required
def edit_employee(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            employee = form.save()
            messages.success(request, 
                f'Данные сотрудника {employee.get_full_name()} обновлены!'
            )
            return redirect('staff:employee_list')
    else:
        form = EmployeeForm(instance=employee)
    
    return render(request, 'staff/edit_employee.html', {'form': form, 'employee': employee})