import pytest
from app.forms.management_group import ManagementGroupForm


# ManagementGroupFormのテストクラス
@pytest.mark.django_db
class TestManagementGroupForm:

    # 有効なデータでフォームが妥当と判定されることを確認
    def test_valid_data_is_valid(self, sample_user):
        form = ManagementGroupForm(data={
            'name': '開発チーム',
            'members': [sample_user.id],
        })
        assert form.is_valid()

    # 名前が空の場合、フォームが無効と判定されることを確認
    def test_blank_name_is_invalid(self):
        form = ManagementGroupForm(data={
            'name': '',
            'members': [],
        })
        assert not form.is_valid()
        assert 'name' in form.errors

    # メンバー未選択でも妥当と判定されることを確認(members=blank許可)
    def test_no_members_is_valid(self):
        form = ManagementGroupForm(data={
            'name': '開発チーム',
            'members': [],
        })
        assert form.is_valid()

    # saveすると指定したメンバーが設定されることを確認
    def test_save_sets_members(self, sample_user, other_user):
        form = ManagementGroupForm(data={
            'name': '開発チーム',
            'members': [sample_user.id, other_user.id],
        })
        assert form.is_valid()

        group = form.save()

        assert group.members.count() == 2
