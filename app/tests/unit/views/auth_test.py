import pytest


# ログインビューのテストクラス
@pytest.mark.django_db
class TestLoginView:

    # GETリクエストでログインフォームが表示されることを確認
    def test_get_returns_form(self, client):
        response = client.get('/login/')
        assert response.status_code == 200
        assert 'form' in response.context

    # 正しい認証情報でログインするとタスク一覧にリダイレクトされることを確認
    def test_post_valid_credentials_logs_in_and_redirects(self, client, sample_user):
        response = client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass123',
        })

        assert response.status_code == 302
        assert response.url == '/tasks/'
        assert response.wsgi_request.user.is_anonymous is False

    # 誤った認証情報の場合、ログインできずフォームが再表示されることを確認
    def test_post_invalid_credentials_redisplays_form(self, client, sample_user):
        response = client.post('/login/', {
            'username': 'testuser',
            'password': 'wrongpassword',
        })

        assert response.status_code == 200
        assert response.context['form'].is_valid() is False


# ログアウトビューのテストクラス
@pytest.mark.django_db
class TestLogoutView:

    # POSTするとログアウトされ、ログインページにリダイレクトされることを確認
    def test_post_logs_out_and_redirects(self, auth_client):
        response = auth_client.post('/logout/')

        assert response.status_code == 302
        assert response.url == '/login/'

        # ログアウト後はタスク一覧にアクセスするとログインページにリダイレクトされる
        response = auth_client.get('/tasks/')
        assert response.status_code == 302
        assert response.url.startswith('/login/')
