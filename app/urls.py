from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.index, name='index'),
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/import/', views.task_import, name='task_import'),
    path('tasks/export/', views.task_export, name='task_export'),
    path('tasks/export-template/', views.task_export_template, name='task_export_template'),
    path('api/tasks/', views.task_api, name='task_api'),
]
