import pytest
from app.forms.task import TaskForm
from app.models import Task
from app.services import task as task_service


@pytest.mark.django_db
class TestCreate:

    # 有効なフォームからタスクが作成され、created_byが設定されることを確認
    def test_creates_task_with_created_by(self, sample_user):
        form = TaskForm(data={'title': '新しいタスク', 'description': '', 'status': 'todo', 'priority': 3})
        assert form.is_valid()

        task = task_service.create(form=form, created_by=sample_user)

        assert task.id is not None
        assert task.title == '新しいタスク'
        assert task.created_by == sample_user


@pytest.mark.django_db
class TestUpdate:

    # 有効なフォームでタスクが更新されることを確認
    def test_updates_task_fields(self, sample_user):
        task = Task.objects.create(title='元のタスク', created_by=sample_user)
        form = TaskForm(
            data={'title': '更新後のタスク', 'description': '', 'status': 'todo', 'priority': 3}, instance=task
        )
        assert form.is_valid()

        updated_task = task_service.update(task=task, form=form)

        assert updated_task.title == '更新後のタスク'


@pytest.mark.django_db
class TestDelete:

    # タスクが削除されることを確認
    def test_deletes_task(self, sample_user):
        task = Task.objects.create(title='削除するタスク', created_by=sample_user)

        task_service.delete(task=task)

        assert Task.objects.filter(id=task.id).count() == 0
