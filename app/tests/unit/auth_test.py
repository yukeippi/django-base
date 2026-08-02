import pytest
from django.contrib.auth.models import User
from app.auth import EmployeeNumberBackend
from app.models import Employee


# app/auth.pyの認証バックエンドのテストクラス
@pytest.mark.django_db
class TestEmployeeNumberBackend:

    # 正しい社員番号とパスワードで認証に成功することを確認
    def test_authenticate_with_correct_credentials(self):
        user = User.objects.create_user(username='backenduser', password='pass12345')
        Employee.objects.create(user=user, employee_number='E1001')

        authenticated_user = EmployeeNumberBackend().authenticate(
            request=None, username='E1001', password='pass12345'
        )

        assert authenticated_user == user

    # 誤ったパスワードでは認証に失敗することを確認
    def test_authenticate_with_wrong_password(self):
        user = User.objects.create_user(username='backenduser', password='pass12345')
        Employee.objects.create(user=user, employee_number='E1001')

        authenticated_user = EmployeeNumberBackend().authenticate(
            request=None, username='E1001', password='wrongpass'
        )

        assert authenticated_user is None

    # 存在しない社員番号では認証に失敗することを確認
    def test_authenticate_with_unknown_employee_number(self):
        authenticated_user = EmployeeNumberBackend().authenticate(
            request=None, username='UNKNOWN', password='pass12345'
        )

        assert authenticated_user is None
