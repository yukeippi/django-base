import pytest
from django.core.exceptions import ValidationError
from app.models import Company, Department, DepartmentHierarchy


# DepartmentHierarchyモデルのテストクラス
@pytest.mark.django_db
class TestDepartmentHierarchyModel:

    # 親部門を指定して作成できることを確認
    def test_create_with_parent(self):
        company = Company.objects.create(name='サンプル株式会社')
        parent = Department.objects.create(company=company, name='本社')
        child = Department.objects.create(company=company, name='営業部')

        hierarchy = DepartmentHierarchy.objects.create(department=child, parent_department=parent)

        assert hierarchy.id is not None
        assert hierarchy.department == child
        assert hierarchy.parent_department == parent

    # 親部門なし(最上位の部門)で作成できることを確認
    def test_create_without_parent(self):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='本社')

        hierarchy = DepartmentHierarchy.objects.create(department=department)

        assert hierarchy.id is not None
        assert hierarchy.parent_department is None

    # 親部門が別の会社に属している場合はエラーになることを確認
    def test_parent_must_be_same_company(self):
        company_a = Company.objects.create(name='A株式会社')
        company_b = Company.objects.create(name='B株式会社')
        department = Department.objects.create(company=company_a, name='営業部')
        other_company_department = Department.objects.create(company=company_b, name='本社')

        with pytest.raises(ValidationError):
            DepartmentHierarchy.objects.create(department=department, parent_department=other_company_department)

    # 同じ部門で2件目のレコードを作成しようとするとエラーになることを確認(1部門につき1レコード)
    def test_department_must_be_unique(self):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='営業部')
        DepartmentHierarchy.objects.create(department=department)

        with pytest.raises(ValidationError):
            DepartmentHierarchy.objects.create(department=department)

    # 親部門に自分自身を指定した場合はエラーになることを確認
    def test_parent_cannot_be_self(self):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='営業部')

        with pytest.raises(ValidationError):
            DepartmentHierarchy.objects.create(department=department, parent_department=department)

    # __str__が「部門 (親: 親部門)」の形式を返すことを確認
    def test_str_includes_department_and_parent(self):
        company = Company.objects.create(name='サンプル株式会社')
        parent = Department.objects.create(company=company, name='本社')
        child = Department.objects.create(company=company, name='営業部')
        hierarchy = DepartmentHierarchy.objects.create(department=child, parent_department=parent)

        assert str(hierarchy) == f'{child} (親: {parent})'
