# テストガイド

このプロジェクトでは、pytestとPlaywrightを使用してテストを実装しています。

## テスト環境の構成

### 使用ツール

- **pytest**: Pythonのテストフレームワーク
- **pytest-django**: Django用のpytestプラグイン
- **pytest-playwright**: Playwright用のpytestプラグイン
- **playwright**: E2Eテスト用のブラウザ自動化ツール
- **pytest-xdist**: 並列テスト実行用のプラグイン

### ディレクトリ構造

```
app/
└── tests/
    ├── __init__.py
    ├── conftest.py              # 共通のフィクスチャ設定
    ├── unit/                    # ユニットテスト(モデルごとにファイル分割)
    │   ├── __init__.py
    │   └── task_test.py         # Taskモデルのテスト
    └── e2e/                     # E2Eテスト(機能ごとにファイル分割)
        ├── __init__.py
        ├── conftest.py          # E2E専用のフィクスチャ
        ├── home_test.py         # ホームページのE2Eテスト
        └── task_test.py         # タスク関連ページのE2Eテスト
```

## テストの実行方法

### すべてのテストを実行

```bash
pytest
```

### ユニットテストのみ実行

```bash
pytest app/tests/unit/
```

### E2Eテストのみ実行

```bash
pytest app/tests/e2e/ --browser chromium
```

### 詳細出力付きで実行

```bash
pytest -v
```

### カバレッジレポート付きで実行

```bash
pytest --cov=app --cov=config --cov-report=html --cov-report=term
```

カバレッジレポートは `htmlcov/index.html` に生成されます。

### 特定のテストファイルを実行

```bash
pytest app/tests/unit/task_test.py -v
```

### 特定のテストクラス・メソッドを実行

```bash
pytest app/tests/unit/task_test.py::TestTaskModel::test_create_task_with_minimal_fields -v
```

### 並列実行

```bash
pytest -n auto
```

## テストの書き方

### ユニットテスト（モデルテスト）

```python
import pytest
from app.models import Task


# Taskモデルのテストクラス
@pytest.mark.django_db
class TestTaskModel:

    # タスクを作成できることを確認
    def test_create_task(self):
        task = Task.objects.create(title='Test Task')
        assert task.id is not None
        assert task.title == 'Test Task'

    # フィクスチャを使用したテスト
    def test_with_user(self, sample_user):
        task = Task.objects.create(
            title='User Task',
            assigned_to=sample_user
        )
        assert task.assigned_to == sample_user
```

### E2Eテスト（Playwrightテスト）

```python
import pytest
from playwright.sync_api import Page, expect


# ホームページのE2Eテスト
@pytest.mark.django_db
class TestHomePage:

    # ホームページが正常に読み込まれることを確認
    def test_home_page_loads(self, page: Page, live_server_url):
        page.goto(live_server_url)

        # 要素の確認
        title_element = page.locator('#title')
        expect(title_element).to_have_text('Task Manager')

    # テストデータを使用したE2Eテスト
    def test_with_data(self, page: Page, live_server_url, setup_test_data):
        page.goto(f'{live_server_url}/tasks/')

        # テーブルの存在確認
        task_table = page.locator('#task-table')
        expect(task_table).to_be_visible()
```

## 便利なフィクスチャ

### `sample_user` (app/tests/conftest.py)

テスト用のサンプルユーザーを作成します。

```python
def test_example(sample_user):
    assert sample_user.username == 'testuser'
```

### `setup_test_data` (app/tests/e2e/conftest.py)

E2Eテスト用のサンプルデータを作成します。

```python
def test_example(setup_test_data):
    user = setup_test_data['user']
    task_count = setup_test_data['task_count']
    assert task_count == 3
```

### `live_server_url` (pytest-django)

DjangoライブサーバーのURLを提供します。

```python
def test_example(page, live_server_url):
    page.goto(live_server_url)
```

## pytest.iniオプション

[pyproject.toml](../pyproject.toml)で以下の設定を行っています：

- `DJANGO_SETTINGS_MODULE`: Djangoの設定モジュール
- `python_files`: テストファイルのパターン
- `python_classes`: テストクラスのパターン
- `python_functions`: テスト関数のパターン
- `testpaths`: テストディレクトリ（app/tests）
- `addopts`: pytest実行時のオプション
  - `--strict-markers`: 未定義のマーカー使用時にエラー
  - `--strict-config`: 設定エラー時にエラー
  - `--showlocals`: 失敗時にローカル変数を表示
  - `--reuse-db`: データベースを再利用（高速化）
- `env`: 環境変数の設定
  - `DJANGO_ALLOW_ASYNC_UNSAFE=true`: Playwright用の非同期設定

## トラブルシューティング

### E2Eテストで非同期エラーが出る

pyproject.tomlで`DJANGO_ALLOW_ASYNC_UNSAFE=true`が設定されていますが、もし問題が発生した場合は以下のように実行してください：

```bash
DJANGO_ALLOW_ASYNC_UNSAFE=true pytest app/tests/e2e/
```

### ブラウザが起動しない（headed mode）

ヘッドレス環境（CI/CD等）では、`--headed`オプションを使用しないでください。デフォルトでヘッドレスモードで実行されます。

### データベースのマイグレーションエラー

マイグレーションを実行してください：

```bash
source .venv/bin/activate
python manage.py migrate
```

### テストデータベースが作成されない

`--reuse-db`オプションを削除して実行してみてください：

```bash
pytest --create-db
```

## CI/CD環境での実行

GitHub ActionsなどのCI環境では、以下のように実行できます：

```yaml
- name: Run tests
  run: |
    source .venv/bin/activate
    pytest --browser chromium
```

## 参考リンク

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [pytest-django公式ドキュメント](https://pytest-django.readthedocs.io/)
- [Playwright公式ドキュメント](https://playwright.dev/python/)
- [pytest-playwright公式ドキュメント](https://github.com/microsoft/playwright-pytest)
