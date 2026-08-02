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


# E2Eテスト用のユーザー(Employee付き)を作成するフィクスチャ
@pytest.fixture(scope='function')
def e2e_user(db):
    from django.contrib.auth.models import User
    from app.models import Employee
    user = User.objects.create_user(
        username='e2euser',
        email='e2e@example.com',
        password='e2epass123'
    )
    Employee.objects.create(user=user, employee_number='E9001')
    return user


# ブラウザ上でログインフォームを操作し、e2e_userとしてログイン済みの状態にするフィクスチャ
@pytest.fixture(scope='function')
def logged_in_page(page, live_server_url, e2e_user):
    page.goto(f'{live_server_url}/login/')
    page.fill('#id_username', e2e_user.employee.employee_number)
    page.fill('#id_password', 'e2epass123')
    page.click('#login-submit')
    return page


# E2Eテスト用のサンプルタスクをセットアップ(e2e_userでログイン済みの状態と合わせて使う想定)
@pytest.fixture(scope='function')
def setup_test_data(e2e_user):
    from app.models import Task
    from datetime import date, timedelta

    # サンプルタスクを作成
    Task.objects.create(
        title='E2E Test Task 1',
        description='This is a test task for E2E testing #1',
        status='todo',
        priority=1,
        assigned_to=e2e_user,
        created_by=e2e_user,
    )

    Task.objects.create(
        title='E2E Test Task 2',
        description='Another test task #2',
        status='in_progress',
        priority=2,
        assigned_to=e2e_user,
        created_by=e2e_user,
        due_date=date.today() + timedelta(days=7)
    )

    Task.objects.create(
        title='E2E Test Task 3',
        description='Completed task #3',
        status='done',
        priority=3,
        created_by=e2e_user,
    )

    return {
        'user': e2e_user,
        'task_count': 3
    }
