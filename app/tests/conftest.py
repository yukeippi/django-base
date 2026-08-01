import pytest
import os
from django.conf import settings

# Playwright用の非同期設定
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'


# テスト用のデータベース設定
@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    from django.core.management import call_command

    with django_db_blocker.unblock():
        # マイグレーションを実行
        call_command('migrate', '--run-syncdb')


# テスト用のサンプルユーザーを作成するフィクスチャ
@pytest.fixture
def sample_user(db):
    from django.contrib.auth.models import User
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


# 別ユーザー(権限チェックで「本人ではない一般ユーザー」として使う)を作成するフィクスチャ
@pytest.fixture
def other_user(db):
    from django.contrib.auth.models import User
    return User.objects.create_user(
        username='otheruser',
        email='other@example.com',
        password='otherpass123'
    )


# sample_userでログイン済みのクライアントを返すフィクスチャ
@pytest.fixture
def auth_client(sample_user):
    from django.test import Client
    client = Client()
    client.force_login(sample_user)
    return client


# other_userでログイン済みのクライアントを返すフィクスチャ(auth_clientとは別セッション)
@pytest.fixture
def other_auth_client(other_user):
    from django.test import Client
    client = Client()
    client.force_login(other_user)
    return client
