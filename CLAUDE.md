# CLAUDE.md

このファイルは、このリポジトリでAIアシスタント(Claude Code等)が開発を行う際の全体像を伝えるためのドキュメントです。

このファイルは、Djangoプロジェクトの雛形(devcontainer / uv / django-environ / pytest+Playwright構成)に付属するテンプレートです。
このリポジトリをコピーして新規プロジェクトを始める場合、**「1. プロジェクト概要」と「8. ドメイン知識・業務ルール」を新プロジェクトの内容に書き換えてください**。それ以外の章(技術スタック〜テスト方針)は雛形として引き継がれる想定です。

## 1. プロジェクト概要

<!-- TODO: 一言要約を記載。詳細はREADME.mdの「プロジェクト概要」を参照 -->

詳細は [README.md](README.md) を参照。

## 2. 技術スタック

- Django 5.2.8
- PostgreSQL (psycopg2-binary 2.9.11 で接続)
- django-environ 0.12.0 (環境変数管理)
- pytest 8.3.4+ / pytest-django 4.9.0+ (テストフレームワーク)
- pytest-playwright 0.6.2+ / playwright 1.49.1+ (E2Eテスト用ブラウザ自動化)
- pytest-xdist 3.6.1+ (並列テスト実行)
- パッケージ管理: uv

## 3. ディレクトリ構成

```
config/          Djangoプロジェクト設定 (settings.py, urls.py, asgi.py, wsgi.py)
app/             メインアプリケーション
├── models/          モデル(1モデル1ファイル)
│   └── task.py
├── views/           ビュー(機能ごとにファイル分割)
│   ├── home.py
│   └── task.py
├── urls.py
├── admin.py
├── static/app/      アプリ固有の静的ファイル
│   └── task.css
├── templates/
│   ├── base/            共通レイアウト
│   │   └── base.html
│   └── app/
│       ├── index.html
│       └── task/        モデルごとのテンプレート (index/show/new/edit)
│           ├── index.html
│           └── show.html
└── tests/
    ├── unit/        ユニットテスト(モデルごとにファイル分割)
    └── e2e/         E2Eテスト(Playwright、機能ごとにファイル分割)
common/          複数アプリ間で共有するモジュール (auth.py, utils.py, mixins.py)
static/          プロジェクト全体の共通静的ファイル
└── common.css
```

## 4. セットアップ・よく使うコマンド

```bash
# 依存パッケージのインストール
uv sync

# 環境変数の設定 (.env.example をコピーして編集)
cp .env.example .env

# マイグレーション
python manage.py makemigrations
python manage.py migrate

# 開発サーバー起動
python manage.py runserver

# テスト実行
pytest                      # 全テスト
pytest app/tests/unit/      # ユニットテストのみ
pytest app/tests/e2e/       # E2Eテストのみ
pytest --cov=app --cov=config --cov-report=html --cov-report=term  # カバレッジ付き
```

詳細は [README.md](README.md) を参照。

## 5. 開発ルール

ファイル構成・命名規則などの詳細ルールは [.claude/instructions.md](.claude/instructions.md) を参照してください。

## 6. 環境変数

`django-environ` により `.env` ファイル(Gitにはコミットされない)から読み込みます。

### 必須

- `DJANGO_SECRET_KEY`: Djangoのシークレットキー(未設定だと起動不可)
- `DATABASE_URL`: データベース接続URL (`postgres://USER:PASSWORD@HOST:PORT/NAME`)

### オプション

- `DEBUG`: デバッグモード (デフォルト: `False`)

## 7. テスト方針

pytest + pytest-django + Playwright(E2E)でテストを実装しています。詳細は [docs/testing.md](docs/testing.md) を参照してください。

## 8. ドメイン知識・業務ルール

<!-- TODO: このアプリケーション固有の仕様・業務ルールをここに記載していく -->
