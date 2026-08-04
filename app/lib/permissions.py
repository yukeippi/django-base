# app内で共有する権限判定ロジックをここに置く

from app.models import DepartmentHierarchy, ManagementGroup


# 管理者かどうかを判定(is_staffを管理者フラグとして扱う)
def is_admin(user):
    return user.is_staff


# タスクを編集できるかどうかを判定
# 管理者、作成者本人、担当者本人のいずれかであれば編集可能
def can_edit_task(user, task):
    if is_admin(user):
        return True
    return task.created_by_id == user.id or task.assigned_to_id == user.id


# タスクを削除できるかどうかを判定
# 編集権限と同じ基準を採用する
def can_delete_task(user, task):
    return can_edit_task(user, task)


# ログインユーザーに適用される管理グループの一覧を返す
def get_applicable_management_groups(user):
    groups = ManagementGroup.objects.filter(members=user)

    primary_department = _get_primary_department(user)

    applicable = []
    for group in groups:
        if group.is_admin:
            applicable.append(group)
            continue
        if primary_department and _is_self_parent_or_sibling(group.department, primary_department):
            applicable.append(group)
    return applicable


# ============================================================
# ここから先はprivateヘルパー
# ============================================================


# ユーザーの社員情報から主務部門を取得する(Employeeが無い/主務が無い場合はNone)
def _get_primary_department(user):
    employee = getattr(user, 'employee', None)
    if employee is None:
        return None
    primary = employee.employee_departments.filter(is_primary=True).first()
    return primary.department if primary else None


# 対象部門(group_department)が、基準部門(primary_department)自身・親・兄弟のいずれかに一致するかを判定する
def _is_self_parent_or_sibling(group_department, primary_department):
    # department未設定(本来は不正なデータ)の場合は、誤って適用されないようfail closedとする
    if group_department is None:
        return False

    if group_department == primary_department:
        return True

    hierarchy = DepartmentHierarchy.objects.filter(department=primary_department).first()
    if hierarchy is None:
        return False

    if group_department == hierarchy.parent_department:
        return True

    if hierarchy.parent_department is None:
        return False

    return DepartmentHierarchy.objects.filter(
        department=group_department, parent_department=hierarchy.parent_department
    ).exists()
