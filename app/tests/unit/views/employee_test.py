import pytest
from app.models import Employee


@pytest.mark.django_db
class TestEmployeeIndexView:

    # 未ログインの場合、ログインページにリダイレクトされることを確認
    def test_index_requires_login(self, client):
        response = client.get('/employees/')
        assert response.status_code == 302
        assert response.url.startswith('/login/')

    # 社員が一覧に表示されることを確認
    def test_index_with_employees(self, auth_client, sample_user, other_user):
        response = auth_client.get('/employees/')
        assert response.status_code == 200
        assert len(response.context['employees']) == 2


@pytest.mark.django_db
class TestEmployeeShowView:

    # 存在する社員の詳細が取得できることを確認
    def test_show_existing_employee(self, auth_client, sample_user):
        response = auth_client.get(f'/employees/{sample_user.employee.id}/')
        assert response.status_code == 200
        assert response.context['employee'] == sample_user.employee

    # 存在しない社員の場合404が返ることを確認
    def test_show_nonexistent_employee_returns_404(self, auth_client):
        response = auth_client.get('/employees/9999/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestEmployeeCreateView:

    # GETリクエストでフォームが表示されることを確認
    def test_get_returns_form(self, auth_client):
        response = auth_client.get('/employees/new/')
        assert response.status_code == 200
        assert 'form' in response.context

    # 有効なデータでPOSTするとUserとEmployeeが作成され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_creates_employee_and_redirects(self, auth_client):
        response = auth_client.post('/employees/new/', {
            'employee_number': 'E0300',
            'last_name': '佐藤',
            'first_name': '次郎',
            'password': 'pass12345',
        })

        employee = Employee.objects.get(employee_number='E0300')
        assert response.status_code == 302
        assert response.url == f'/employees/{employee.id}/'
        assert employee.user.check_password('pass12345')

    # 無効なデータでPOSTするとフォームが再表示されることを確認
    def test_post_invalid_data_redisplays_form(self, auth_client):
        response = auth_client.post('/employees/new/', {
            'employee_number': '',
            'last_name': '佐藤',
            'first_name': '次郎',
            'password': 'pass12345',
        })

        assert response.status_code == 200
        assert response.context['form'].is_valid() is False


@pytest.mark.django_db
class TestEmployeeEditView:

    # GETリクエストで既存社員の値がフォームに入っていることを確認
    def test_get_returns_form_with_instance(self, auth_client, sample_user):
        employee = sample_user.employee

        response = auth_client.get(f'/employees/{employee.id}/edit/')
        assert response.status_code == 200
        assert response.context['form'].initial['employee_number'] == employee.employee_number

    # 有効なデータでPOSTすると社員情報が更新され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_updates_employee_and_redirects(self, auth_client, sample_user):
        employee = sample_user.employee

        response = auth_client.post(f'/employees/{employee.id}/edit/', {
            'employee_number': employee.employee_number,
            'last_name': '更新後姓',
            'first_name': '更新後名',
            'password': '',
        })

        sample_user.refresh_from_db()
        assert response.status_code == 302
        assert response.url == f'/employees/{employee.id}/'
        assert sample_user.last_name == '更新後姓'

    # 存在しない社員の場合404が返ることを確認
    def test_edit_nonexistent_employee_returns_404(self, auth_client):
        response = auth_client.get('/employees/9999/edit/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestEmployeeDeleteView:

    # GETリクエストで削除確認ページが表示されることを確認
    def test_get_returns_confirmation_page(self, auth_client, sample_user):
        employee = sample_user.employee

        response = auth_client.get(f'/employees/{employee.id}/delete/')
        assert response.status_code == 200
        assert response.context['employee'] == employee

    # POSTすると社員(User含む)が削除され一覧ページにリダイレクトされることを確認
    def test_post_deletes_employee_and_redirects_to_index(self, auth_client, other_user):
        employee = other_user.employee

        response = auth_client.post(f'/employees/{employee.id}/delete/')

        assert response.status_code == 302
        assert response.url == '/employees/'
        assert Employee.objects.filter(id=employee.id).count() == 0

    # 存在しない社員の場合404が返ることを確認
    def test_delete_nonexistent_employee_returns_404(self, auth_client):
        response = auth_client.get('/employees/9999/delete/')
        assert response.status_code == 404
