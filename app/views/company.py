from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from app.forms import CompanyForm
from app.models import Company


# 会社一覧
# TODO: 権限制御を再設計後、閲覧範囲を絞り込む
@login_required
def index(request):
    companies_qs = Company.objects.all()
    paginator = Paginator(companies_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'app/company/index.html', {
        'companies': page_obj,
        'page_obj': page_obj,
    })


# 会社詳細
@login_required
def show(request, pk):
    company = get_object_or_404(Company, pk=pk)
    return render(request, 'app/company/show.html', {'company': company})


# 会社新規作成
# TODO: 権限制御を再設計後、作成可否をチェックする
@login_required
def new(request):
    if request.method == 'POST':
        return _create_company(request)
    return _display_new_form(request)


# 会社編集
# TODO: 権限制御を再設計後、編集可否をチェックする
@login_required
def edit(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        return _update_company(request, company)
    return _display_edit_form(request, company)


# 会社削除
# TODO: 権限制御を再設計後、削除可否をチェックする
@login_required
def delete(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        company.delete()
        messages.success(request, '会社を削除しました。')
        return redirect('app:company_index')
    return render(request, 'app/company/delete.html', {'company': company})


# ============================================================
# ここから先はprivateヘルパー
# ============================================================


# 新規作成フォームを表示する
def _display_new_form(request):
    form = CompanyForm()
    return _render_new_form(request, form)


# 会社の新規作成処理を行う
def _create_company(request):
    form = CompanyForm(request.POST)
    if form.is_valid():
        company = form.save()
        messages.success(request, '会社を作成しました。')
        return redirect('app:company_show', pk=company.pk)
    return _render_new_form(request, form)


# 会社新規作成フォームのレンダリング
def _render_new_form(request, form):
    return render(request, 'app/company/new.html', {'form': form})


# 編集フォームを表示する
def _display_edit_form(request, company):
    form = CompanyForm(instance=company)
    return _render_edit_form(request, company, form)


# 会社の更新処理を行う
def _update_company(request, company):
    form = CompanyForm(request.POST, instance=company)
    if form.is_valid():
        form.save()
        messages.success(request, '会社情報を更新しました。')
        return redirect('app:company_show', pk=company.pk)
    return _render_edit_form(request, company, form)


# 会社編集フォームのレンダリング
def _render_edit_form(request, company, form):
    return render(request, 'app/company/edit.html', {'form': form, 'company': company})
