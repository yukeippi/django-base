import pytest
from app.forms.department import DepartmentForm
from app.models import Company, Department


# DepartmentFormのテストクラス
@pytest.mark.django_db
class TestDepartmentForm:

    # 有効なデータでフォームが妥当と判定されることを確認
    def test_valid_data_is_valid(self):
        company = Company.objects.create(name='サンプル株式会社')
        form = DepartmentForm(data={'company': company.id, 'name': '開発部'})
        assert form.is_valid()

    # 部門名が空の場合、フォームが無効と判定されることを確認
    def test_blank_name_is_invalid(self):
        company = Company.objects.create(name='サンプル株式会社')
        form = DepartmentForm(data={'company': company.id, 'name': ''})
        assert not form.is_valid()
        assert 'name' in form.errors

    # 同じ会社内で部門名が重複する場合、フォームが無効と判定されることを確認
    def test_duplicate_name_within_company_is_invalid(self):
        company = Company.objects.create(name='サンプル株式会社')
        Department.objects.create(company=company, name='開発部')

        form = DepartmentForm(data={'company': company.id, 'name': '開発部'})
        assert not form.is_valid()

    # saveすると部門が作成されることを確認
    def test_save_creates_department(self):
        company = Company.objects.create(name='サンプル株式会社')
        form = DepartmentForm(data={'company': company.id, 'name': '開発部'})
        assert form.is_valid()

        department = form.save()

        assert department.id is not None
        assert department.company == company
        assert department.name == '開発部'
