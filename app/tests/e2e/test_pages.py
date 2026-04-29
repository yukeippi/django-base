import pytest
from playwright.sync_api import Page, expect


@pytest.mark.django_db
class TestHomePage:
    """
    ホームページのE2Eテスト
    """

    def test_home_page_loads(self, page: Page, live_server_url):
        """
        ホームページが正常に読み込まれることを確認
        """
        page.goto(live_server_url)

        # タイトルの確認
        title_element = page.locator('#title')
        expect(title_element).to_have_text('Task Manager')

        # リンクの存在確認
        tasks_link = page.locator('#tasks-link')
        expect(tasks_link).to_be_visible()

    def test_navigation_to_task_list(self, page: Page, live_server_url):
        """
        タスク一覧ページへのナビゲーションが機能することを確認
        """
        page.goto(live_server_url)

        # タスク一覧リンクをクリック
        page.click('#tasks-link')

        # URLが変わったことを確認
        expect(page).to_have_url(f'{live_server_url}/tasks/')


@pytest.mark.django_db
class TestTaskListPage:
    """
    タスク一覧ページのE2Eテスト
    """

    def test_task_list_page_with_no_tasks(self, page: Page, live_server_url):
        """
        タスクが存在しない場合の表示を確認
        """
        page.goto(f'{live_server_url}/tasks/')

        # タスクがない場合のメッセージを確認
        no_tasks_message = page.locator('#no-tasks')
        expect(no_tasks_message).to_be_visible()
        expect(no_tasks_message).to_have_text('タスクがありません。')

    def test_task_list_page_with_tasks(self, page: Page, live_server_url, setup_test_data):
        """
        タスクが存在する場合、タスク一覧が表示されることを確認
        """
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

    def test_task_list_displays_correct_columns(self, page: Page, live_server_url, setup_test_data):
        """
        タスク一覧テーブルに正しいカラムが表示されることを確認
        """
        page.goto(f'{live_server_url}/tasks/')

        # ヘッダーの確認
        headers = page.locator('th')
        expect(headers.nth(0)).to_have_text('タイトル')
        expect(headers.nth(1)).to_have_text('ステータス')
        expect(headers.nth(2)).to_have_text('優先度')
        expect(headers.nth(3)).to_have_text('作成日時')


@pytest.mark.django_db
class TestTaskAPI:
    """
    タスクAPIのE2Eテスト
    """

    def test_task_api_returns_json(self, page: Page, live_server_url, setup_test_data):
        """
        タスクAPIがJSON形式でデータを返すことを確認
        """
        response = page.goto(f'{live_server_url}/api/tasks/')

        # ステータスコードの確認
        assert response.status == 200

        # Content-Typeの確認
        content_type = response.headers.get('content-type')
        assert 'application/json' in content_type

    def test_task_api_returns_correct_data(self, page: Page, live_server_url, setup_test_data):
        """
        タスクAPIが正しいデータを返すことを確認
        """
        page.goto(f'{live_server_url}/api/tasks/')

        # ページのコンテンツを取得
        content = page.content()

        # タスクのタイトルが含まれていることを確認
        assert 'E2E Test Task 1' in content
        assert 'E2E Test Task 2' in content
        assert 'E2E Test Task 3' in content


@pytest.mark.django_db
class TestResponsiveness:
    """
    レスポンシブデザインのE2Eテスト
    """

    def test_mobile_viewport(self, page: Page, live_server_url):
        """
        モバイル表示で正常に動作することを確認
        """
        # モバイルビューポートに設定
        page.set_viewport_size({"width": 375, "height": 667})

        page.goto(live_server_url)

        # ページが正常に読み込まれることを確認
        title_element = page.locator('#title')
        expect(title_element).to_be_visible()

    def test_tablet_viewport(self, page: Page, live_server_url):
        """
        タブレット表示で正常に動作することを確認
        """
        # タブレットビューポートに設定
        page.set_viewport_size({"width": 768, "height": 1024})

        page.goto(live_server_url)

        # ページが正常に読み込まれることを確認
        title_element = page.locator('#title')
        expect(title_element).to_be_visible()
