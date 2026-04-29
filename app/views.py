from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from .models import Task


def index(request):
    """
    ホームページビュー
    """
    return render(request, 'app/index.html', {
        'title': 'Task Manager',
    })


class TaskListView(ListView):
    """
    タスク一覧ビュー
    """
    model = Task
    template_name = 'app/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10


class TaskDetailView(DetailView):
    """
    タスク詳細ビュー
    """
    model = Task
    template_name = 'app/task_detail.html'
    context_object_name = 'task'


def task_api(request):
    """
    タスクAPI（E2Eテスト用）
    """
    if request.method == 'GET':
        tasks = Task.objects.all().values('id', 'title', 'status', 'priority')
        return JsonResponse(list(tasks), safe=False)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
