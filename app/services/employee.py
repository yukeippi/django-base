from django.contrib.auth.models import User
from django.db import transaction
from app.forms.employee import EmployeeForm
from app.models import Employee


# 社員を新規登録する(UserとEmployeeを同時作成)
@transaction.atomic
def create(*, form: EmployeeForm) -> Employee:
    user = User.objects.create_user(
        username=form.cleaned_data['employee_number'],
        first_name=form.cleaned_data['first_name'],
        last_name=form.cleaned_data['last_name'],
        password=form.cleaned_data['password'],
    )
    return Employee.objects.create(user=user, employee_number=form.cleaned_data['employee_number'])


# 社員情報を更新する(パスワードは入力があった場合のみ変更)
@transaction.atomic
def update(*, employee: Employee, form: EmployeeForm) -> Employee:
    employee.employee_number = form.cleaned_data['employee_number']
    employee.save()

    user = employee.user
    user.first_name = form.cleaned_data['first_name']
    user.last_name = form.cleaned_data['last_name']
    if form.cleaned_data['password']:
        user.set_password(form.cleaned_data['password'])
    user.save()
    return employee


# 社員(User含む)を削除する
def delete(*, employee: Employee) -> None:
    employee.user.delete()
