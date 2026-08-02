from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from app.forms import ManagementGroupForm
from app.models import ManagementGroup
from app.lib.permissions import is_admin


# 管理グループ一覧
@login_required
def index(request):
    _require_admin(request)
    groups_qs = ManagementGroup.objects.all()
    paginator = Paginator(groups_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'app/management_group/index.html', {
        'management_groups': page_obj,
        'page_obj': page_obj,
    })


# 管理グループ詳細
@login_required
def show(request, pk):
    _require_admin(request)
    management_group = get_object_or_404(ManagementGroup, pk=pk)
    return render(request, 'app/management_group/show.html', {'management_group': management_group})


# 管理グループ新規作成
@login_required
def new(request):
    _require_admin(request)
    if request.method == 'POST':
        return _create_management_group(request)
    return _display_new_form(request)


# 管理グループ編集
@login_required
def edit(request, pk):
    _require_admin(request)
    management_group = get_object_or_404(ManagementGroup, pk=pk)
    if request.method == 'POST':
        return _update_management_group(request, management_group)
    return _display_edit_form(request, management_group)


# 管理グループ削除
@login_required
def delete(request, pk):
    _require_admin(request)
    management_group = get_object_or_404(ManagementGroup, pk=pk)
    if request.method == 'POST':
        management_group.delete()
        messages.success(request, '管理グループを削除しました。')
        return redirect('app:management_group_index')
    return render(request, 'app/management_group/delete.html', {'management_group': management_group})


# ============================================================
# ここから先はprivateヘルパー
# ============================================================


# 管理グループの操作はis_staffのみ許可する
def _require_admin(request):
    if not is_admin(request.user):
        raise PermissionDenied


# 新規作成フォームを表示する
def _display_new_form(request):
    form = ManagementGroupForm()
    return _render_new_form(request, form)


# 管理グループの新規作成処理を行う
def _create_management_group(request):
    form = ManagementGroupForm(request.POST)
    if form.is_valid():
        management_group = form.save()
        messages.success(request, '管理グループを作成しました。')
        return redirect('app:management_group_show', pk=management_group.pk)
    return _render_new_form(request, form)


# 管理グループ新規作成フォームのレンダリング
def _render_new_form(request, form):
    return render(request, 'app/management_group/new.html', {'form': form})


# 編集フォームを表示する
def _display_edit_form(request, management_group):
    form = ManagementGroupForm(instance=management_group)
    return _render_edit_form(request, management_group, form)


# 管理グループの更新処理を行う
def _update_management_group(request, management_group):
    form = ManagementGroupForm(request.POST, instance=management_group)
    if form.is_valid():
        form.save()
        messages.success(request, '管理グループを更新しました。')
        return redirect('app:management_group_show', pk=management_group.pk)
    return _render_edit_form(request, management_group, form)


# 管理グループ編集フォームのレンダリング
def _render_edit_form(request, management_group, form):
    return render(request, 'app/management_group/edit.html', {
        'form': form, 'management_group': management_group,
    })
