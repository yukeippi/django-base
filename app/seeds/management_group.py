from django.contrib.auth.models import User
from app.models import ManagementGroup


# 管理グループのシードデータを作成する
def create():
    hr_group = ManagementGroup.objects.create(name='人事部', is_admin=True)
    hr_group.members.set(User.objects.filter(username='E0001'))

    dev_group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)
    dev_group.members.set(User.objects.filter(username='E0002'))
