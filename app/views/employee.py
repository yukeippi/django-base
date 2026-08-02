from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from app.forms import EmployeeForm
from app.models import Employee


# 社員一覧
# TODO: 権限制御を再設計後、閲覧範囲を絞り込む
@login_required
def index(request):
    employees_qs = Employee.objects.select_related('user').all()
    paginator = Paginator(employees_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'app/employee/index.html', {
        'employees': page_obj,
        'page_obj': page_obj,
    })


# 社員詳細
@login_required
def show(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'app/employee/show.html', {'employee': employee})


# 社員新規作成
# TODO: 権限制御を再設計後、作成可否をチェックする
@login_required
def new(request):
    if request.method == 'POST':
        return _create_employee(request)
    return _display_new_form(request)


# 社員編集
# TODO: 権限制御を再設計後、編集可否をチェックする
@login_required
def edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        return _update_employee(request, employee)
    return _display_edit_form(request, employee)


# 社員削除
# TODO: 権限制御を再設計後、削除可否をチェックする
@login_required
def delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.user.delete()
        messages.success(request, '社員情報を削除しました。')
        return redirect('app:employee_index')
    return render(request, 'app/employee/delete.html', {'employee': employee})


# ============================================================
# ここから先はprivateヘルパー
# ============================================================


# 新規作成フォームを表示する
def _display_new_form(request):
    form = EmployeeForm()
    return _render_new_form(request, form)


# 社員の新規作成処理を行う(UserとEmployeeを同時作成)
def _create_employee(request):
    form = EmployeeForm(request.POST)
    if form.is_valid():
        employee = form.save()
        messages.success(request, '社員を登録しました。')
        return redirect('app:employee_show', pk=employee.pk)
    return _render_new_form(request, form)


# 社員新規作成フォームのレンダリング
def _render_new_form(request, form):
    return render(request, 'app/employee/new.html', {'form': form})


# 編集フォームを表示する
def _display_edit_form(request, employee):
    form = EmployeeForm(instance=employee)
    return _render_edit_form(request, employee, form)


# 社員の更新処理を行う
def _update_employee(request, employee):
    form = EmployeeForm(request.POST, instance=employee)
    if form.is_valid():
        form.save()
        messages.success(request, '社員情報を更新しました。')
        return redirect('app:employee_show', pk=employee.pk)
    return _render_edit_form(request, employee, form)


# 社員編集フォームのレンダリング
def _render_edit_form(request, employee, form):
    return render(request, 'app/employee/edit.html', {'form': form, 'employee': employee})
