from app.forms.department import DepartmentForm
from app.models import Department


# 部門を作成する
def create(*, form: DepartmentForm) -> Department:
    return form.save()


# 部門を更新する
def update(*, department: Department, form: DepartmentForm) -> Department:
    return form.save()


# 部門を削除する
def delete(*, department: Department) -> None:
    department.delete()
