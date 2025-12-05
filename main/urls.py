from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-task-view/', views.add_task_view, name='add_task_view'),
    path('delete-task/<int:task_id>/', views.delete_task, name='delete_task'),
]
