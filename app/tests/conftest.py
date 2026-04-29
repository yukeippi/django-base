import pytest
import os
from django.conf import settings

# Playwright用の非同期設定
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'


# --line オプションを追加する（指定した行番号を含むテストだけを実行する）
def pytest_addoption(parser):
    parser.addoption("--line", action="store", default=None, type=int,
                     help="指定した行番号を含むテストだけを実行する（例: --line 206）")


# --line オプションが指定された場合、その行番号を含むテストだけに絞り込む
def pytest_collection_modifyitems(config, items):
    line = config.getoption("--line", default=None)
    if line is None:
        return

    candidates = sorted(
        [(item.location[1] + 1, item) for item in items if item.location[1] is not None],
        key=lambda x: x[0],
    )

    selected = None
    for item_line, item in candidates:
        if item_line <= line:
            selected = item
        else:
            break

    items[:] = [selected] if selected else []


# テスト用データベースのセットアップ
@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    from django.core.management import call_command

    with django_db_blocker.unblock():
        call_command('migrate', '--run-syncdb')


# テスト用サンプルユーザーを作成するフィクスチャ
@pytest.fixture
def sample_user(db):
    from django.contrib.auth.models import User
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
