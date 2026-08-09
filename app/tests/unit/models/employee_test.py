import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError
from app.models import Employee


# Employeeモデルのテストクラス
@pytest.mark.django_db
class TestEmployeeModel:

    # Userと社員番号を指定して作成できることを確認
    def test_create_employee(self):
        user = User.objects.create_user(username='taro', password='pass12345')
        employee = Employee.objects.create(user=user, employee_number='E2001')

        assert employee.id is not None
        assert employee.user == user
        assert employee.employee_number == 'E2001'

    # employee_numberが重複する場合はエラーになることを確認
    def test_employee_number_must_be_unique(self):
        user1 = User.objects.create_user(username='taro', password='pass12345')
        user2 = User.objects.create_user(username='jiro', password='pass12345')
        Employee.objects.create(user=user1, employee_number='E3001')

        with pytest.raises(IntegrityError):
            Employee.objects.create(user=user2, employee_number='E3001')

    # __str__がユーザーのフルネームを返すことを確認
    def test_str_returns_full_name(self):
        user = User.objects.create_user(
            username='taro', password='pass12345', first_name='太郎', last_name='山田'
        )
        employee = Employee.objects.create(user=user, employee_number='E4001')

        assert str(employee) == user.get_full_name()

    # フルネームが未設定の場合はusernameを返すことを確認
    def test_str_falls_back_to_username(self):
        user = User.objects.create_user(username='taro', password='pass12345')
        employee = Employee.objects.create(user=user, employee_number='E5001')

        assert str(employee) == 'taro'
