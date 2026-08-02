import pytest
from app.permissions import can_delete_task, can_edit_task, is_admin
from app.models import Task


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
