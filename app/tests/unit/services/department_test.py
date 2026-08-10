import pytest
from app.forms.department import DepartmentForm
from app.models import Company, Department
from app.services import department as department_service


@pytest.mark.django_db
class TestCreate:

    # 有効なフォームから部門が作成されることを確認
    def test_creates_department(self):
        company = Company.objects.create(name='サンプル株式会社')
        form = DepartmentForm(data={'company': company.id, 'name': '開発部'})
        assert form.is_valid()

        department = department_service.create(form=form)

        assert department.id is not None
        assert department.name == '開発部'


@pytest.mark.django_db
class TestUpdate:

    # 有効なフォームで部門が更新されることを確認
    def test_updates_department(self):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='元の部門')
        form = DepartmentForm(data={'company': company.id, 'name': '更新後の部門'}, instance=department)
        assert form.is_valid()

        updated_department = department_service.update(department=department, form=form)

        assert updated_department.name == '更新後の部門'


@pytest.mark.django_db
class TestDelete:

    # 部門が削除されることを確認
    def test_deletes_department(self):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='削除する部門')

        department_service.delete(department=department)

        assert Department.objects.filter(id=department.id).count() == 0
