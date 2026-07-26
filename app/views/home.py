from django.shortcuts import render


# ホームページビュー
def index(request):
    return render(request, 'app/index.html', {
        'title': 'Task Manager',
    })
