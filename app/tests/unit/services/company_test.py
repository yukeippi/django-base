import pytest
from app.forms.company import CompanyForm
from app.models import Company
from app.services import company as company_service


@pytest.mark.django_db
class TestCreate:

    # 有効なフォームから会社が作成されることを確認
    def test_creates_company(self):
        form = CompanyForm(data={'name': 'サンプル株式会社'})
        assert form.is_valid()

        company = company_service.create(form=form)

        assert company.id is not None
        assert company.name == 'サンプル株式会社'


@pytest.mark.django_db
class TestUpdate:

    # 有効なフォームで会社が更新されることを確認
    def test_updates_company(self):
        company = Company.objects.create(name='元の会社')
        form = CompanyForm(data={'name': '更新後の会社'}, instance=company)
        assert form.is_valid()

        updated_company = company_service.update(form=form)

        assert updated_company.name == '更新後の会社'


@pytest.mark.django_db
class TestDelete:

    # 会社が削除されることを確認
    def test_deletes_company(self):
        company = Company.objects.create(name='削除する会社')

        company_service.delete(company=company)

        assert Company.objects.filter(id=company.id).count() == 0
