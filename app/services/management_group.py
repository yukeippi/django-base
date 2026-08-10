from app.forms.management_group import ManagementGroupForm
from app.models import ManagementGroup


# 管理グループを作成する
def create(*, form: ManagementGroupForm) -> ManagementGroup:
    return form.save()


# 管理グループを更新する
def update(*, form: ManagementGroupForm) -> ManagementGroup:
    return form.save()


# 管理グループを削除する
def delete(*, management_group: ManagementGroup) -> None:
    management_group.delete()
