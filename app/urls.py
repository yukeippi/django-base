from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.home.index, name='index'),
    path('login/', views.auth.login, name='login'),
    path('logout/', views.auth.logout, name='logout'),
    path('tasks/', views.task.index, name='task_index'),
    path('tasks/new/', views.task.new, name='task_new'),
    path('tasks/<int:pk>/', views.task.show, name='task_show'),
    path('tasks/<int:pk>/edit/', views.task.edit, name='task_edit'),
    path('tasks/<int:pk>/delete/', views.task.delete, name='task_delete'),
    path('api/tasks/', views.task.api, name='task_api'),
    path('employees/', views.employee.index, name='employee_index'),
    path('employees/new/', views.employee.new, name='employee_new'),
    path('employees/<int:pk>/', views.employee.show, name='employee_show'),
    path('employees/<int:pk>/edit/', views.employee.edit, name='employee_edit'),
    path('employees/<int:pk>/delete/', views.employee.delete, name='employee_delete'),
    path('management_groups/', views.management_group.index, name='management_group_index'),
    path('management_groups/new/', views.management_group.new, name='management_group_new'),
    path('management_groups/<int:pk>/', views.management_group.show, name='management_group_show'),
    path('management_groups/<int:pk>/edit/', views.management_group.edit, name='management_group_edit'),
    path('management_groups/<int:pk>/delete/', views.management_group.delete, name='management_group_delete'),
]
