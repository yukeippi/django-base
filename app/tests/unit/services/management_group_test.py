import pytest
from app.forms.management_group import ManagementGroupForm
from app.models import ManagementGroup
from app.services import management_group as management_group_service


@pytest.mark.django_db
class TestCreate:

    # 有効なフォームから管理グループが作成されることを確認
    def test_creates_management_group(self):
        form = ManagementGroupForm(data={'name': '開発チーム', 'members': [], 'is_admin': True})
        assert form.is_valid()

        management_group = management_group_service.create(form=form)

        assert management_group.id is not None
        assert management_group.name == '開発チーム'


@pytest.mark.django_db
class TestUpdate:

    # 有効なフォームで管理グループが更新されることを確認
    def test_updates_management_group(self):
        management_group = ManagementGroup.objects.create(name='元のチーム', is_admin=True)
        form = ManagementGroupForm(
            data={'name': '更新後のチーム', 'members': [], 'is_admin': True}, instance=management_group
        )
        assert form.is_valid()

        updated_group = management_group_service.update(management_group=management_group, form=form)

        assert updated_group.name == '更新後のチーム'


@pytest.mark.django_db
class TestDelete:

    # 管理グループが削除されることを確認
    def test_deletes_management_group(self):
        management_group = ManagementGroup.objects.create(name='削除するチーム', is_admin=True)

        management_group_service.delete(management_group=management_group)

        assert ManagementGroup.objects.filter(id=management_group.id).count() == 0
