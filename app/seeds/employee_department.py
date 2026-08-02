from django.contrib.auth.models import User
from app.models import Department, EmployeeDepartment


# 社員の部門所属(主務/兼務)のシードデータを作成する
def create():
    dev = Department.objects.get(company__name='サンプル株式会社', name='開発部')
    sales = Department.objects.get(company__name='サンプル株式会社', name='営業部')

    e0001 = User.objects.get(username='E0001').employee
    e0002 = User.objects.get(username='E0002').employee

    # E0001は開発部が主務
    EmployeeDepartment.objects.create(employee=e0001, department=dev, is_primary=True)

    # E0002は営業部が主務、開発部を兼務
    EmployeeDepartment.objects.create(employee=e0002, department=sales, is_primary=True)
    EmployeeDepartment.objects.create(employee=e0002, department=dev)
