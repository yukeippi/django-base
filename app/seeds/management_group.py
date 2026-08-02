from django.contrib.auth.models import User
from app.models import ManagementGroup


# 管理グループのシードデータを作成する
def create():
    hr_group = ManagementGroup.objects.create(name='人事部')
    hr_group.members.set(User.objects.filter(username='E0001'))

    dev_group = ManagementGroup.objects.create(name='開発チーム')
    dev_group.members.set(User.objects.filter(username='E0002'))
