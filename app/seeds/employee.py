from django.contrib.auth.models import User
from faker import Faker
from app.models import Employee

fake = Faker('ja_JP')

DUMMY_EMPLOYEE_COUNT = 10


# 社員のシードデータを作成する
def create():
    # ログイン確認用に社員番号を固定した社員
    _create_employee('E0001', '太郎', '山田', is_staff=True)
    _create_employee('E0002', '花子', '鈴木')

    # 一覧・ページネーション確認用のダミー社員
    for i in range(1, DUMMY_EMPLOYEE_COUNT + 1):
        employee_number = f'E9{i:03d}'
        _create_employee(employee_number, fake.first_name(), fake.last_name())


# 社員番号をログインIDとするEmployee(+User)を作成する
def _create_employee(employee_number, first_name, last_name, is_staff=False):
    user = User.objects.create_user(
        username=employee_number,
        password='password123',
        first_name=first_name,
        last_name=last_name,
        is_staff=is_staff,
    )
    return Employee.objects.create(user=user, employee_number=employee_number)
