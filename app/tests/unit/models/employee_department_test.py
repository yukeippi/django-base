import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from app.models import Company, Department, Employee, EmployeeDepartment


# EmployeeDepartmentモデルのテストクラス
@pytest.mark.django_db
class TestEmployeeDepartmentModel:

    # 主務として作成できることを確認
    def test_create_as_primary(self):
        employee = _create_employee('E7001')
        department = _create_department('開発部')

        relation = EmployeeDepartment.objects.create(employee=employee, department=department, is_primary=True)

        assert relation.id is not None
        assert relation.is_primary is True

    # 同じ社員・部門の組み合わせが重複する場合はエラーになることを確認(アプリ側のバリデーション)
    def test_same_employee_department_pair_must_be_unique(self):
        employee = _create_employee('E7002')
        department = _create_department('開発部')
        EmployeeDepartment.objects.create(employee=employee, department=department)

        with pytest.raises(ValidationError):
            EmployeeDepartment.objects.create(employee=employee, department=department)

    # __str__が「社員 - 部門」を返すことを確認
    def test_str_returns_employee_and_department(self):
        employee = _create_employee('E7006')
        department = _create_department('開発部')
        relation = EmployeeDepartment.objects.create(employee=employee, department=department)

        assert str(relation) == f'{employee} - {department}'


# EmployeeDepartmentQuerySetのテストクラス
@pytest.mark.django_db
class TestEmployeeDepartmentQuerySet:

    # primary()が主務の所属のみに絞り込むことを確認
    def test_primary_filters_to_primary_relations(self):
        employee = _create_employee('E7007')
        primary_department = _create_department('開発部')
        secondary_department = _create_department('営業部')
        primary_relation = EmployeeDepartment.objects.create(
            employee=employee, department=primary_department, is_primary=True
        )
        EmployeeDepartment.objects.create(employee=employee, department=secondary_department)

        result = list(employee.employee_departments.primary())

        assert result == [primary_relation]


def _create_employee(employee_number):
    user = User.objects.create_user(username=employee_number, password='pass12345')
    return Employee.objects.create(user=user, employee_number=employee_number)


def _create_department(name):
    company = Company.objects.create(name=f'{name}の会社')
    return Department.objects.create(company=company, name=name)
