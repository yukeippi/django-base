import pytest
from app.models import Task


@pytest.mark.django_db
class TestTaskIndexView:

    # 未ログインの場合、ログインページにリダイレクトされることを確認
    def test_index_requires_login(self, client):
        response = client.get('/tasks/')
        assert response.status_code == 302
        assert response.url.startswith('/login/')

    # タスクが無い場合、空の一覧が返ることを確認
    def test_index_with_no_tasks(self, auth_client):
        response = auth_client.get('/tasks/')
        assert response.status_code == 200
        assert list(response.context['tasks']) == []

    # タスクが一覧に表示されることを確認
    def test_index_with_tasks(self, auth_client):
        Task.objects.create(title='Task 1')
        Task.objects.create(title='Task 2')

        response = auth_client.get('/tasks/')
        assert response.status_code == 200
        assert len(response.context['tasks']) == 2


@pytest.mark.django_db
class TestTaskShowView:

    # 未ログインの場合、ログインページにリダイレクトされることを確認
    def test_show_requires_login(self, client):
        task = Task.objects.create(title='Task Detail')
        response = client.get(f'/tasks/{task.id}/')
        assert response.status_code == 302
        assert response.url.startswith('/login/')

    # 存在するタスクの詳細が取得できることを確認
    def test_show_existing_task(self, auth_client):
        task = Task.objects.create(title='Task Detail')

        response = auth_client.get(f'/tasks/{task.id}/')
        assert response.status_code == 200
        assert response.context['task'] == task

    # 存在しないタスクの場合404が返ることを確認
    def test_show_nonexistent_task_returns_404(self, auth_client):
        response = auth_client.get('/tasks/9999/')
        assert response.status_code == 404

    # 誰のタスクでも一覧・詳細は閲覧できる(閲覧に所有者制限は無い)ことを確認
    def test_show_task_owned_by_other_user(self, auth_client, other_user):
        task = Task.objects.create(title='Other User Task', created_by=other_user)

        response = auth_client.get(f'/tasks/{task.id}/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestTaskCreateView:

    # GETリクエストでフォームが表示されることを確認
    def test_get_returns_form(self, auth_client):
        response = auth_client.get('/tasks/new/')
        assert response.status_code == 200
        assert 'form' in response.context

    # 有効なデータでPOSTするとタスクが作成され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_creates_task_and_redirects(self, auth_client):
        response = auth_client.post('/tasks/new/', {
            'title': 'Client Created Task',
            'description': '',
            'status': 'todo',
            'priority': 3,
        })

        task = Task.objects.get(title='Client Created Task')
        assert response.status_code == 302
        assert response.url == f'/tasks/{task.id}/'

    # 作成者(created_by)がログインユーザーとして自動設定されることを確認
    def test_post_valid_data_sets_created_by(self, auth_client, sample_user):
        auth_client.post('/tasks/new/', {
            'title': 'Task With Creator',
            'description': '',
            'status': 'todo',
            'priority': 3,
        })

        task = Task.objects.get(title='Task With Creator')
        assert task.created_by == sample_user

    # 無効なデータでPOSTするとフォームが再表示されることを確認
    def test_post_invalid_data_redisplays_form(self, auth_client):
        response = auth_client.post('/tasks/new/', {
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
    def test_get_returns_form_with_instance(self, auth_client, sample_user):
        task = Task.objects.create(title='Original Title', created_by=sample_user)

        response = auth_client.get(f'/tasks/{task.id}/edit/')
        assert response.status_code == 200
        assert response.context['form'].instance == task

    # 有効なデータでPOSTするとタスクが更新され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_updates_task_and_redirects(self, auth_client, sample_user):
        task = Task.objects.create(title='Original Title', created_by=sample_user)

        response = auth_client.post(f'/tasks/{task.id}/edit/', {
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
    def test_edit_nonexistent_task_returns_404(self, auth_client):
        response = auth_client.get('/tasks/9999/edit/')
        assert response.status_code == 404

    # 無効なデータでPOSTするとフォームが再表示されることを確認
    def test_post_invalid_data_redisplays_form(self, auth_client, sample_user):
        task = Task.objects.create(title='Original Title', created_by=sample_user)

        response = auth_client.post(f'/tasks/{task.id}/edit/', {
            'title': '',
            'description': '',
            'status': 'todo',
            'priority': 3,
        })

        assert response.status_code == 200
        assert response.context['form'].is_valid() is False

        task.refresh_from_db()
        assert task.title == 'Original Title'

    # 作成者でも担当者でもない一般ユーザーが編集しようとすると403が返ることを確認
    def test_edit_by_unrelated_user_returns_403(self, other_auth_client, sample_user):
        task = Task.objects.create(title='Original Title', created_by=sample_user)

        response = other_auth_client.get(f'/tasks/{task.id}/edit/')
        assert response.status_code == 403

    # 作成者でも担当者でもない一般ユーザーがPOSTで更新しようとすると403が返り、タスクが変更されないことを確認
    def test_edit_by_unrelated_user_post_returns_403(self, other_auth_client, sample_user):
        task = Task.objects.create(title='Original Title', created_by=sample_user)

        response = other_auth_client.post(f'/tasks/{task.id}/edit/', {
            'title': 'Hacked Title',
            'description': '',
            'status': 'todo',
            'priority': 3,
        })

        task.refresh_from_db()
        assert response.status_code == 403
        assert task.title == 'Original Title'

    # 担当者は編集できることを確認
    def test_edit_by_assigned_user_succeeds(self, other_auth_client, sample_user, other_user):
        task = Task.objects.create(title='Original Title', created_by=sample_user, assigned_to=other_user)

        response = other_auth_client.get(f'/tasks/{task.id}/edit/')
        assert response.status_code == 200

    # 担当者はPOSTで更新を完了できることを確認
    def test_edit_by_assigned_user_can_update(self, other_auth_client, sample_user, other_user):
        task = Task.objects.create(title='Original Title', created_by=sample_user, assigned_to=other_user)

        response = other_auth_client.post(f'/tasks/{task.id}/edit/', {
            'title': 'Updated By Assignee',
            'description': '',
            'status': 'todo',
            'priority': 3,
        })

        task.refresh_from_db()
        assert response.status_code == 302
        assert task.title == 'Updated By Assignee'

    # 管理者は誰のタスクでも編集できることを確認
    def test_edit_by_admin_succeeds(self, admin_client, sample_user):
        task = Task.objects.create(title='Original Title', created_by=sample_user)

        response = admin_client.get(f'/tasks/{task.id}/edit/')
        assert response.status_code == 200

    # 管理者はPOSTで誰のタスクでも更新を完了できることを確認
    def test_edit_by_admin_can_update(self, admin_client, sample_user):
        task = Task.objects.create(title='Original Title', created_by=sample_user)

        response = admin_client.post(f'/tasks/{task.id}/edit/', {
            'title': 'Updated By Admin',
            'description': '',
            'status': 'todo',
            'priority': 3,
        })

        task.refresh_from_db()
        assert response.status_code == 302
        assert task.title == 'Updated By Admin'


@pytest.mark.django_db
class TestTaskDeleteView:

    # GETリクエストで削除確認ページが表示されることを確認
    def test_get_returns_confirmation_page(self, auth_client, sample_user):
        task = Task.objects.create(title='To Delete', created_by=sample_user)

        response = auth_client.get(f'/tasks/{task.id}/delete/')
        assert response.status_code == 200
        assert response.context['task'] == task

    # POSTするとタスクが削除され一覧ページにリダイレクトされることを確認
    def test_post_deletes_task_and_redirects_to_index(self, auth_client, sample_user):
        task = Task.objects.create(title='To Delete', created_by=sample_user)

        response = auth_client.post(f'/tasks/{task.id}/delete/')

        assert response.status_code == 302
        assert response.url == '/tasks/'
        assert Task.objects.filter(id=task.id).count() == 0

    # 存在しないタスクの場合404が返ることを確認
    def test_delete_nonexistent_task_returns_404(self, auth_client):
        response = auth_client.get('/tasks/9999/delete/')
        assert response.status_code == 404

    # 作成者でも担当者でもない一般ユーザーが削除しようとすると403が返り、タスクが削除されないことを確認
    def test_delete_by_unrelated_user_returns_403(self, other_auth_client, sample_user):
        task = Task.objects.create(title='Protected Task', created_by=sample_user)

        response = other_auth_client.post(f'/tasks/{task.id}/delete/')

        assert response.status_code == 403
        assert Task.objects.filter(id=task.id).count() == 1
