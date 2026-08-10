import pytest
from app.forms.employee import EmployeeForm


# EmployeeFormのテストクラス
@pytest.mark.django_db
class TestEmployeeFormCreate:

    # 有効なデータでフォームが妥当と判定されることを確認
    def test_valid_data_is_valid(self):
        form = EmployeeForm(data={
            'employee_number': 'E0100',
            'last_name': '山田',
            'first_name': '太郎',
            'password': 'pass12345',
        })
        assert form.is_valid()

    # 新規作成時はパスワードが必須であることを確認
    def test_password_is_required_on_create(self):
        form = EmployeeForm(data={
            'employee_number': 'E0100',
            'last_name': '山田',
            'first_name': '太郎',
            'password': '',
        })
        assert not form.is_valid()
        assert 'password' in form.errors

    # 社員番号が重複している場合、フォームが無効と判定されることを確認
    def test_duplicate_employee_number_is_invalid(self, sample_user):
        form = EmployeeForm(data={
            'employee_number': sample_user.employee.employee_number,
            'last_name': '山田',
            'first_name': '太郎',
            'password': 'pass12345',
        })
        assert not form.is_valid()
        assert 'employee_number' in form.errors


@pytest.mark.django_db
class TestEmployeeFormEdit:

    # 編集時はパスワード未入力でも妥当と判定されることを確認
    def test_password_is_optional_on_edit(self, sample_user):
        employee = sample_user.employee
        form = EmployeeForm(data={
            'employee_number': employee.employee_number,
            'last_name': '変更後姓',
            'first_name': '変更後名',
            'password': '',
        }, instance=employee)
        assert form.is_valid()

    # 他人の社員番号に変更しようとするとフォームが無効と判定されることを確認
    def test_duplicate_employee_number_is_invalid(self, sample_user, other_user):
        employee = sample_user.employee
        form = EmployeeForm(data={
            'employee_number': other_user.employee.employee_number,
            'last_name': sample_user.last_name,
            'first_name': sample_user.first_name,
            'password': '',
        }, instance=employee)
        assert not form.is_valid()
        assert 'employee_number' in form.errors
