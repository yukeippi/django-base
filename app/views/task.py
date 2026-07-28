from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from app.forms import TaskForm
from app.models import Task


# タスク一覧
def index(request):
    tasks_qs = Task.objects.all()
    paginator = Paginator(tasks_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'app/task/index.html', {
        'tasks': page_obj,
        'page_obj': page_obj,
    })


# タスク詳細
def show(request, pk):
    task = get_object_or_404(Task, pk=pk)
    return render(request, 'app/task/show.html', {'task': task})


# タスク新規作成
def new(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            messages.success(request, 'タスクを作成しました。')
            return redirect('app:task_show', pk=task.pk)
    else:
        form = TaskForm()
    return render(request, 'app/task/new.html', {'form': form})


# タスク編集
def edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'タスクを更新しました。')
            return redirect('app:task_show', pk=task.pk)
    else:
        form = TaskForm(instance=task)
    return render(request, 'app/task/edit.html', {'form': form, 'task': task})


# タスク削除
def delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'タスクを削除しました。')
        return redirect('app:task_index')
    return render(request, 'app/task/delete.html', {'task': task})


# タスクAPI(E2Eテスト用)
def api(request):
    if request.method == 'GET':
        tasks = Task.objects.all().values('id', 'title', 'status', 'priority')
        return JsonResponse(list(tasks), safe=False)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
