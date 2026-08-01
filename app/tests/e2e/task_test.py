import pytest
from playwright.sync_api import Page, expect


# タスク一覧ページのE2Eテスト
@pytest.mark.django_db
class TestTaskListPage:

    # タスクが存在しない場合の表示を確認
    def test_task_list_page_with_no_tasks(self, logged_in_page: Page, live_server_url):
        logged_in_page.goto(f'{live_server_url}/tasks/')

        # タスクがない場合のメッセージを確認
        no_tasks_message = logged_in_page.locator('#no-tasks')
        expect(no_tasks_message).to_be_visible()
        expect(no_tasks_message).to_have_text('タスクがありません。')

    # タスクが存在する場合、タスク一覧が表示されることを確認
    def test_task_list_page_with_tasks(self, logged_in_page: Page, live_server_url, setup_test_data):
        logged_in_page.goto(f'{live_server_url}/tasks/')

        # タスクテーブルの確認
        task_table = logged_in_page.locator('#task-table')
        expect(task_table).to_be_visible()

        # タスク行の数を確認
        task_rows = logged_in_page.locator('.task-row')
        expect(task_rows).to_have_count(setup_test_data['task_count'])

        # 最初のタスクのタイトルを確認
        first_task = task_rows.first
        expect(first_task).to_contain_text('E2E Test Task')

    # タスク一覧テーブルに正しいカラムが表示されることを確認
    def test_task_list_displays_correct_columns(self, logged_in_page: Page, live_server_url, setup_test_data):
        logged_in_page.goto(f'{live_server_url}/tasks/')

        # ヘッダーの確認
        headers = logged_in_page.locator('th')
        expect(headers.nth(0)).to_have_text('タイトル')
        expect(headers.nth(1)).to_have_text('ステータス')
        expect(headers.nth(2)).to_have_text('優先度')
        expect(headers.nth(3)).to_have_text('作成日時')


# 未ログイン時のアクセス制御に関するE2Eテスト
@pytest.mark.django_db
class TestTaskAccessControl:

    # 未ログインでタスク一覧にアクセスするとログインページにリダイレクトされることを確認
    def test_task_index_redirects_anonymous_user_to_login(self, page: Page, live_server_url):
        page.goto(f'{live_server_url}/tasks/')
        expect(page).to_have_url(f'{live_server_url}/login/?next=/tasks/')


# タスクAPIのE2Eテスト
@pytest.mark.django_db
class TestTaskAPI:

    # タスクAPIがJSON形式でデータを返すことを確認
    def test_task_api_returns_json(self, logged_in_page: Page, live_server_url, setup_test_data):
        response = logged_in_page.goto(f'{live_server_url}/api/tasks/')

        # ステータスコードの確認
        assert response.status == 200

        # Content-Typeの確認
        content_type = response.headers.get('content-type')
        assert 'application/json' in content_type

    # タスクAPIが正しいデータを返すことを確認
    def test_task_api_returns_correct_data(self, logged_in_page: Page, live_server_url, setup_test_data):
        logged_in_page.goto(f'{live_server_url}/api/tasks/')

        # ページのコンテンツを取得
        content = logged_in_page.content()

        # タスクのタイトルが含まれていることを確認
        assert 'E2E Test Task 1' in content
        assert 'E2E Test Task 2' in content
        assert 'E2E Test Task 3' in content


@pytest.mark.django_db
class TestTaskCreatePage:

    # 新規作成フォームが表示されることを確認
    def test_new_task_form_displays(self, logged_in_page: Page, live_server_url):
        logged_in_page.goto(f'{live_server_url}/tasks/new/')

        expect(logged_in_page.locator('#task-form')).to_be_visible()

    # タスクを新規作成すると詳細ページにリダイレクトされ、成功メッセージが表示されることを確認
    def test_create_task_redirects_to_detail(self, logged_in_page: Page, live_server_url):
        logged_in_page.goto(f'{live_server_url}/tasks/new/')

        logged_in_page.fill('#id_title', 'Created via E2E')
        logged_in_page.select_option('#id_status', 'todo')
        logged_in_page.fill('#id_priority', '2')
        logged_in_page.click('#task-form-submit')

        expect(logged_in_page.locator('#task-title')).to_have_text('Created via E2E')
        expect(logged_in_page.locator('.messages')).to_contain_text('タスクを作成しました。')


@pytest.mark.django_db
class TestTaskEditPage:

    # タスクを編集すると詳細ページにリダイレクトされ、成功メッセージが表示されることを確認
    def test_edit_task_updates_and_redirects(self, logged_in_page: Page, live_server_url, e2e_user):
        from app.models import Task
        task = Task.objects.create(title='Before Edit', status='todo', priority=3, created_by=e2e_user)

        logged_in_page.goto(f'{live_server_url}/tasks/{task.id}/edit/')
        logged_in_page.fill('#id_title', 'After Edit')
        logged_in_page.click('#task-form-submit')

        expect(logged_in_page.locator('#task-title')).to_have_text('After Edit')
        expect(logged_in_page.locator('.messages')).to_contain_text('タスクを更新しました。')


@pytest.mark.django_db
class TestTaskDeletePage:

    # タスクを削除すると一覧ページにリダイレクトされ、成功メッセージが表示されることを確認
    def test_delete_task_removes_and_redirects_to_index(self, logged_in_page: Page, live_server_url, e2e_user):
        from app.models import Task
        task = Task.objects.create(title='To Delete', created_by=e2e_user)

        logged_in_page.goto(f'{live_server_url}/tasks/{task.id}/delete/')
        expect(logged_in_page.locator('#delete-task-title')).to_have_text('To Delete')

        logged_in_page.click('#task-delete-confirm')

        expect(logged_in_page).to_have_url(f'{live_server_url}/tasks/')
        expect(logged_in_page.locator('.messages')).to_contain_text('タスクを削除しました。')
        assert Task.objects.filter(id=task.id).count() == 0


@pytest.mark.django_db
class TestTaskFullCrudFlow:

    # 新規作成→編集→削除までの一連の操作が正しく機能することを確認
    def test_create_edit_delete_flow(self, logged_in_page: Page, live_server_url):
        # 新規作成
        logged_in_page.goto(f'{live_server_url}/tasks/')
        logged_in_page.click('#new-task-link')
        logged_in_page.fill('#id_title', 'Full Flow Task')
        logged_in_page.select_option('#id_status', 'todo')
        logged_in_page.fill('#id_priority', '3')
        logged_in_page.click('#task-form-submit')
        expect(logged_in_page.locator('#task-title')).to_have_text('Full Flow Task')

        # 編集
        logged_in_page.click('#edit-task-link')
        logged_in_page.fill('#id_title', 'Full Flow Task Updated')
        logged_in_page.click('#task-form-submit')
        expect(logged_in_page.locator('#task-title')).to_have_text('Full Flow Task Updated')

        # 削除
        logged_in_page.click('#delete-task-link')
        logged_in_page.click('#task-delete-confirm')
        expect(logged_in_page).to_have_url(f'{live_server_url}/tasks/')
        expect(logged_in_page.locator('#no-tasks')).to_be_visible()
