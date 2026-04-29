import pytest
import os
from django.conf import settings

# Playwright用の非同期設定
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    テスト用のデータベース設定
    """
    from django.core.management import call_command

    with django_db_blocker.unblock():
        # マイグレーションを実行
        call_command('migrate', '--run-syncdb')


@pytest.fixture
def sample_user(db):
    """
    テスト用のサンプルユーザーを作成するフィクスチャ
    """
    from django.contrib.auth.models import User
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
