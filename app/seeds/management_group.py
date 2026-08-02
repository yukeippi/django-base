from django.contrib.auth.models import User
from app.models import ManagementGroup


# 管理グループのシードデータを作成する
def create():
    admin_group = ManagementGroup.objects.create(name='人事部', permission_level=ManagementGroup.ADMIN)
    admin_group.members.set(User.objects.filter(username='E0001'))

    dev_group = ManagementGroup.objects.create(name='開発チーム', permission_level=ManagementGroup.EDIT)
    dev_group.members.set(User.objects.filter(username='E0002'))
