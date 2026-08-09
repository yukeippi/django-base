import pytest
from app.models import Company, Department, EmployeeDepartment, ManagementGroup
from app.permissions.access import can_create, can_delete, can_display_create_form, can_edit, can_execute, can_view

DEPARTMENT_VIEWER_ALL = 1
COMPANY_SCOPED_DEPARTMENT_MANAGER = 2


@pytest.mark.django_db
class TestIsAdminBypass:

    # is_admin=Trueのグループに所属していれば、どのモデル・アクションでも常にallowと判定されることを確認
    def test_admin_group_member_can_do_anything(self, sample_user):
        company = Company.objects.create(name='サンプル株式会社')
        admin_group = ManagementGroup.objects.create(name='全社管理者', is_admin=True)
        admin_group.members.add(sample_user)

        assert can_view(sample_user, 'Company', company) is True
        assert can_edit(sample_user, 'Company', company) is True
        assert can_delete(sample_user, 'Company', company) is True
        assert can_execute(sample_user, 'Company', company) is True
        assert can_create(sample_user, 'Company', Company(name='新会社')) is True


@pytest.mark.django_db
class TestScopeMatching:

    # scope={}(絞り込み無し)のルールはどのレコードにもallowすることを確認
    def test_empty_scope_matches_any_record(self, sample_user):
        anchor = _create_department('総務部', 'テスト工業株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('viewer', DEPARTMENT_VIEWER_ALL, anchor, sample_user)

        assert can_view(sample_user, 'Department', anchor) is True

    # 該当するeffect=denyのルールがあればdenyと判定されることを確認
    def test_explicit_deny_rule_denies(self, sample_user):
        anchor = _create_department('総務部', 'テスト工業株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('viewer', DEPARTMENT_VIEWER_ALL, anchor, sample_user)

        assert can_edit(sample_user, 'Department', anchor) is False

    # ルールが1件も無いモデル・アクションはデフォルトでdenyと判定されることを確認
    def test_no_matching_rule_defaults_to_deny(self, sample_user):
        anchor = _create_department('総務部', 'テスト工業株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('viewer', DEPARTMENT_VIEWER_ALL, anchor, sample_user)
        company = Company.objects.create(name='サンプル株式会社')

        assert can_view(sample_user, 'Company', company) is False

    # scopeのフィールドパスが一致する場合にallowと判定されることを確認
    def test_scope_field_path_matches(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)
        matching_department = Department.objects.create(company=anchor.company, name='開発部')

        assert can_view(sample_user, 'Department', matching_department) is True

    # scopeのフィールドパスが一致しない場合、そのグループは棄権しdenyになることを確認
    def test_scope_field_path_mismatch_defaults_to_deny(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)
        other_company = Company.objects.create(name='テスト工業株式会社')
        non_matching_department = Department.objects.create(company=other_company, name='総務部')

        assert can_view(sample_user, 'Department', non_matching_department) is False


@pytest.mark.django_db
class TestMultiGroupMerge:

    # 一方のグループがscope不一致で棄権しても、もう一方のグループのallowが有効になることを確認
    def test_abstaining_group_does_not_block_other_groups_allow(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)
        _create_group('viewer', DEPARTMENT_VIEWER_ALL, anchor, sample_user)
        other_company = Company.objects.create(name='テスト工業株式会社')
        target_department = Department.objects.create(company=other_company, name='総務部')

        # company_scoped_department_managerはscope不一致で棄権するが、department_viewer_allが常にallowするため最終的にTrue
        assert can_view(sample_user, 'Department', target_department) is True

    # 一方のグループが明示的にdeny、もう一方がallowの場合、deny優先で最終的にdenyになることを確認
    def test_explicit_deny_overrides_other_groups_allow(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)
        matching_department = Department.objects.create(company=anchor.company, name='開発部')

        # company_scoped_department_managerはこの部門の削除を明示的にdenyしている
        assert can_delete(sample_user, 'Department', matching_department) is False


@pytest.mark.django_db
class TestFieldLevelPermission:

    # フィールド権限にdenyルールがある場合、can_edit(..., field=...)がFalseになることを確認
    def test_field_level_deny(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)
        department = Department.objects.create(company=anchor.company, name='開発部')

        assert can_edit(sample_user, 'Department', department, field='company') is False

    # フィールド権限にルールが無い場合、デフォルトdenyになることを確認
    def test_field_level_no_rule_defaults_to_deny(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)
        department = Department.objects.create(company=anchor.company, name='開発部')

        assert can_edit(sample_user, 'Department', department, field='name') is False


@pytest.mark.django_db
class TestCanCreate:

    # フォーム入力値から組み立てた未保存インスタンスのscopeが一致すればallowと判定されることを確認
    def test_create_with_matching_scope_allows(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)
        candidate = Department(company=anchor.company, name='新部門')

        assert can_create(sample_user, 'Department', candidate) is True

    # 未保存インスタンスのscopeが一致しなければdenyと判定されることを確認
    def test_create_with_non_matching_scope_denies(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)
        other_company = Company.objects.create(name='テスト工業株式会社')
        candidate = Department(company=other_company, name='新部門')

        assert can_create(sample_user, 'Department', candidate) is False


@pytest.mark.django_db
class TestCanDisplayCreateForm:

    # createにallowのルールを持つグループに所属していれば、具体的な値が無くてもTrueと判定されることを確認
    def test_true_when_any_group_allows_create(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)

        assert can_display_create_form(sample_user, 'Department') is True

    # createがdeny(または未定義)のルールセットしか無ければFalseと判定されることを確認
    def test_false_when_no_group_allows_create(self, sample_user):
        anchor = _create_department('総務部', 'テスト工業株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('viewer', DEPARTMENT_VIEWER_ALL, anchor, sample_user)

        assert can_display_create_form(sample_user, 'Department') is False

    # どの管理グループにも所属していなければFalseと判定されることを確認
    def test_false_when_user_has_no_groups(self, sample_user):
        assert can_display_create_form(sample_user, 'Department') is False


def _create_department(name, company_name):
    company, _ = Company.objects.get_or_create(name=company_name)
    return Department.objects.create(company=company, name=name)


def _set_primary_department(user, department):
    EmployeeDepartment.objects.create(employee=user.employee, department=department, is_primary=True)


def _create_group(name, permission_set_id, department, member):
    group = ManagementGroup.objects.create(name=name, department=department, permission_set_id=permission_set_id)
    group.members.add(member)
    return group
