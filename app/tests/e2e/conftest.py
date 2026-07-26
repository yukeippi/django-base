import pytest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command


# E2Eテスト用のデータベース設定とマイグレーション
@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('migrate', '--run-syncdb')


# ライブサーバーのURLを返すフィクスチャ
@pytest.fixture(scope='function')
def live_server_url(live_server):
    return live_server.url


# E2Eテスト用のテストデータをセットアップ
@pytest.fixture(scope='function')
def setup_test_data(db):
    from django.contrib.auth.models import User
    from app.models import Task
    from datetime import date, timedelta

    # ユーザーを作成
    user = User.objects.create_user(
        username='e2euser',
        email='e2e@example.com',
        password='e2epass123'
    )

    # サンプルタスクを作成
    Task.objects.create(
        title='E2E Test Task 1',
        description='This is a test task for E2E testing',
        status='todo',
        priority=1,
        assigned_to=user
    )

    Task.objects.create(
        title='E2E Test Task 2',
        description='Another test task',
        status='in_progress',
        priority=2,
        assigned_to=user,
        due_date=date.today() + timedelta(days=7)
    )

    Task.objects.create(
        title='E2E Test Task 3',
        description='Completed task',
        status='done',
        priority=3
    )

    return {
        'user': user,
        'task_count': 3
    }
