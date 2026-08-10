from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


# ホームページビュー
def index(request: HttpRequest) -> HttpResponse:
    return render(request, 'app/index.html', {
        'title': 'Task Manager',
    })
