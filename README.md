# Django Project

## プロジェクト概要

<!-- TODO: このアプリケーションが何を実現するものか、対象ユーザー、主要な機能などを記載
     (このリポジトリを雛形として新規プロジェクトを始めた場合は、このセクションを新プロジェクトの内容に書き換えてください) -->

## 環境構築

### 1. 依存パッケージのインストール

```bash
uv sync
```

### 2. 環境変数の設定

`.env.example`をコピーして`.env`ファイルを作成します。

```bash
cp .env.example .env
```

`.env`ファイルを編集して、必要な環境変数を設定してください。

```env
# Django Settings
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True

# Database
DATABASE_URL=postgres://postgres:postgres@db:5432/postgres
```

**DJANGO_SECRET_KEYの生成方法:**

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. settings.pyの環境変数対応

`config/settings.py`を修正して、環境変数から値を読み込むようにします。

#### 3.1 django-environのインポートと初期化

ファイルの先頭に以下を追加します:

```python
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environ
env = environ.Env(
    DEBUG=(bool, False)
)

# Read .env file
environ.Env.read_env(BASE_DIR / '.env')
```

#### 3.2 SECRET_KEYの設定

ハードコードされたSECRET_KEYを環境変数から読み込むように変更します:

```python
# 変更前
SECRET_KEY = 'django-insecure-...'

# 変更後
SECRET_KEY = env('DJANGO_SECRET_KEY')
```

#### 3.3 DEBUGの設定

DEBUGも環境変数から読み込むように変更します:

```python
# 変更前
DEBUG = True

# 変更後
DEBUG = env.bool('DEBUG', default=False)
```

#### 3.4 DATABASESの設定

データベース設定を環境変数のDATABASE_URLから読み込むように変更します:

```python
# 変更前
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 変更後
DATABASES = {
    'default': env.db()
}
```

`env.db()`は`DATABASE_URL`環境変数を自動的にパースして、Django用のデータベース設定に変換します。

### 4. Djangoプロジェクトのセットアップ

既にプロジェクトは作成済みですが、新規に作成する場合は以下のコマンドを実行します。

```bash
# プロジェクト作成
django-admin startproject config .

# アプリケーション作成
python manage.py startapp app
```

### 5. データベースのマイグレーション

```bash
# マイグレーションファイルの作成
python manage.py makemigrations

# マイグレーションの適用
python manage.py migrate
```

### 6. 開発サーバーの起動

```bash
python manage.py runserver
```

ブラウザで http://127.0.0.1:8000/ にアクセスして確認できます。

## テスト

このプロジェクトでは、pytestとPlaywrightを使用してテストを実装しています。

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
pytest app/tests/e2e/
```

### 詳細な出力付きで実行

```bash
pytest -v
```

### カバレッジレポート付きで実行

```bash
pytest --cov=app --cov=config --cov-report=html --cov-report=term
```

詳細なテストガイドは [docs/testing.md](docs/testing.md) を参照してください。

## 開発用コマンド

### TODO/FIXME/OPTIMIZEコメントの一覧表示

Railsの`rails notes`相当のコマンドです。`app`/`config`/`common`配下のコード中の`TODO`/`FIXME`/`OPTIMIZE`コメントを一覧表示します。

```bash
python manage.py notes

# 特定のタグのみ表示
python manage.py notes --tag=FIXME
```

### データベースのリセット・シードデータ投入

開発用データベースを初期化し、動作確認用のサンプルデータ(社員・管理グループなど)を投入します。

```bash
# データベースを初期化してシードデータを投入
python manage.py reset_database --seed

# 確認プロンプトを省略する場合
python manage.py reset_database --seed --noinput

# リセットせずシードデータだけ投入する場合
python manage.py seed_database
```

## 使用している主要なパッケージ

- Django 6.0
- django-environ 0.12.0 (環境変数管理)
- psycopg2-binary 2.9.11 (PostgreSQL接続)
- pytest 9.0.3+ (テストフレームワーク)
- pytest-django 4.12.0+ (Django用pytestプラグイン)
- pytest-playwright 0.7.2+ (Playwright用pytestプラグイン)
- pytest-xdist 3.8.0+ (並列テスト実行)
- playwright 1.58.0+ (E2Eテスト用ブラウザ自動化)

## 環境変数について

このプロジェクトでは`django-environ`を使用して環境変数を管理しています。

- `.env`ファイルに設定を記述
- 環境変数が設定されている場合は、環境変数の値が優先される
- `.env`ファイルは`.gitignore`に含まれており、Gitにコミットされません

### 必須の環境変数

- `DJANGO_SECRET_KEY`: Djangoのシークレットキー
  - **重要**: この環境変数が設定されていない場合、Djangoは起動しません
  - エラー例: `django.core.exceptions.ImproperlyConfigured: Set the DJANGO_SECRET_KEY environment variable`
  - 生成方法は上記の「2. 環境変数の設定」を参照してください
- `DATABASE_URL`: データベース接続URL (形式: `postgres://USER:PASSWORD@HOST:PORT/NAME`)
  - **重要**: この環境変数が設定されていない場合、Djangoは起動しません

### オプションの環境変数

- `DEBUG`: デバッグモード (デフォルト: False)
