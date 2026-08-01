from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


# ログイン
def login(request):
    if request.method == 'POST':
        return _authenticate_user(request)
    return _display_login_form(request)


# ログアウト
def logout(request):
    if request.method == 'POST':
        auth_logout(request)
        messages.success(request, 'ログアウトしました。')
    return redirect('app:login')


# ============================================================
# ここから先はprivateヘルパー
# ============================================================


# ログインフォームを表示する
def _display_login_form(request):
    form = AuthenticationForm(request)
    return _render_login_form(request, form)


# ログイン処理を行う
def _authenticate_user(request):
    form = AuthenticationForm(request, data=request.POST)
    if not form.is_valid():
        return _render_login_form(request, form)
    auth_login(request, form.get_user())
    messages.success(request, 'ログインしました。')
    return redirect(_safe_next_url(request) or 'app:task_index')


# next先が同一オリジンのURLであればそれを返す(オープンリダイレクト対策)
def _safe_next_url(request):
    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return None


# ログインフォームのレンダリング
def _render_login_form(request, form):
    return render(request, 'app/auth/login.html', {'form': form})
