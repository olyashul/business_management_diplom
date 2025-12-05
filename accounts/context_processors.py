from datetime import datetime

def current_datetime(request):
    return {
        'current_date': datetime.now(),
        'current_time': datetime.now(),
    }