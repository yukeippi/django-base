from django.core.management.base import BaseCommand
from app import seeds


# 動作確認用のシードデータを投入する(モデルごとの生成ロジックはapp/seeds/以下に定義する)
class Command(BaseCommand):
    help = '動作確認用のシードデータを投入する'

    def handle(self, *_args, **_options):
        seeds.employee.create()
        seeds.company.create()
        seeds.department.create()
        seeds.management_group.create()
        seeds.employee_department.create()

        self.stdout.write(self.style.SUCCESS(
            'シードデータを投入しました。(ログイン例: 社員番号=E0001 パスワード=password123)'
        ))
