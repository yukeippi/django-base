import pytest
from app.forms.company import CompanyForm
from app.models import Company


# CompanyFormのテストクラス
@pytest.mark.django_db
class TestCompanyForm:

    # 有効なデータでフォームが妥当と判定されることを確認
    def test_valid_data_is_valid(self):
        form = CompanyForm(data={'name': 'サンプル株式会社'})
        assert form.is_valid()

    # 名前が空の場合、フォームが無効と判定されることを確認
    def test_blank_name_is_invalid(self):
        form = CompanyForm(data={'name': ''})
        assert not form.is_valid()
        assert 'name' in form.errors

    # 名前が重複する場合、フォームが無効と判定されることを確認
    def test_duplicate_name_is_invalid(self):
        Company.objects.create(name='サンプル株式会社')

        form = CompanyForm(data={'name': 'サンプル株式会社'})
        assert not form.is_valid()
        assert 'name' in form.errors

    # saveすると会社が作成されることを確認
    def test_save_creates_company(self):
        form = CompanyForm(data={'name': 'サンプル株式会社'})
        assert form.is_valid()

        company = form.save()

        assert company.id is not None
        assert company.name == 'サンプル株式会社'
