from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.contrib import messages

from .models import Task
from .forms import TaskImportForm
from .excel import import_tasks_from_excel, export_tasks_to_new_excel, export_tasks_to_template


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


def task_import(request):
    """
    ExcelファイルからTaskを一括インポートする。
    """
    if request.method == 'POST':
        form = TaskImportForm(request.POST, request.FILES)
        if form.is_valid():
            created_count, errors = import_tasks_from_excel(
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


def task_export(request):
    """
    全タスクを新規Excelファイルとしてダウンロードする。
    """
    tasks = Task.objects.all()
    return export_tasks_to_new_excel(tasks)


def task_export_template(request):
    """
    テンプレートExcelに全タスクを書き込んでダウンロードする。
    テンプレートファイルのパスはsettings.EXCEL_TEMPLATE_PATHで指定してください。
    """
    from django.conf import settings
    template_path = getattr(settings, 'EXCEL_TEMPLATE_PATH', None)
    if not template_path:
        messages.error(request, 'settings.EXCEL_TEMPLATE_PATH が設定されていません。')
        return redirect('app:task_list')

    tasks = Task.objects.all()
    return export_tasks_to_template(tasks, template_path)
