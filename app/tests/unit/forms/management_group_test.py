import pytest
from app.forms.management_group import ManagementGroupForm


# ManagementGroupFormのテストクラス
@pytest.mark.django_db
class TestManagementGroupForm:

    # 全社管理者として有効なデータでフォームが妥当と判定されることを確認
    def test_valid_data_is_valid(self, sample_user):
        form = ManagementGroupForm(data={
            'name': '開発チーム',
            'members': [sample_user.id],
            'is_admin': True,
        })
        assert form.is_valid()

    # 名前が空の場合、フォームが無効と判定されることを確認
    def test_blank_name_is_invalid(self):
        form = ManagementGroupForm(data={
            'name': '',
            'members': [],
            'is_admin': True,
        })
        assert not form.is_valid()
        assert 'name' in form.errors

    # メンバー未選択でも妥当と判定されることを確認(members=blank許可)
    def test_no_members_is_valid(self):
        form = ManagementGroupForm(data={
            'name': '開発チーム',
            'members': [],
            'is_admin': True,
        })
        assert form.is_valid()

    # 全社管理者でないのに部門が未指定の場合、フォームが無効と判定されることを確認
    def test_department_required_when_not_admin(self):
        form = ManagementGroupForm(data={
            'name': '開発チーム',
            'members': [],
            'is_admin': False,
        })
        assert not form.is_valid()

    # 全社管理者でないのに権限セット番号が未指定の場合、フォームが無効と判定されることを確認
    def test_permission_set_id_required_when_not_admin(self, sample_department):
        form = ManagementGroupForm(data={
            'name': '開発チーム',
            'members': [],
            'is_admin': False,
            'department': sample_department.id,
        })
        assert not form.is_valid()

    # 全社管理者でなく、部門・権限セット番号を指定していれば妥当と判定されることを確認
    def test_valid_non_admin_data_is_valid(self, sample_department):
        form = ManagementGroupForm(data={
            'name': '開発チーム',
            'members': [],
            'is_admin': False,
            'department': sample_department.id,
            'permission_set_id': 1,
        })
        assert form.is_valid()

    # saveすると指定したメンバーが設定されることを確認
    def test_save_sets_members(self, sample_user, other_user):
        form = ManagementGroupForm(data={
            'name': '開発チーム',
            'members': [sample_user.id, other_user.id],
            'is_admin': True,
        })
        assert form.is_valid()

        group = form.save()

        assert group.members.count() == 2


@pytest.fixture
def sample_department():
    from app.models import Company, Department
    company = Company.objects.create(name='サンプル株式会社')
    return Department.objects.create(company=company, name='開発部')
