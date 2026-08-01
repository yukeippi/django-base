from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from app.forms import TaskForm
from app.models import Task
from app.auth import can_delete_task, can_edit_task


# タスク一覧
@login_required
def index(request):
    tasks_qs = Task.objects.all()
    paginator = Paginator(tasks_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'app/task/index.html', {
        'tasks': page_obj,
        'page_obj': page_obj,
    })


# タスク詳細
@login_required
def show(request, pk):
    task = get_object_or_404(Task, pk=pk)
    return render(request, 'app/task/show.html', {
        'task': task,
        'can_edit': can_edit_task(request.user, task),
        'can_delete': can_delete_task(request.user, task),
    })


# タスク新規作成
@login_required
def new(request):
    if request.method == 'POST':
        return _create_task(request)
    return _display_new_form(request)


# タスク編集
@login_required
def edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not can_edit_task(request.user, task):
        raise PermissionDenied
    if request.method == 'POST':
        return _update_task(request, task)
    return _display_edit_form(request, task)


# タスク削除
@login_required
def delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not can_delete_task(request.user, task):
        raise PermissionDenied
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'タスクを削除しました。')
        return redirect('app:task_index')
    return render(request, 'app/task/delete.html', {'task': task})


# タスクAPI(E2Eテスト用)
@login_required
def api(request):
    if request.method == 'GET':
        tasks = Task.objects.all().values('id', 'title', 'status', 'priority')
        return JsonResponse(list(tasks), safe=False)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ============================================================
# ここから先はprivateヘルパー
# ============================================================


# 新規作成フォームを表示する
def _display_new_form(request):
    form = TaskForm()
    return _render_new_form(request, form)


# タスクの新規作成処理を行う
def _create_task(request):
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.created_by = request.user
        task.save()
        messages.success(request, 'タスクを作成しました。')
        return redirect('app:task_show', pk=task.pk)
    return _render_new_form(request, form)


# タスク新規作成フォームのレンダリング
def _render_new_form(request, form):
    return render(request, 'app/task/new.html', {'form': form})


# 編集フォームを表示する
def _display_edit_form(request, task):
    form = TaskForm(instance=task)
    return _render_edit_form(request, task, form)


# タスクの更新処理を行う
def _update_task(request, task):
    form = TaskForm(request.POST, instance=task)
    if form.is_valid():
        form.save()
        messages.success(request, 'タスクを更新しました。')
        return redirect('app:task_show', pk=task.pk)
    return _render_edit_form(request, task, form)


# タスク編集フォームのレンダリング
def _render_edit_form(request, task, form):
    return render(request, 'app/task/edit.html', {'form': form, 'task': task})
