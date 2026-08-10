import pytest
from django.core.exceptions import ValidationError
from app.models import Company, Department


# Departmentモデルのテストクラス
@pytest.mark.django_db
class TestDepartmentModel:

    # 会社と名前を指定して作成できることを確認
    def test_create_department(self):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='開発部')

        assert department.id is not None
        assert department.company == company
        assert department.name == '開発部'

    # 同じ会社内で部門名が重複する場合はエラーになることを確認(アプリ側のバリデーション)
    def test_name_must_be_unique_within_company(self):
        company = Company.objects.create(name='サンプル株式会社')
        Department.objects.create(company=company, name='開発部')

        with pytest.raises(ValidationError):
            Department.objects.create(company=company, name='開発部')

    # 別の会社であれば同じ部門名を使えることを確認
    def test_same_name_allowed_in_different_company(self):
        company_a = Company.objects.create(name='A株式会社')
        company_b = Company.objects.create(name='B株式会社')
        Department.objects.create(company=company_a, name='開発部')

        department = Department.objects.create(company=company_b, name='開発部')

        assert department.id is not None

    # __str__が「会社名 / 部門名」を返すことを確認
    def test_str_returns_company_and_name(self):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='開発部')

        assert str(department) == 'サンプル株式会社 / 開発部'


# DepartmentQuerySetのテストクラス
@pytest.mark.django_db
class TestDepartmentQuerySet:

    # with_company()が全件を返すことを確認
    def test_with_company_returns_all_departments(self):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='開発部')

        result = list(Department.objects.with_company())

        assert result == [department]

    # with_company()がcompanyをselect_relatedし、追加クエリが発生しないことを確認
    def test_with_company_avoids_extra_query(self, django_assert_num_queries):
        company = Company.objects.create(name='サンプル株式会社')
        Department.objects.create(company=company, name='開発部')

        with django_assert_num_queries(1):
            department = Department.objects.with_company().first()
            str(department.company)
