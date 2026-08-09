import pytest
from playwright.sync_api import Page, expect


# 会社の新規作成〜詳細確認〜編集〜削除までの一連のE2Eテスト
@pytest.mark.django_db
class TestCompanyCrudFlow:

    # 新規作成フォームから会社を登録すると詳細ページに遷移することを確認
    def test_create_company_and_view_detail(self, logged_in_page: Page, live_server_url):
        logged_in_page.goto(f'{live_server_url}/companies/new/')

        logged_in_page.fill('#id_name', 'E2Eテスト株式会社')
        logged_in_page.click('#company-form-submit')

        expect(logged_in_page.locator('#company-name')).to_have_text('E2Eテスト株式会社')

    # 詳細ページから編集し、会社名が更新されることを確認
    def test_edit_company_updates_name(self, logged_in_page: Page, live_server_url):
        logged_in_page.goto(f'{live_server_url}/companies/new/')
        logged_in_page.fill('#id_name', '編集前株式会社')
        logged_in_page.click('#company-form-submit')

        logged_in_page.click('#edit-company-link')
        logged_in_page.fill('#id_name', '編集後株式会社')
        logged_in_page.click('#company-form-submit')

        expect(logged_in_page.locator('#company-name')).to_have_text('編集後株式会社')

    # 削除確認ページから削除すると一覧ページに戻り、対象が表示されなくなることを確認
    def test_delete_company_removes_from_list(self, logged_in_page: Page, live_server_url):
        logged_in_page.goto(f'{live_server_url}/companies/new/')
        logged_in_page.fill('#id_name', '削除対象株式会社')
        logged_in_page.click('#company-form-submit')

        logged_in_page.click('#delete-company-link')
        logged_in_page.click('#company-delete-confirm')

        expect(logged_in_page).to_have_url(f'{live_server_url}/companies/')
        expect(logged_in_page.locator('#no-companies')).to_be_visible()


# 未ログイン時のアクセス制御に関するE2Eテスト
@pytest.mark.django_db
class TestCompanyAccessControl:

    # 未ログインで会社一覧にアクセスするとログインページにリダイレクトされることを確認
    def test_company_index_redirects_anonymous_user_to_login(self, page: Page, live_server_url):
        page.goto(f'{live_server_url}/companies/')
        expect(page).to_have_url(f'{live_server_url}/login/?next=/companies/')
