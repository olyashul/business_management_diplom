# accounts/context_processors.py
from datetime import datetime

def current_datetime(request):
    """Добавляет текущие дату и время в контекст шаблонов"""
    return {
        'current_date': datetime.now(),
        'current_time': datetime.now(),
    }