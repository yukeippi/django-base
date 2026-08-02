from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from app.models import Employee


# 動作確認用のシードデータ(社員)を投入する
class Command(BaseCommand):
    help = '動作確認用のシードデータ(社員)を投入する'

    def handle(self, *_args, **_options):
        self._create_employee('E0001', '太郎', '山田', is_staff=True)
        self._create_employee('E0002', '花子', '鈴木')

        self.stdout.write(self.style.SUCCESS(
            'シードデータを投入しました。(ログイン例: 社員番号=E0001 パスワード=password123)'
        ))

    # 社員番号をログインIDとするEmployee(+User)を作成する
    def _create_employee(self, employee_number, first_name, last_name, is_staff=False):
        user = User.objects.create_user(
            username=employee_number,
            password='password123',
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
        )
        return Employee.objects.create(user=user, employee_number=employee_number)
