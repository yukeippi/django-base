from app.forms.company import CompanyForm
from app.models import Company


# 会社を作成する
def create(*, form: CompanyForm) -> Company:
    return form.save()


# 会社を更新する
def update(*, company: Company, form: CompanyForm) -> Company:
    return form.save()


# 会社を削除する
def delete(*, company: Company) -> None:
    company.delete()
