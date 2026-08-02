import pytest
from playwright.sync_api import Page, expect
from app.models import Company


# 部門の新規作成〜詳細確認〜編集〜削除までの一連のE2Eテスト
@pytest.mark.django_db
class TestDepartmentCrudFlow:

    # 新規作成フォームから部門を登録すると詳細ページに遷移することを確認
    def test_create_department_and_view_detail(self, logged_in_page: Page, live_server_url):
        company = Company.objects.create(name='E2Eテスト株式会社')

        logged_in_page.goto(f'{live_server_url}/departments/new/')
        logged_in_page.select_option('#id_company', str(company.id))
        logged_in_page.fill('#id_name', '開発部')
        logged_in_page.click('#department-form-submit')

        expect(logged_in_page.locator('#department-name')).to_have_text('開発部')
        expect(logged_in_page.locator('#department-company')).to_have_text('E2Eテスト株式会社')

    # 詳細ページから編集し、部門名が更新されることを確認
    def test_edit_department_updates_name(self, logged_in_page: Page, live_server_url):
        company = Company.objects.create(name='E2Eテスト株式会社')
        logged_in_page.goto(f'{live_server_url}/departments/new/')
        logged_in_page.select_option('#id_company', str(company.id))
        logged_in_page.fill('#id_name', '編集前部門')
        logged_in_page.click('#department-form-submit')

        logged_in_page.click('#edit-department-link')
        logged_in_page.fill('#id_name', '編集後部門')
        logged_in_page.click('#department-form-submit')

        expect(logged_in_page.locator('#department-name')).to_have_text('編集後部門')

    # 削除確認ページから削除すると一覧ページに戻り、対象が表示されなくなることを確認
    def test_delete_department_removes_from_list(self, logged_in_page: Page, live_server_url):
        company = Company.objects.create(name='E2Eテスト株式会社')
        logged_in_page.goto(f'{live_server_url}/departments/new/')
        logged_in_page.select_option('#id_company', str(company.id))
        logged_in_page.fill('#id_name', '削除対象部門')
        logged_in_page.click('#department-form-submit')

        logged_in_page.click('#delete-department-link')
        logged_in_page.click('#department-delete-confirm')

        expect(logged_in_page).to_have_url(f'{live_server_url}/departments/')
        expect(logged_in_page.locator('#no-departments')).to_be_visible()


# 未ログイン時のアクセス制御に関するE2Eテスト
@pytest.mark.django_db
class TestDepartmentAccessControl:

    # 未ログインで部門一覧にアクセスするとログインページにリダイレクトされることを確認
    def test_department_index_redirects_anonymous_user_to_login(self, page: Page, live_server_url):
        page.goto(f'{live_server_url}/departments/')
        expect(page).to_have_url(f'{live_server_url}/login/?next=/departments/')
