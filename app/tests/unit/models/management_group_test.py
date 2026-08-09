import pytest
from django.core.exceptions import ValidationError
from app.models import Company, Department, ManagementGroup


# ManagementGroupモデルのテストクラス
@pytest.mark.django_db
class TestManagementGroupModel:

    # is_admin=Trueなら部門なしでグループを作成できることを確認
    def test_create_admin_group_without_department(self):
        group = ManagementGroup.objects.create(name='全社管理者グループ', is_admin=True)

        assert group.id is not None
        assert group.name == '全社管理者グループ'
        assert group.department is None

    # is_admin=Falseの場合は部門・権限セット番号を指定してグループを作成できることを確認
    def test_create_non_admin_group_with_department(self):
        department = _create_department('開発部')

        group = ManagementGroup.objects.create(name='開発部管理グループ', department=department, permission_set_id=1)

        assert group.id is not None
        assert group.is_admin is False
        assert group.department == department

    # is_admin=Falseなのに部門が未設定の場合はエラーになることを確認
    def test_department_required_when_not_admin(self):
        with pytest.raises(ValidationError):
            ManagementGroup.objects.create(name='不正なグループ', permission_set_id=1)

    # is_admin=Trueなのに部門が設定されている場合はエラーになることを確認
    def test_department_forbidden_when_admin(self):
        department = _create_department('開発部')

        with pytest.raises(ValidationError):
            ManagementGroup.objects.create(name='不正なグループ', is_admin=True, department=department)

    # is_admin=Falseなのに権限セット番号が未設定の場合はエラーになることを確認
    def test_permission_set_id_required_when_not_admin(self):
        department = _create_department('開発部')

        with pytest.raises(ValidationError):
            ManagementGroup.objects.create(name='不正なグループ', department=department)

    # is_admin=Trueなのに権限セット番号が設定されている場合はエラーになることを確認
    def test_permission_set_id_forbidden_when_admin(self):
        with pytest.raises(ValidationError):
            ManagementGroup.objects.create(name='不正なグループ', is_admin=True, permission_set_id=1)

    # REGISTRYに存在しない権限セット番号を指定した場合はエラーになることを確認
    def test_unknown_permission_set_id_is_rejected(self):
        department = _create_department('開発部')

        with pytest.raises(ValidationError):
            ManagementGroup.objects.create(name='不正なグループ', department=department, permission_set_id=999)

    # REGISTRYに存在する権限セット番号を指定した場合は作成できることを確認
    def test_valid_permission_set_id_is_accepted(self):
        department = _create_department('開発部')

        group = ManagementGroup.objects.create(name='開発部管理グループ2', department=department, permission_set_id=1)

        assert group.permission_set_id == 1

    # 名前が重複する場合はエラーになることを確認
    def test_name_must_be_unique(self):
        ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        with pytest.raises(ValidationError):
            ManagementGroup.objects.create(name='開発チーム', is_admin=True)

    # メンバーを複数のユーザーで構成できることを確認
    def test_members_can_have_multiple_users(self, sample_user, other_user):
        group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)
        group.members.add(sample_user, other_user)

        assert group.members.count() == 2

    # __str__が名前を返すことを確認
    def test_str_returns_name(self):
        group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        assert str(group) == '開発チーム'


def _create_department(name):
    company = Company.objects.create(name=f'{name}の会社')
    return Department.objects.create(company=company, name=name)
