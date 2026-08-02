import pytest
from app.models import Company


@pytest.mark.django_db
class TestCompanyIndexView:

    # 未ログインの場合、ログインページにリダイレクトされることを確認
    def test_index_requires_login(self, client):
        response = client.get('/companies/')
        assert response.status_code == 302
        assert response.url.startswith('/login/')

    # 会社が一覧に表示されることを確認
    def test_index_with_companies(self, auth_client):
        Company.objects.create(name='サンプル株式会社')

        response = auth_client.get('/companies/')
        assert response.status_code == 200
        assert len(response.context['companies']) == 1


@pytest.mark.django_db
class TestCompanyShowView:

    # 存在する会社の詳細が取得できることを確認
    def test_show_existing_company(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')

        response = auth_client.get(f'/companies/{company.id}/')
        assert response.status_code == 200
        assert response.context['company'] == company

    # 存在しない会社の場合404が返ることを確認
    def test_show_nonexistent_company_returns_404(self, auth_client):
        response = auth_client.get('/companies/9999/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestCompanyCreateView:

    # GETリクエストでフォームが表示されることを確認
    def test_get_returns_form(self, auth_client):
        response = auth_client.get('/companies/new/')
        assert response.status_code == 200
        assert 'form' in response.context

    # 有効なデータでPOSTすると会社が作成され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_creates_company_and_redirects(self, auth_client):
        response = auth_client.post('/companies/new/', {'name': 'サンプル株式会社'})

        company = Company.objects.get(name='サンプル株式会社')
        assert response.status_code == 302
        assert response.url == f'/companies/{company.id}/'

    # 無効なデータでPOSTするとフォームが再表示されることを確認
    def test_post_invalid_data_redisplays_form(self, auth_client):
        response = auth_client.post('/companies/new/', {'name': ''})

        assert response.status_code == 200
        assert response.context['form'].is_valid() is False


@pytest.mark.django_db
class TestCompanyEditView:

    # 有効なデータでPOSTすると会社が更新され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_updates_company_and_redirects(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')

        response = auth_client.post(f'/companies/{company.id}/edit/', {'name': '更新後株式会社'})

        company.refresh_from_db()
        assert response.status_code == 302
        assert company.name == '更新後株式会社'

    # 存在しない会社の場合404が返ることを確認
    def test_edit_nonexistent_company_returns_404(self, auth_client):
        response = auth_client.get('/companies/9999/edit/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestCompanyDeleteView:

    # POSTすると会社が削除され一覧ページにリダイレクトされることを確認
    def test_post_deletes_company_and_redirects_to_index(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')

        response = auth_client.post(f'/companies/{company.id}/delete/')

        assert response.status_code == 302
        assert response.url == '/companies/'
        assert Company.objects.filter(id=company.id).count() == 0

    # 存在しない会社の場合404が返ることを確認
    def test_delete_nonexistent_company_returns_404(self, auth_client):
        response = auth_client.get('/companies/9999/delete/')
        assert response.status_code == 404
