import pytest
from django.db import IntegrityError
from app.models import ManagementGroup


# ManagementGroupモデルのテストクラス
@pytest.mark.django_db
class TestManagementGroupModel:

    # 名前のみでデフォルト値(閲覧のみ)のグループを作成できることを確認
    def test_create_with_default_permission_level(self):
        group = ManagementGroup.objects.create(name='開発チーム')

        assert group.id is not None
        assert group.permission_level == ManagementGroup.VIEW

    # 権限レベルを指定して作成できることを確認
    def test_create_with_admin_permission_level(self):
        group = ManagementGroup.objects.create(name='人事部', permission_level=ManagementGroup.ADMIN)

        assert group.permission_level == ManagementGroup.ADMIN

    # 名前が重複する場合はエラーになることを確認
    def test_name_must_be_unique(self):
        ManagementGroup.objects.create(name='開発チーム')

        with pytest.raises(IntegrityError):
            ManagementGroup.objects.create(name='開発チーム')

    # メンバーを複数のユーザーで構成できることを確認
    def test_members_can_have_multiple_users(self, sample_user, other_user):
        group = ManagementGroup.objects.create(name='開発チーム')
        group.members.add(sample_user, other_user)

        assert group.members.count() == 2

    # __str__が名前を返すことを確認
    def test_str_returns_name(self):
        group = ManagementGroup.objects.create(name='開発チーム')

        assert str(group) == '開発チーム'
