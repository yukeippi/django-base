from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


# ログイン
def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            messages.success(request, 'ログインしました。')
            next_url = request.POST.get('next')
            # next先が同一オリジンでない場合(オープンリダイレクト)は無視する
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
            ):
                return redirect(next_url)
            return redirect('app:task_index')
    else:
        form = AuthenticationForm(request)
    return render(request, 'app/auth/login.html', {'form': form})


# ログアウト
def logout(request):
    if request.method == 'POST':
        auth_logout(request)
        messages.success(request, 'ログアウトしました。')
    return redirect('app:login')
