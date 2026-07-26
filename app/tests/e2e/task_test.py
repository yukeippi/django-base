import pytest
from playwright.sync_api import Page, expect


# タスク一覧ページのE2Eテスト
@pytest.mark.django_db
class TestTaskListPage:

    # タスクが存在しない場合の表示を確認
    def test_task_list_page_with_no_tasks(self, page: Page, live_server_url):
        page.goto(f'{live_server_url}/tasks/')

        # タスクがない場合のメッセージを確認
        no_tasks_message = page.locator('#no-tasks')
        expect(no_tasks_message).to_be_visible()
        expect(no_tasks_message).to_have_text('タスクがありません。')

    # タスクが存在する場合、タスク一覧が表示されることを確認
    def test_task_list_page_with_tasks(self, page: Page, live_server_url, setup_test_data):
        page.goto(f'{live_server_url}/tasks/')

        # タスクテーブルの確認
        task_table = page.locator('#task-table')
        expect(task_table).to_be_visible()

        # タスク行の数を確認
        task_rows = page.locator('.task-row')
        expect(task_rows).to_have_count(setup_test_data['task_count'])

        # 最初のタスクのタイトルを確認
        first_task = task_rows.first
        expect(first_task).to_contain_text('E2E Test Task')

    # タスク一覧テーブルに正しいカラムが表示されることを確認
    def test_task_list_displays_correct_columns(self, page: Page, live_server_url, setup_test_data):
        page.goto(f'{live_server_url}/tasks/')

        # ヘッダーの確認
        headers = page.locator('th')
        expect(headers.nth(0)).to_have_text('タイトル')
        expect(headers.nth(1)).to_have_text('ステータス')
        expect(headers.nth(2)).to_have_text('優先度')
        expect(headers.nth(3)).to_have_text('作成日時')


# タスクAPIのE2Eテスト
@pytest.mark.django_db
class TestTaskAPI:

    # タスクAPIがJSON形式でデータを返すことを確認
    def test_task_api_returns_json(self, page: Page, live_server_url, setup_test_data):
        response = page.goto(f'{live_server_url}/api/tasks/')

        # ステータスコードの確認
        assert response.status == 200

        # Content-Typeの確認
        content_type = response.headers.get('content-type')
        assert 'application/json' in content_type

    # タスクAPIが正しいデータを返すことを確認
    def test_task_api_returns_correct_data(self, page: Page, live_server_url, setup_test_data):
        page.goto(f'{live_server_url}/api/tasks/')

        # ページのコンテンツを取得
        content = page.content()

        # タスクのタイトルが含まれていることを確認
        assert 'E2E Test Task 1' in content
        assert 'E2E Test Task 2' in content
        assert 'E2E Test Task 3' in content
