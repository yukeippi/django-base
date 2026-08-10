import pytest
from django.contrib.auth.models import User
from app.models import Company, Department, Employee
from app.services import employee_department as employee_department_service


@pytest.mark.django_db
class TestCreate:

    # 主務として作成できることを確認
    def test_creates_as_primary(self):
        employee = _create_employee('E8001')
        department = _create_department('開発部')

        relation = employee_department_service.create(employee=employee, department=department, is_primary=True)

        assert relation.id is not None
        assert relation.is_primary is True

    # is_primaryを省略すると兼務(is_primary=False)として作成されることを確認
    def test_defaults_to_non_primary(self):
        employee = _create_employee('E8002')
        department = _create_department('開発部')

        relation = employee_department_service.create(employee=employee, department=department)

        assert relation.is_primary is False

    # 新しく主務を設定すると、既存の主務が自動的に解除されることを確認
    def test_new_primary_unsets_previous_primary(self):
        employee = _create_employee('E8003')
        dept_a = _create_department('開発部')
        dept_b = _create_department('営業部')
        relation_a = employee_department_service.create(employee=employee, department=dept_a, is_primary=True)

        employee_department_service.create(employee=employee, department=dept_b, is_primary=True)

        relation_a.refresh_from_db()
        assert relation_a.is_primary is False

    # 別の社員の主務には影響しないことを確認
    def test_primary_change_does_not_affect_other_employees(self):
        employee_a = _create_employee('E8004')
        employee_b = _create_employee('E8005')
        department = _create_department('開発部')
        relation_b = employee_department_service.create(employee=employee_b, department=department, is_primary=True)

        employee_department_service.create(employee=employee_a, department=department, is_primary=True)

        relation_b.refresh_from_db()
        assert relation_b.is_primary is True


def _create_employee(employee_number: str) -> Employee:
    user = User.objects.create_user(username=employee_number, password='pass12345')
    return Employee.objects.create(user=user, employee_number=employee_number)


def _create_department(name: str) -> Department:
    company = Company.objects.create(name=f'{name}の会社')
    return Department.objects.create(company=company, name=name)
