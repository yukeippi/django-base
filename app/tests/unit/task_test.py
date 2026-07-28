import pytest
from datetime import date, timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from app.forms.task import TaskForm
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
        user_id = sample_user.id
        sample_user.delete()

        task.refresh_from_db()
        assert task.assigned_to is None
        assert task.id is not None


@pytest.mark.django_db
class TestTaskIndexView:

    # タスクが無い場合、空の一覧が返ることを確認
    def test_index_with_no_tasks(self, client):
        response = client.get('/tasks/')
        assert response.status_code == 200
        assert list(response.context['tasks']) == []

    # タスクが一覧に表示されることを確認
    def test_index_with_tasks(self, client):
        Task.objects.create(title='Task 1')
        Task.objects.create(title='Task 2')

        response = client.get('/tasks/')
        assert response.status_code == 200
        assert len(response.context['tasks']) == 2


@pytest.mark.django_db
class TestTaskShowView:

    # 存在するタスクの詳細が取得できることを確認
    def test_show_existing_task(self, client):
        task = Task.objects.create(title='Task Detail')

        response = client.get(f'/tasks/{task.id}/')
        assert response.status_code == 200
        assert response.context['task'] == task

    # 存在しないタスクの場合404が返ることを確認
    def test_show_nonexistent_task_returns_404(self, client):
        response = client.get('/tasks/9999/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestTaskForm:

    # 有効なデータでフォームが妥当と判定されることを確認
    def test_valid_data_is_valid(self):
        form = TaskForm(data={
            'title': 'New Task',
            'description': '',
            'status': 'todo',
            'priority': 3,
        })
        assert form.is_valid()

    # タイトル未入力の場合、フォームが無効と判定されることを確認
    def test_missing_title_is_invalid(self):
        form = TaskForm(data={
            'title': '',
            'description': '',
            'status': 'todo',
            'priority': 3,
        })
        assert not form.is_valid()
        assert 'title' in form.errors

    # 優先度が範囲外の場合、フォームが無効と判定されることを確認
    def test_priority_out_of_range_is_invalid(self):
        form = TaskForm(data={
            'title': 'Task',
            'description': '',
            'status': 'todo',
            'priority': 6,
        })
        assert not form.is_valid()
        assert 'priority' in form.errors

    # 担当者を指定してフォームを保存すると反映されることを確認
    def test_save_with_assigned_to(self):
        user = User.objects.create_user(username='formuser', password='pass12345')
        form = TaskForm(data={
            'title': 'Assigned Task',
            'description': '',
            'status': 'todo',
            'priority': 3,
            'assigned_to': user.id,
        })
        assert form.is_valid()
        task = form.save()
        assert task.assigned_to == user


@pytest.mark.django_db
class TestTaskCreateView:

    # GETリクエストでフォームが表示されることを確認
    def test_get_returns_form(self, client):
        response = client.get('/tasks/new/')
        assert response.status_code == 200
        assert 'form' in response.context

    # 有効なデータでPOSTするとタスクが作成され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_creates_task_and_redirects(self, client):
        response = client.post('/tasks/new/', {
            'title': 'Client Created Task',
            'description': '',
            'status': 'todo',
            'priority': 3,
        })

        task = Task.objects.get(title='Client Created Task')
        assert response.status_code == 302
        assert response.url == f'/tasks/{task.id}/'

    # 無効なデータでPOSTするとフォームが再表示されることを確認
    def test_post_invalid_data_redisplays_form(self, client):
        response = client.post('/tasks/new/', {
            'title': '',
            'description': '',
            'status': 'todo',
            'priority': 3,
        })

        assert response.status_code == 200
        assert response.context['form'].is_valid() is False


@pytest.mark.django_db
class TestTaskEditView:

    # GETリクエストで既存タスクの値がフォームに入っていることを確認
    def test_get_returns_form_with_instance(self, client):
        task = Task.objects.create(title='Original Title')

        response = client.get(f'/tasks/{task.id}/edit/')
        assert response.status_code == 200
        assert response.context['form'].instance == task

    # 有効なデータでPOSTするとタスクが更新され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_updates_task_and_redirects(self, client):
        task = Task.objects.create(title='Original Title')

        response = client.post(f'/tasks/{task.id}/edit/', {
            'title': 'Updated Title',
            'description': '',
            'status': 'todo',
            'priority': 3,
        })

        task.refresh_from_db()
        assert task.title == 'Updated Title'
        assert response.status_code == 302
        assert response.url == f'/tasks/{task.id}/'

    # 存在しないタスクの場合404が返ることを確認
    def test_edit_nonexistent_task_returns_404(self, client):
        response = client.get('/tasks/9999/edit/')
        assert response.status_code == 404

    # 無効なデータでPOSTするとフォームが再表示されることを確認
    def test_post_invalid_data_redisplays_form(self, client):
        task = Task.objects.create(title='Original Title')

        response = client.post(f'/tasks/{task.id}/edit/', {
            'title': '',
            'description': '',
            'status': 'todo',
            'priority': 3,
        })

        assert response.status_code == 200
        assert response.context['form'].is_valid() is False

        task.refresh_from_db()
        assert task.title == 'Original Title'


@pytest.mark.django_db
class TestTaskDeleteView:

    # GETリクエストで削除確認ページが表示されることを確認
    def test_get_returns_confirmation_page(self, client):
        task = Task.objects.create(title='To Delete')

        response = client.get(f'/tasks/{task.id}/delete/')
        assert response.status_code == 200
        assert response.context['task'] == task

    # POSTするとタスクが削除され一覧ページにリダイレクトされることを確認
    def test_post_deletes_task_and_redirects_to_index(self, client):
        task = Task.objects.create(title='To Delete')

        response = client.post(f'/tasks/{task.id}/delete/')

        assert response.status_code == 302
        assert response.url == '/tasks/'
        assert Task.objects.filter(id=task.id).count() == 0

    # 存在しないタスクの場合404が返ることを確認
    def test_delete_nonexistent_task_returns_404(self, client):
        response = client.get('/tasks/9999/delete/')
        assert response.status_code == 404
