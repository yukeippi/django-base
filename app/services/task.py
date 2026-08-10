from django.contrib.auth.models import User
from app.forms.task import TaskForm
from app.models import Task


# タスクを作成する
def create(*, form: TaskForm, created_by: User) -> Task:
    task = form.save(commit=False)
    task.created_by = created_by
    task.save()
    return task


# タスクを更新する
def update(*, task: Task, form: TaskForm) -> Task:
    return form.save()


# タスクを削除する
def delete(*, task: Task) -> None:
    task.delete()
