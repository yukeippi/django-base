from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.contrib import messages

from .models import Task
from .forms import TaskImportForm
from .excel import TaskExcelHandler


# ホームページビュー
def index(request):
    return render(request, 'app/index.html', {
        'title': 'Task Manager',
    })


# タスク一覧ビュー
class TaskListView(ListView):
    model = Task
    template_name = 'app/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10


# タスク詳細ビュー
class TaskDetailView(DetailView):
    model = Task
    template_name = 'app/task_detail.html'
    context_object_name = 'task'


# タスクAPI（E2Eテスト用）
def task_api(request):
    if request.method == 'GET':
        tasks = Task.objects.all().values('id', 'title', 'status', 'priority')
        return JsonResponse(list(tasks), safe=False)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ExcelファイルからTaskを一括インポートする
def task_import(request):
    if request.method == 'POST':
        form = TaskImportForm(request.POST, request.FILES)
        if form.is_valid():
            handler = TaskExcelHandler()
            created_count, errors = handler.import_from_excel(
                file=request.FILES['file'],
                has_header=form.cleaned_data['has_header'],
            )
            if errors:
                for err in errors:
                    messages.warning(request, f"行{err['row']}: {err['message']}")
            if created_count:
                messages.success(request, f'{created_count}件のタスクをインポートしました。')
            return redirect('app:task_list')
    else:
        form = TaskImportForm()

    return render(request, 'app/task_import.html', {'form': form})


# 全タスクを新規Excelファイルとしてダウンロードする
def task_export(request):
    return TaskExcelHandler().export_to_new_excel(Task.objects.all())


# テンプレートExcelに全タスクを書き込んでダウンロードする
# テンプレートファイルのパスは settings.EXCEL_TEMPLATE_PATH で指定すること
def task_export_template(request):
    from django.conf import settings
    template_path = getattr(settings, 'EXCEL_TEMPLATE_PATH', None)
    if not template_path:
        messages.error(request, 'settings.EXCEL_TEMPLATE_PATH が設定されていません。')
        return redirect('app:task_list')

    return TaskExcelHandler().export_to_template(Task.objects.all(), template_path)
