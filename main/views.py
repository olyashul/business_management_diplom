from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import Task
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

@login_required
def dashboard(request):
    today = timezone.now().date()
    shift_time = "09:00 - 18:00"  # Заглушка
    
    tasks = Task.objects.filter(user=request.user).order_by('-date', 'is_completed', 'title')  # Добавила 'is_completed' для предыдущей логики сортировки — если не нужно, убери
    
    context = {
        'current_date': today,
        'shift_time': shift_time,
        'tasks': tasks,
    }
    return render(request, 'main/dashboard.html', context)

@login_required
@csrf_exempt
def add_task_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        due_date = request.POST.get('due_date')
        
        if title and due_date:
            try:
                task = Task.objects.create(
                    title=title,
                    date=due_date,
                    user=request.user,
                    is_completed=False
                )
                return JsonResponse({
                    'id': task.id,
                    'title': task.title,
                    'date': task.date.strftime('%d.%m.%Y'),
                    'success': True
                })
            except Exception as e:
                return JsonResponse({'error': str(e), 'success': False}, status=400)
        else:
            return JsonResponse({'error': 'Заполните все поля', 'success': False}, status=400)
    
    return JsonResponse({'error': 'Недопустимый метод', 'success': False}, status=405)

@login_required
@csrf_exempt
def delete_task(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id, user=request.user)
        task.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Недопустимый метод', 'success': False}, status=405)
