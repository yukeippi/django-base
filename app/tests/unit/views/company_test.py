import pytest
from app.models import Company, Department, EmployeeDepartment, ManagementGroup

DEPARTMENT_VIEWER_ALL = 1
COMPANY_SCOPED_DEPARTMENT_MANAGER = 2


# admin_client(pytest-djangoのis_staffユーザー)を、新しいアクセス制御(ManagementGroup.is_admin)の
# 全社管理者グループにも所属させる(is_staffと新しいアクセス制御は別の仕組みのため)
@pytest.fixture(autouse=True)
def _grant_group_admin(admin_user):
    group = ManagementGroup.objects.create(name='test-admin-group', is_admin=True)
    group.members.add(admin_user)


@pytest.mark.django_db
class TestCompanyIndexView:

    # 未ログインの場合、ログインページにリダイレクトされることを確認
    def test_index_requires_login(self, client):
        response = client.get('/companies/')
        assert response.status_code == 302
        assert response.url.startswith('/login/')

    # 会社閲覧の権限が無いユーザーには一覧が0件になることを確認
    def test_index_by_user_without_permission_is_empty(self, auth_client):
        Company.objects.create(name='サンプル株式会社')

        response = auth_client.get('/companies/')
        assert response.status_code == 200
        assert len(response.context['companies']) == 0

    # 会社閲覧を許可する権限セットを持つユーザーには一覧に表示されることを確認
    def test_index_by_user_with_view_permission(self, sample_user, auth_client):
        company = Company.objects.create(name='サンプル株式会社')
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER)

        response = auth_client.get('/companies/')
        assert response.status_code == 200
        assert company in response.context['companies']

    # 管理者は一覧を取得できることを確認
    def test_index_by_admin_succeeds(self, admin_client):
        Company.objects.create(name='サンプル株式会社')

        response = admin_client.get('/companies/')
        assert response.status_code == 200
        assert len(response.context['companies']) == 1


@pytest.mark.django_db
class TestCompanyShowView:

    # 会社閲覧の権限が無いユーザーがアクセスすると403が返ることを確認
    def test_show_by_user_without_permission_returns_403(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')

        response = auth_client.get(f'/companies/{company.id}/')
        assert response.status_code == 403

    # 会社閲覧を許可する権限セットを持つユーザーは詳細を取得できることを確認
    def test_show_by_user_with_view_permission(self, sample_user, auth_client):
        company = Company.objects.create(name='サンプル株式会社')
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER)

        response = auth_client.get(f'/companies/{company.id}/')
        assert response.status_code == 200
        assert response.context['company'] == company

    # 存在しない会社の場合404が返ることを確認
    def test_show_nonexistent_company_returns_404(self, admin_client):
        response = admin_client.get('/companies/9999/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestCompanyCreateView:

    # 作成権限が無いユーザーがアクセスすると403が返ることを確認(会社閲覧のみの権限セットでは作成不可)
    def test_new_by_user_without_create_permission_returns_403(self, sample_user, auth_client):
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER)

        response = auth_client.get('/companies/new/')
        assert response.status_code == 403

    # 管理者はGETでフォームを取得できることを確認
    def test_get_returns_form(self, admin_client):
        response = admin_client.get('/companies/new/')
        assert response.status_code == 200
        assert 'form' in response.context

    # 管理者が有効なデータでPOSTすると会社が作成され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_creates_company_and_redirects(self, admin_client):
        response = admin_client.post('/companies/new/', {'name': 'サンプル株式会社'})

        company = Company.objects.get(name='サンプル株式会社')
        assert response.status_code == 302
        assert response.url == f'/companies/{company.id}/'

    # 管理者が無効なデータでPOSTするとフォームが再表示されることを確認
    def test_post_invalid_data_redisplays_form(self, admin_client):
        response = admin_client.post('/companies/new/', {'name': ''})

        assert response.status_code == 200
        assert response.context['form'].is_valid() is False


@pytest.mark.django_db
class TestCompanyEditView:

    # 編集権限が無いユーザーがアクセスすると403が返ることを確認
    def test_edit_by_user_without_permission_returns_403(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')

        response = auth_client.get(f'/companies/{company.id}/edit/')
        assert response.status_code == 403

    # 管理者が有効なデータでPOSTすると会社が更新され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_updates_company_and_redirects(self, admin_client):
        company = Company.objects.create(name='サンプル株式会社')

        response = admin_client.post(f'/companies/{company.id}/edit/', {'name': '更新後株式会社'})

        company.refresh_from_db()
        assert response.status_code == 302
        assert company.name == '更新後株式会社'

    # 存在しない会社の場合404が返ることを確認
    def test_edit_nonexistent_company_returns_404(self, admin_client):
        response = admin_client.get('/companies/9999/edit/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestCompanyDeleteView:

    # 削除権限が無いユーザーがアクセスすると403が返ることを確認
    def test_delete_by_user_without_permission_returns_403(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')

        response = auth_client.post(f'/companies/{company.id}/delete/')
        assert response.status_code == 403
        assert Company.objects.filter(id=company.id).count() == 1

    # 管理者はPOSTで削除でき、一覧ページにリダイレクトされることを確認
    def test_post_deletes_company_and_redirects_to_index(self, admin_client):
        company = Company.objects.create(name='サンプル株式会社')

        response = admin_client.post(f'/companies/{company.id}/delete/')

        assert response.status_code == 302
        assert response.url == '/companies/'
        assert Company.objects.filter(id=company.id).count() == 0

    # 存在しない会社の場合404が返ることを確認
    def test_delete_nonexistent_company_returns_404(self, admin_client):
        response = admin_client.get('/companies/9999/delete/')
        assert response.status_code == 404


def _grant(user, permission_set_id):
    company = Company.objects.create(name=f'権限セット{permission_set_id}用の会社')
    department = Department.objects.create(company=company, name='権限セット用部門')
    EmployeeDepartment.objects.create(employee=user.employee, department=department, is_primary=True)
    group = ManagementGroup.objects.create(
        name=f'test-group-{permission_set_id}-{user.username}', department=department, permission_set_id=permission_set_id
    )
    group.members.add(user)
