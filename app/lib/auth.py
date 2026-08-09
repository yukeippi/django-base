# app内で共有する認証関連の処理をここに置く

from django.contrib.auth.backends import ModelBackend
from app.models import Employee


# 社員番号(employee_number)でログインするための認証バックエンド
class EmployeeNumberBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = Employee.objects.select_related('user').get(employee_number=username).user
        except Employee.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
