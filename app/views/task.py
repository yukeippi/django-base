from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from app.models import Task


# タスク一覧ビュー
class TaskListView(ListView):
    model = Task
    template_name = 'app/task/index.html'
    context_object_name = 'tasks'
    paginate_by = 10


# タスク詳細ビュー
class TaskDetailView(DetailView):
    model = Task
    template_name = 'app/task/show.html'
    context_object_name = 'task'


# タスクAPI（E2Eテスト用）
def task_api(request):
    if request.method == 'GET':
        tasks = Task.objects.all().values('id', 'title', 'status', 'priority')
        return JsonResponse(list(tasks), safe=False)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
