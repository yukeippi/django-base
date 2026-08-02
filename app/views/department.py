from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from app.forms import DepartmentForm
from app.models import Department


# 部門一覧
# TODO: 権限制御を再設計後、閲覧範囲を絞り込む
@login_required
def index(request):
    departments_qs = Department.objects.select_related('company').all()
    paginator = Paginator(departments_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'app/department/index.html', {
        'departments': page_obj,
        'page_obj': page_obj,
    })


# 部門詳細
@login_required
def show(request, pk):
    department = get_object_or_404(Department, pk=pk)
    return render(request, 'app/department/show.html', {'department': department})


# 部門新規作成
# TODO: 権限制御を再設計後、作成可否をチェックする
@login_required
def new(request):
    if request.method == 'POST':
        return _create_department(request)
    return _display_new_form(request)


# 部門編集
# TODO: 権限制御を再設計後、編集可否をチェックする
@login_required
def edit(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        return _update_department(request, department)
    return _display_edit_form(request, department)


# 部門削除
# TODO: 権限制御を再設計後、削除可否をチェックする
@login_required
def delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, '部門を削除しました。')
        return redirect('app:department_index')
    return render(request, 'app/department/delete.html', {'department': department})


# ============================================================
# ここから先はprivateヘルパー
# ============================================================


# 新規作成フォームを表示する
def _display_new_form(request):
    form = DepartmentForm()
    return _render_new_form(request, form)


# 部門の新規作成処理を行う
def _create_department(request):
    form = DepartmentForm(request.POST)
    if form.is_valid():
        department = form.save()
        messages.success(request, '部門を作成しました。')
        return redirect('app:department_show', pk=department.pk)
    return _render_new_form(request, form)


# 部門新規作成フォームのレンダリング
def _render_new_form(request, form):
    return render(request, 'app/department/new.html', {'form': form})


# 編集フォームを表示する
def _display_edit_form(request, department):
    form = DepartmentForm(instance=department)
    return _render_edit_form(request, department, form)


# 部門の更新処理を行う
def _update_department(request, department):
    form = DepartmentForm(request.POST, instance=department)
    if form.is_valid():
        form.save()
        messages.success(request, '部門情報を更新しました。')
        return redirect('app:department_show', pk=department.pk)
    return _render_edit_form(request, department, form)


# 部門編集フォームのレンダリング
def _render_edit_form(request, department, form):
    return render(request, 'app/department/edit.html', {'form': form, 'department': department})
