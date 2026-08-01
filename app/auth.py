# app内で共有する認証・認可関連の処理をここに置く


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
