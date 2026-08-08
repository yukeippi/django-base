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
class TestDepartmentIndexView:

    # 未ログインの場合、ログインページにリダイレクトされることを確認
    def test_index_requires_login(self, client):
        response = client.get('/departments/')
        assert response.status_code == 302
        assert response.url.startswith('/login/')

    # 部門閲覧の権限が無いユーザーには一覧が0件になることを確認
    def test_index_by_user_without_permission_is_empty(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')
        Department.objects.create(company=company, name='開発部')

        response = auth_client.get('/departments/')
        assert response.status_code == 200
        assert len(response.context['departments']) == 0

    # 全部門閲覧を許可する権限セットを持つユーザーには会社を問わず一覧に表示されることを確認
    def test_index_by_user_with_view_all_permission(self, sample_user, auth_client):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='開発部')
        _grant(sample_user, DEPARTMENT_VIEWER_ALL, 'テスト工業株式会社')

        response = auth_client.get('/departments/')
        assert response.status_code == 200
        assert department in response.context['departments']

    # 特定の会社に絞った権限セットを持つユーザーには、その会社の部門のみ表示されることを確認
    def test_index_by_user_with_company_scoped_permission(self, sample_user, auth_client):
        sample_company = Company.objects.create(name='サンプル株式会社')
        matching_department = Department.objects.create(company=sample_company, name='開発部')
        other_company = Company.objects.create(name='別会社')
        other_department = Department.objects.create(company=other_company, name='総務部')
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER, 'サンプル株式会社')

        response = auth_client.get('/departments/')
        assert response.status_code == 200
        assert matching_department in response.context['departments']
        assert other_department not in response.context['departments']

    # 管理者は一覧を取得できることを確認
    def test_index_by_admin_succeeds(self, admin_client):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='開発部')

        response = admin_client.get('/departments/')
        assert response.status_code == 200
        assert department in response.context['departments']


@pytest.mark.django_db
class TestDepartmentShowView:

    # 部門閲覧の権限が無いユーザーがアクセスすると403が返ることを確認
    def test_show_by_user_without_permission_returns_403(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='開発部')

        response = auth_client.get(f'/departments/{department.id}/')
        assert response.status_code == 403

    # 存在しない部門の場合404が返ることを確認
    def test_show_nonexistent_department_returns_404(self, admin_client):
        response = admin_client.get('/departments/9999/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestDepartmentCreateView:

    # 作成権限が無いユーザーがアクセスすると403が返ることを確認
    def test_new_by_user_without_create_permission_returns_403(self, sample_user, auth_client):
        _grant(sample_user, DEPARTMENT_VIEWER_ALL, 'テスト工業株式会社')

        response = auth_client.get('/departments/new/')
        assert response.status_code == 403

    # 会社を絞った作成権限を持つユーザーはGETでフォームを取得できることを確認
    def test_get_returns_form(self, sample_user, auth_client):
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER, 'サンプル株式会社')

        response = auth_client.get('/departments/new/')
        assert response.status_code == 200
        assert 'form' in response.context

    # 権限の対象範囲内の会社であれば作成でき詳細ページにリダイレクトされることを確認
    def test_post_within_scope_creates_department_and_redirects(self, sample_user, auth_client):
        sample_company = Company.objects.create(name='サンプル株式会社')
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER, 'サンプル株式会社')

        response = auth_client.post('/departments/new/', {'company': sample_company.id, 'name': '新部門'})

        department = Department.objects.get(name='新部門')
        assert response.status_code == 302
        assert response.url == f'/departments/{department.id}/'

    # 権限の対象範囲外の会社を指定すると403が返ることを確認
    def test_post_outside_scope_returns_403(self, sample_user, auth_client):
        other_company = Company.objects.create(name='別会社')
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER, 'サンプル株式会社')

        response = auth_client.post('/departments/new/', {'company': other_company.id, 'name': '新部門'})

        assert response.status_code == 403
        assert Department.objects.filter(name='新部門').count() == 0

    # 管理者が無効なデータでPOSTするとフォームが再表示されることを確認
    def test_post_invalid_data_redisplays_form(self, admin_client):
        company = Company.objects.create(name='サンプル株式会社')

        response = admin_client.post('/departments/new/', {'company': company.id, 'name': ''})

        assert response.status_code == 200
        assert response.context['form'].is_valid() is False


@pytest.mark.django_db
class TestDepartmentEditView:

    # 編集権限が無いユーザーがアクセスすると403が返ることを確認
    def test_edit_by_user_without_permission_returns_403(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='開発部')

        response = auth_client.get(f'/departments/{department.id}/edit/')
        assert response.status_code == 403

    # 対象範囲内の部門であれば編集でき詳細ページにリダイレクトされることを確認
    def test_post_within_scope_updates_department_and_redirects(self, sample_user, auth_client):
        sample_company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=sample_company, name='開発部')
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER, 'サンプル株式会社')

        response = auth_client.post(f'/departments/{department.id}/edit/', {
            'company': sample_company.id, 'name': '更新後部門',
        })

        department.refresh_from_db()
        assert response.status_code == 302
        assert department.name == '更新後部門'

    # 存在しない部門の場合404が返ることを確認
    def test_edit_nonexistent_department_returns_404(self, admin_client):
        response = admin_client.get('/departments/9999/edit/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestDepartmentDeleteView:

    # company_scoped_department_managerは削除を明示的にdenyしているため、403が返ることを確認
    def test_delete_by_user_with_explicit_deny_rule_returns_403(self, sample_user, auth_client):
        sample_company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=sample_company, name='開発部')
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER, 'サンプル株式会社')

        response = auth_client.post(f'/departments/{department.id}/delete/')

        assert response.status_code == 403
        assert Department.objects.filter(id=department.id).count() == 1

    # 管理者はPOSTで削除でき、一覧ページにリダイレクトされることを確認
    def test_post_deletes_department_and_redirects_to_index(self, admin_client):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='開発部')

        response = admin_client.post(f'/departments/{department.id}/delete/')

        assert response.status_code == 302
        assert response.url == '/departments/'
        assert Department.objects.filter(id=department.id).count() == 0


def _grant(user, permission_set_id, anchor_company_name):
    company, _ = Company.objects.get_or_create(name=anchor_company_name)
    department = Department.objects.create(company=company, name=f'権限セット{permission_set_id}用部門')
    EmployeeDepartment.objects.create(employee=user.employee, department=department, is_primary=True)
    group = ManagementGroup.objects.create(
        name=f'test-group-{permission_set_id}-{user.username}', department=department, permission_set_id=permission_set_id
    )
    group.members.add(user)
