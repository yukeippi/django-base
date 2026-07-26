import pytest
from playwright.sync_api import Page, expect


# ホームページのE2Eテスト
@pytest.mark.django_db
class TestHomePage:

    # ホームページが正常に読み込まれることを確認
    def test_home_page_loads(self, page: Page, live_server_url):
        page.goto(live_server_url)

        # タイトルの確認
        title_element = page.locator('#title')
        expect(title_element).to_have_text('Task Manager')

        # リンクの存在確認
        tasks_link = page.locator('#tasks-link')
        expect(tasks_link).to_be_visible()

    # タスク一覧ページへのナビゲーションが機能することを確認
    def test_navigation_to_task_list(self, page: Page, live_server_url):
        page.goto(live_server_url)

        # タスク一覧リンクをクリック
        page.click('#tasks-link')

        # URLが変わったことを確認
        expect(page).to_have_url(f'{live_server_url}/tasks/')


# レスポンシブデザインのE2Eテスト
@pytest.mark.django_db
class TestResponsiveness:

    # モバイル表示で正常に動作することを確認
    def test_mobile_viewport(self, page: Page, live_server_url):
        # モバイルビューポートに設定
        page.set_viewport_size({"width": 375, "height": 667})

        page.goto(live_server_url)

        # ページが正常に読み込まれることを確認
        title_element = page.locator('#title')
        expect(title_element).to_be_visible()

    # タブレット表示で正常に動作することを確認
    def test_tablet_viewport(self, page: Page, live_server_url):
        # タブレットビューポートに設定
        page.set_viewport_size({"width": 768, "height": 1024})

        page.goto(live_server_url)

        # ページが正常に読み込まれることを確認
        title_element = page.locator('#title')
        expect(title_element).to_be_visible()
