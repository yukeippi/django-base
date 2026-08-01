import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from app.models import Task


# Taskモデルのテストクラス
@pytest.mark.django_db
class TestTaskModel:

    # 最小限のフィールドでタスクを作成できることを確認
    def test_create_task_with_minimal_fields(self):
        task = Task.objects.create(title='Test Task')

        assert task.id is not None
        assert task.title == 'Test Task'
        assert task.description == ''
        assert task.status == 'todo'
        assert task.priority == 3
        assert task.assigned_to is None

    # 全フィールドを指定してタスクを作成できることを確認
    def test_create_task_with_all_fields(self, sample_user):
        due_date = date.today() + timedelta(days=7)
        task = Task.objects.create(
            title='Complete Task',
            description='This is a test task',
            status='in_progress',
            priority=1,
            assigned_to=sample_user,
            due_date=due_date
        )

        assert task.title == 'Complete Task'
        assert task.description == 'This is a test task'
        assert task.status == 'in_progress'
        assert task.priority == 1
        assert task.assigned_to == sample_user
        assert task.due_date == due_date

    # __str__メソッドがタイトルを返すことを確認
    def test_task_str_method(self):
        task = Task.objects.create(title='String Test Task')
        assert str(task) == 'String Test Task'

    # タスクが作成日時の降順でソートされることを確認
    def test_task_ordering(self):
        task1 = Task.objects.create(title='First Task')
        task2 = Task.objects.create(title='Second Task')
        task3 = Task.objects.create(title='Third Task')

        tasks = list(Task.objects.all())
        assert tasks[0] == task3
        assert tasks[1] == task2
        assert tasks[2] == task1

    # 期限が過去の場合、is_overdue()がTrueを返すことを確認
    def test_is_overdue_with_past_due_date(self):
        past_date = date.today() - timedelta(days=1)
        task = Task.objects.create(
            title='Overdue Task',
            due_date=past_date,
            status='in_progress'
        )
        assert task.is_overdue() is True

    # 期限が未来の場合、is_overdue()がFalseを返すことを確認
    def test_is_overdue_with_future_due_date(self):
        future_date = date.today() + timedelta(days=1)
        task = Task.objects.create(
            title='Future Task',
            due_date=future_date
        )
        assert task.is_overdue() is False

    # 期限が設定されていない場合、is_overdue()がFalseを返すことを確認
    def test_is_overdue_with_no_due_date(self):
        task = Task.objects.create(title='No Due Date Task')
        assert task.is_overdue() is False

    # 完了したタスクは期限を過ぎていてもis_overdue()がFalseを返すことを確認
    def test_is_overdue_completed_task(self):
        past_date = date.today() - timedelta(days=1)
        task = Task.objects.create(
            title='Completed Task',
            due_date=past_date,
            status='done'
        )
        assert task.is_overdue() is False

    # todoステータスのタスクは完了可能であることを確認
    def test_can_be_completed_todo_status(self):
        task = Task.objects.create(title='Todo Task', status='todo')
        assert task.can_be_completed() is True

    # in_progressステータスのタスクは完了可能であることを確認
    def test_can_be_completed_in_progress_status(self):
        task = Task.objects.create(title='In Progress Task', status='in_progress')
        assert task.can_be_completed() is True

    # doneステータスのタスクは完了不可であることを確認
    def test_can_be_completed_done_status(self):
        task = Task.objects.create(title='Done Task', status='done')
        assert task.can_be_completed() is False

    # 優先度が1-5の範囲外の場合、バリデーションエラーが発生することを確認
    def test_priority_validation(self):
        task = Task(title='Invalid Priority Task', priority=6)
        with pytest.raises(ValidationError):
            task.full_clean()

    # タスクとユーザーの関連が正しく機能することを確認
    def test_task_user_relationship(self, sample_user):
        task1 = Task.objects.create(title='Task 1', assigned_to=sample_user)
        task2 = Task.objects.create(title='Task 2', assigned_to=sample_user)

        user_tasks = sample_user.tasks.all()
        assert task1 in user_tasks
        assert task2 in user_tasks
        assert user_tasks.count() == 2

    # ユーザーが削除されてもタスクは削除されず、assigned_toがNullになることを確認
    def test_task_user_deletion_sets_null(self, sample_user):
        task = Task.objects.create(title='Task', assigned_to=sample_user)
        sample_user.delete()

        task.refresh_from_db()
        assert task.assigned_to is None
        assert task.id is not None
