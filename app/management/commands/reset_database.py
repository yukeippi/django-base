from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection


# データベースを初期化する(全テーブルを削除してマイグレーションを再適用する)
class Command(BaseCommand):
    help = 'データベースを初期化する(全テーブルを削除してマイグレーションを再適用する)'

    def add_arguments(self, parser):
        parser.add_argument('--seed', action='store_true', help='初期化後にシードデータを投入する')
        parser.add_argument('--noinput', action='store_true', help='確認プロンプトを表示せずに実行する')

    def handle(self, *args, **options):
        if not options['noinput'] and not self._confirm():
            self.stdout.write('中止しました。')
            return

        self.stdout.write('データベースをリセットしています...')
        with connection.cursor() as cursor:
            cursor.execute('DROP SCHEMA public CASCADE;')
            cursor.execute('CREATE SCHEMA public;')

        call_command('migrate')
        self.stdout.write(self.style.SUCCESS('データベースのリセットが完了しました。'))

        if options['seed']:
            call_command('seed_database')

    def _confirm(self):
        answer = input('データベースの全データを削除します。よろしいですか? [y/N]: ')
        return answer.lower() == 'y'
