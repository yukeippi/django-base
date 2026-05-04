# Django Excel ハンドラー実験プロジェクト

Django + openpyxl を使った **汎用 Excel インポート・エクスポートハンドラー** の実験場です。
`app/excel_base.py` を別プロジェクトにコピーして再利用することを想定して設計しています。

## Excel ハンドラーの概要

### ファイル構成

| ファイル | 役割 |
|---|---|
| `app/excel_base.py` | 汎用ロジック（他プロジェクトへの転用用） |
| `app/excel.py` | `Task` モデル用の具体的な設定 |

### 主要クラス

**`ColumnDef`** — 1列分の定義（DB カラム名と Excel ヘッダー名のマッピング）

```python
ColumnDef(
    model_field='due_date',      # モデルのフィールド名
    excel_header='期限',          # Excel の列ヘッダー名
    required=False,
    cell_to_value=parse_date_cell,   # インポート時: セル値 → Python 値
    value_to_cell=lambda v: str(v) if v else '',  # エクスポート時: Python 値 → セル値
)
```

**`ExcelHandler`** — インポート・エクスポートの汎用基底クラス

```python
handler.import_from_excel(file, has_header=True)  # → (作成件数, エラーリスト)
handler.export_to_new_excel(queryset)              # → HttpResponse
handler.export_to_template(queryset, template_path)  # → HttpResponse
```

インポートはエラーが 1 件でもあれば **全件ロールバック**。バリデーションは Django の `Model.full_clean()` に委譲。

### 別モデルへの適用方法

`TaskExcelHandler`（`app/excel.py`）を参考に、`ExcelHandler` を継承してクラスを定義するだけです。

```python
from app.excel_base import ColumnDef, ExcelHandler
from .models import Product

class ProductExcelHandler(ExcelHandler):
    model = Product
    sheet_name = '商品'
    filename = 'products.xlsx'
    columns = [
        ColumnDef(model_field='name',  excel_header='商品名', required=True),
        ColumnDef(model_field='price', excel_header='価格',
                  cell_to_value=lambda v: int(v) if v else 0),
    ]
```

あとは `views.py` でインスタンスを作って呼び出すだけです。

```python
# インポート
handler = ProductExcelHandler()
count, errors = handler.import_from_excel(request.FILES['file'])

# エクスポート
return ProductExcelHandler().export_to_new_excel(Product.objects.all())
```

---

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

## 使用している主要なパッケージ

- Django 5.2.8
- django-environ 0.12.0 (環境変数管理)
- psycopg2-binary 2.9.11 (PostgreSQL接続)
- pytest 8.3.4+ (テストフレームワーク)
- pytest-django 4.9.0+ (Django用pytestプラグイン)
- playwright 1.49.1+ (E2Eテスト用ブラウザ自動化)

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
