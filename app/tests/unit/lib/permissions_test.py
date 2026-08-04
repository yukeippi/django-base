import pytest
from app.lib.permissions import can_delete_task, can_edit_task, get_applicable_management_groups, is_admin
from app.models import Company, Department, DepartmentHierarchy, EmployeeDepartment, ManagementGroup, Task


# app/permissions.pyの権限判定ロジックのテストクラス
@pytest.mark.django_db
class TestIsAdmin:

    # is_staffがTrueのユーザーは管理者と判定されることを確認
    def test_staff_user_is_admin(self, admin_user):
        assert is_admin(admin_user) is True

    # is_staffがFalseのユーザーは管理者ではないと判定されることを確認
    def test_regular_user_is_not_admin(self, sample_user):
        assert is_admin(sample_user) is False


@pytest.mark.django_db
class TestCanEditTask:

    # 作成者本人は編集可能と判定されることを確認
    def test_creator_can_edit(self, sample_user):
        task = Task.objects.create(title='Task', created_by=sample_user)
        assert can_edit_task(sample_user, task) is True

    # 担当者本人は編集可能と判定されることを確認
    def test_assignee_can_edit(self, sample_user):
        task = Task.objects.create(title='Task', assigned_to=sample_user)
        assert can_edit_task(sample_user, task) is True

    # 管理者はどのタスクでも編集可能と判定されることを確認
    def test_admin_can_edit_any_task(self, admin_user, other_user):
        task = Task.objects.create(title='Task', created_by=other_user)
        assert can_edit_task(admin_user, task) is True

    # 作成者でも担当者でも管理者でもないユーザーは編集不可と判定されることを確認
    def test_unrelated_user_cannot_edit(self, sample_user, other_user):
        task = Task.objects.create(title='Task', created_by=other_user)
        assert can_edit_task(sample_user, task) is False


@pytest.mark.django_db
class TestCanDeleteTask:

    # 作成者本人は削除可能と判定されることを確認
    def test_creator_can_delete(self, sample_user):
        task = Task.objects.create(title='Task', created_by=sample_user)
        assert can_delete_task(sample_user, task) is True

    # 作成者でも担当者でも管理者でもないユーザーは削除不可と判定されることを確認
    def test_unrelated_user_cannot_delete(self, sample_user, other_user):
        task = Task.objects.create(title='Task', created_by=other_user)
        assert can_delete_task(sample_user, task) is False


