from django.contrib.auth.models import User
from app.models import Department, ManagementGroup


# 管理グループのシードデータを作成する
def create() -> None:
    hr_group = ManagementGroup.objects.create(name='人事部', is_admin=True)
    hr_group.members.set(User.objects.filter(username='E0001'))

    dev_group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)
    dev_group.members.set(User.objects.filter(username='E0002'))

    # 権限セットの動作確認用(サンプル株式会社の部門のみ閲覧・編集できる)
    sample_department = Department.objects.get(company__name='サンプル株式会社', name='開発部')
    department_manager_group = ManagementGroup.objects.create(
        name='サンプル株式会社 部門管理者', department=sample_department, permission_set_id=2,
    )
    department_manager_group.members.set(User.objects.filter(username='E0002'))
