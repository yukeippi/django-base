import pytest
from app.forms.employee import EmployeeForm
from app.models import Employee
from app.services import employee as employee_service


@pytest.mark.django_db
class TestCreate:

    # 有効なフォームからUserとEmployeeが同時に作成されることを確認
    def test_creates_user_and_employee(self):
        form = EmployeeForm(data={
            'employee_number': 'E0200', 'last_name': '鈴木', 'first_name': '花子', 'password': 'pass12345',
        })
        assert form.is_valid()

        employee = employee_service.create(form=form)

        assert employee.employee_number == 'E0200'
        assert employee.user.username == 'E0200'
        assert employee.user.first_name == '花子'
        assert employee.user.last_name == '鈴木'
        assert employee.user.check_password('pass12345')


@pytest.mark.django_db
class TestUpdate:

    # 氏名が更新され、パスワード未入力なら変更されないことを確認
    def test_updates_name_without_changing_password(self, sample_user):
        employee = sample_user.employee
        original_password_hash = sample_user.password
        form = EmployeeForm(data={
            'employee_number': employee.employee_number, 'last_name': '変更後姓', 'first_name': '変更後名',
            'password': '',
        }, instance=employee)
        assert form.is_valid()

        employee_service.update(employee=employee, form=form)
        sample_user.refresh_from_db()

        assert sample_user.last_name == '変更後姓'
        assert sample_user.first_name == '変更後名'
        assert sample_user.password == original_password_hash

    # パスワードを入力した場合はパスワードも更新されることを確認
    def test_updates_password_when_provided(self, sample_user):
        employee = sample_user.employee
        form = EmployeeForm(data={
            'employee_number': employee.employee_number, 'last_name': '山田', 'first_name': '太郎',
            'password': 'newpass456',
        }, instance=employee)
        assert form.is_valid()

        employee_service.update(employee=employee, form=form)
        sample_user.refresh_from_db()

        assert sample_user.check_password('newpass456')


@pytest.mark.django_db
class TestDelete:

    # 社員(User含む)が削除されることを確認
    def test_deletes_employee_and_user(self, sample_user):
        employee = sample_user.employee
        user_id = sample_user.id

        employee_service.delete(employee=employee)

        assert Employee.objects.filter(id=employee.id).count() == 0
        from django.contrib.auth.models import User
        assert User.objects.filter(id=user_id).count() == 0
