import pytest
from django.db import IntegrityError
from app.models import ManagementGroup


# ManagementGroupモデルのテストクラス
@pytest.mark.django_db
class TestManagementGroupModel:

    # 名前のみでグループを作成できることを確認
    def test_create_with_name_only(self):
        group = ManagementGroup.objects.create(name='開発チーム')

        assert group.id is not None
        assert group.name == '開発チーム'

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