@pytest.mark.django_db
class TestGetApplicableManagementGroups:

    # 主務部門そのものに割り当てられたグループがメンバーに適用されることを確認
    def test_group_assigned_to_own_department_applies(self, sample_user):
        department = _create_department('開発部')
        _set_primary_department(sample_user, department)
        group = ManagementGroup.objects.create(name='開発部グループ', department=department)
        group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == [group]

    # 親部門に割り当てられたグループがメンバーに適用されることを確認
    def test_group_assigned_to_parent_department_applies(self, sample_user):
        company = Company.objects.create(name='サンプル株式会社')
        parent = Department.objects.create(company=company, name='本社')
        child = Department.objects.create(company=company, name='営業部')
        DepartmentHierarchy.objects.create(department=child, parent_department=parent)
        _set_primary_department(sample_user, child)
        group = ManagementGroup.objects.create(name='本社グループ', department=parent)
        group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == [group]

    # 兄弟部門に割り当てられたグループがメンバーに適用されることを確認
    def test_group_assigned_to_sibling_department_applies(self, sample_user):
        company = Company.objects.create(name='サンプル株式会社')
        parent = Department.objects.create(company=company, name='本社')
        sales = Department.objects.create(company=company, name='営業部')
        hr = Department.objects.create(company=company, name='人事部')
        DepartmentHierarchy.objects.create(department=sales, parent_department=parent)
        DepartmentHierarchy.objects.create(department=hr, parent_department=parent)
        _set_primary_department(sample_user, sales)
        group = ManagementGroup.objects.create(name='人事部グループ', department=hr)
        group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == [group]

    # 親・兄弟のいずれにも該当しない部門のグループは適用されないことを確認
    def test_unrelated_department_group_does_not_apply(self, sample_user):
        company = Company.objects.create(name='サンプル株式会社')
        own_department = Department.objects.create(company=company, name='開発部')
        unrelated_department = Department.objects.create(company=company, name='総務部')
        _set_primary_department(sample_user, own_department)
        group = ManagementGroup.objects.create(name='総務部グループ', department=unrelated_department)
        group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == []

    # is_admin=Trueのグループはメンバーであれば部門に関係なく適用されることを確認
    def test_admin_group_applies_regardless_of_department(self, sample_user):
        group = ManagementGroup.objects.create(name='全社管理者グループ', is_admin=True)
        group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == [group]

    # メンバーでなければ、部門が一致していても適用されないことを確認
    def test_non_member_does_not_get_group_applied(self, sample_user):
        department = _create_department('開発部')
        _set_primary_department(sample_user, department)
        ManagementGroup.objects.create(name='開発部グループ', department=department)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == []

    # 主務部門が無い社員には、is_admin以外のグループが適用されないことを確認
    def test_employee_without_primary_department_only_gets_admin_groups(self, sample_user):
        department = _create_department('開発部')
        non_admin_group = ManagementGroup.objects.create(name='開発部グループ', department=department)
        non_admin_group.members.add(sample_user)
        admin_group = ManagementGroup.objects.create(name='全社管理者グループ', is_admin=True)
        admin_group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == [admin_group]

    # Employeeが無いユーザーには、is_admin以外のグループが適用されないことを確認
    def test_user_without_employee_only_gets_admin_groups(self, admin_user):
        department = _create_department('開発部')
        non_admin_group = ManagementGroup.objects.create(name='開発部グループ', department=department)
        non_admin_group.members.add(admin_user)
        admin_group = ManagementGroup.objects.create(name='全社管理者グループ', is_admin=True)
        admin_group.members.add(admin_user)

        applicable = get_applicable_management_groups(admin_user)

        assert applicable == [admin_group]

    # 複数のグループが同時に適用されるケースを確認
    def test_multiple_groups_can_apply_simultaneously(self, sample_user):
        department = _create_department('開発部')
        _set_primary_department(sample_user, department)
        own_group = ManagementGroup.objects.create(name='開発部グループ', department=department)
        own_group.members.add(sample_user)
        admin_group = ManagementGroup.objects.create(name='全社管理者グループ', is_admin=True)
        admin_group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert set(applicable) == {own_group, admin_group}

    # 部門階層にレコードが無い場合は自分自身のみ判定されることを確認
    def test_department_without_hierarchy_record_only_matches_self(self, sample_user):
        company = Company.objects.create(name='サンプル株式会社')
        own_department = Department.objects.create(company=company, name='開発部')
        other_department = Department.objects.create(company=company, name='営業部')
        _set_primary_department(sample_user, own_department)
        matching_group = ManagementGroup.objects.create(name='開発部グループ', department=own_department)
        matching_group.members.add(sample_user)
        other_group = ManagementGroup.objects.create(name='営業部グループ', department=other_department)
        other_group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == [matching_group]

    # 子部門に割り当てられたグループは適用されないことを確認(一段階の上方向・横方向のみが対象で、下方向には適用されないことの確認)
    def test_group_assigned_to_child_department_does_not_apply(self, sample_user):
        company = Company.objects.create(name='サンプル株式会社')
        parent = Department.objects.create(company=company, name='本社')
        child = Department.objects.create(company=company, name='営業部')
        DepartmentHierarchy.objects.create(department=child, parent_department=parent)
        _set_primary_department(sample_user, parent)
        group = ManagementGroup.objects.create(name='営業部グループ', department=child)
        group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == []

    # department=NULLの不正なManagementGroup(clean()を経由せずmigration等で発生しうる状態)が、
    # 主務部門が最上位部門(親部門なし)のユーザーに誤って適用されないことを確認(fail-closed)
    def test_group_with_null_department_does_not_apply_to_top_level_department_user(self, sample_user):
        company = Company.objects.create(name='サンプル株式会社')
        top_level_department = Department.objects.create(company=company, name='本社')
        DepartmentHierarchy.objects.create(department=top_level_department)
        _set_primary_department(sample_user, top_level_department)
        other_department = Department.objects.create(company=company, name='営業部')
        group = ManagementGroup.objects.create(name='不正データグループ', department=other_department)
        group.members.add(sample_user)
        # full_clean()を経由するsave()ではdepartment=NULLは弾かれるため、
        # migrate直後のデータ等を再現するために.update()でDBを直接書き換える
        ManagementGroup.objects.filter(pk=group.pk).update(department=None)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == []


def _create_department(name):
    company = Company.objects.create(name=f'{name}の会社')
    return Department.objects.create(company=company, name=name)


def _set_primary_department(user, department):
    EmployeeDepartment.objects.create(employee=user.employee, department=department, is_primary=True)
