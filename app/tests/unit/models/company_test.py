import pytest
from django.db import IntegrityError
from app.models import Company


# Companyモデルのテストクラス
@pytest.mark.django_db
class TestCompanyModel:

    # 名前を指定して作成できることを確認
    def test_create_company(self):
        company = Company.objects.create(name='サンプル株式会社')

        assert company.id is not None
        assert company.name == 'サンプル株式会社'

    # 名前が重複する場合はエラーになることを確認
    def test_name_must_be_unique(self):
        Company.objects.create(name='サンプル株式会社')

        with pytest.raises(IntegrityError):
            Company.objects.create(name='サンプル株式会社')

    # __str__が名前を返すことを確認
    def test_str_returns_name(self):
        company = Company.objects.create(name='サンプル株式会社')

        assert str(company) == 'サンプル株式会社'
