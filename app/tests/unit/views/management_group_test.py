import pytest
from app.models import ManagementGroup


@pytest.mark.django_db
class TestManagementGroupIndexView:

    # 未ログインの場合、ログインページにリダイレクトされることを確認
    def test_index_requires_login(self, client):
        response = client.get('/management_groups/')
        assert response.status_code == 302
        assert response.url.startswith('/login/')

    # 管理者以外がアクセスすると403が返ることを確認
    def test_index_by_non_admin_returns_403(self, auth_client):
        response = auth_client.get('/management_groups/')
        assert response.status_code == 403

    # 管理者は一覧を取得できることを確認
    def test_index_by_admin_succeeds(self, admin_client):
        ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        response = admin_client.get('/management_groups/')
        assert response.status_code == 200
        assert len(response.context['management_groups']) == 1


@pytest.mark.django_db
class TestManagementGroupShowView:

    # 管理者以外がアクセスすると403が返ることを確認
    def test_show_by_non_admin_returns_403(self, auth_client):
        group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        response = auth_client.get(f'/management_groups/{group.id}/')
        assert response.status_code == 403

    # 管理者は詳細を取得できることを確認
    def test_show_by_admin_succeeds(self, admin_client):
        group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        response = admin_client.get(f'/management_groups/{group.id}/')
        assert response.status_code == 200
        assert response.context['management_group'] == group


@pytest.mark.django_db
class TestManagementGroupCreateView:

    # 管理者以外がアクセスすると403が返ることを確認
    def test_new_by_non_admin_returns_403(self, auth_client):
        response = auth_client.get('/management_groups/new/')
        assert response.status_code == 403

    # 管理者はGETでフォームを取得できることを確認
    def test_get_returns_form(self, admin_client):
        response = admin_client.get('/management_groups/new/')
        assert response.status_code == 200
        assert 'form' in response.context

    # 有効なデータでPOSTするとグループが作成され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_creates_group_and_redirects(self, admin_client, sample_user):
        response = admin_client.post('/management_groups/new/', {
            'name': '開発チーム',
            'members': [sample_user.id],
            'is_admin': True,
        })

        group = ManagementGroup.objects.get(name='開発チーム')
        assert response.status_code == 302
        assert response.url == f'/management_groups/{group.id}/'


@pytest.mark.django_db
class TestManagementGroupEditView:

    # 管理者以外がアクセスすると403が返ることを確認
    def test_edit_by_non_admin_returns_403(self, auth_client):
        group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        response = auth_client.get(f'/management_groups/{group.id}/edit/')
        assert response.status_code == 403

    # 有効なデータでPOSTすると更新され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_updates_group_and_redirects(self, admin_client):
        group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        response = admin_client.post(f'/management_groups/{group.id}/edit/', {
            'name': '運用チーム',
            'members': [],
            'is_admin': True,
        })

        group.refresh_from_db()
        assert response.status_code == 302
        assert group.name == '運用チーム'


@pytest.mark.django_db
class TestManagementGroupDeleteView:

    # 管理者以外がアクセスすると403が返ることを確認
    def test_delete_by_non_admin_returns_403(self, auth_client):
        group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        response = auth_client.post(f'/management_groups/{group.id}/delete/')
        assert response.status_code == 403
        assert ManagementGroup.objects.filter(id=group.id).count() == 1

    # 管理者はPOSTで削除でき、一覧ページにリダイレクトされることを確認
    def test_post_deletes_group_and_redirects_to_index(self, admin_client):
        group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        response = admin_client.post(f'/management_groups/{group.id}/delete/')

        assert response.status_code == 302
        assert response.url == '/management_groups/'
        assert ManagementGroup.objects.filter(id=group.id).count() == 0
