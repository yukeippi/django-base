import pytest
from app.models import Company, Department


@pytest.mark.django_db
class TestDepartmentIndexView:

    # 未ログインの場合、ログインページにリダイレクトされることを確認
    def test_index_requires_login(self, client):
        response = client.get('/departments/')
        assert response.status_code == 302
        assert response.url.startswith('/login/')

    # 部門が一覧に表示されることを確認
    def test_index_with_departments(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')
        Department.objects.create(company=company, name='開発部')

        response = auth_client.get('/departments/')
        assert response.status_code == 200
        assert len(response.context['departments']) == 1


@pytest.mark.django_db
class TestDepartmentShowView:

    # 存在する部門の詳細が取得できることを確認
    def test_show_existing_department(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='開発部')

        response = auth_client.get(f'/departments/{department.id}/')
        assert response.status_code == 200
        assert response.context['department'] == department

    # 存在しない部門の場合404が返ることを確認
    def test_show_nonexistent_department_returns_404(self, auth_client):
        response = auth_client.get('/departments/9999/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestDepartmentCreateView:

    # GETリクエストでフォームが表示されることを確認
    def test_get_returns_form(self, auth_client):
        response = auth_client.get('/departments/new/')
        assert response.status_code == 200
        assert 'form' in response.context

    # 有効なデータでPOSTすると部門が作成され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_creates_department_and_redirects(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')

        response = auth_client.post('/departments/new/', {'company': company.id, 'name': '開発部'})

        department = Department.objects.get(company=company, name='開発部')
        assert response.status_code == 302
        assert response.url == f'/departments/{department.id}/'

    # 無効なデータでPOSTするとフォームが再表示されることを確認
    def test_post_invalid_data_redisplays_form(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')

        response = auth_client.post('/departments/new/', {'company': company.id, 'name': ''})

        assert response.status_code == 200
        assert response.context['form'].is_valid() is False


@pytest.mark.django_db
class TestDepartmentEditView:

    # 有効なデータでPOSTすると部門が更新され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_updates_department_and_redirects(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='開発部')

        response = auth_client.post(f'/departments/{department.id}/edit/', {
            'company': company.id, 'name': '更新後部門',
        })

        department.refresh_from_db()
        assert response.status_code == 302
        assert department.name == '更新後部門'

    # 存在しない部門の場合404が返ることを確認
    def test_edit_nonexistent_department_returns_404(self, auth_client):
        response = auth_client.get('/departments/9999/edit/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestDepartmentDeleteView:

    # POSTすると部門が削除され一覧ページにリダイレクトされることを確認
    def test_post_deletes_department_and_redirects_to_index(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='開発部')

        response = auth_client.post(f'/departments/{department.id}/delete/')

        assert response.status_code == 302
        assert response.url == '/departments/'
        assert Department.objects.filter(id=department.id).count() == 0

    # 存在しない部門の場合404が返ることを確認
    def test_delete_nonexistent_department_returns_404(self, auth_client):
        response = auth_client.get('/departments/9999/delete/')
        assert response.status_code == 404
