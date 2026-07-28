from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.home.index, name='index'),
    path('tasks/', views.task.index, name='task_index'),
    path('tasks/new/', views.task.new, name='task_new'),
    path('tasks/<int:pk>/', views.task.show, name='task_show'),
    path('tasks/<int:pk>/edit/', views.task.edit, name='task_edit'),
    path('tasks/<int:pk>/delete/', views.task.delete, name='task_delete'),
    path('api/tasks/', views.task.api, name='task_api'),
]
