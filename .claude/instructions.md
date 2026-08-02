# Django Development Guidelines

> **このファイルの位置づけ**: 別のDjangoプロジェクトにそのままコピーして使う、再利用可能な開発規約集(`CLAUDE.md`が「雛形として引き継ぐ」と定義している章の一つ)。書く内容は「このプロジェクトの現在の状態」ではなく、Djangoプロジェクト一般に適用できる規約・パターンにすること。
>
> - 各ルールの例に出てくる`Task`/`Employee`等のモデル名は、あくまでパターンを説明するための例示。実際のこのプロジェクトのモデル・ファイル構成と完全に一致している必要はない(コピー先の別プロジェクトではどのみち別のモデル名になる)
> - 一方、規約・パターンの説明自体に矛盾や誤りがある場合は、コピー先でも同じ混乱を招くため修正する

## File Structure Rules

models、forms、views、tests、templatesはディレクトリ化し、機能ごとにファイル分割してください。

### Examples
- models/todo.py
- views/todo.py
- tests/unit/models/todo_test.py
- tests/unit/forms/todo_test.py
- tests/unit/views/todo_test.py
- tests/e2e/todo_test.py

各ディレクトリに__init__.pyを配置すること。

`tests/unit/`配下は、ソース側の`models/`, `forms/`, `views/`, `lib/`と対応するレイヤーごとのディレクトリにさらに分割する(Railsの`test/models/`, `test/controllers/`に相当)。`app/lib/`(`auth.py`/`permissions.py`/`validators.py`等、app内で共有するロジック。詳細はCommon Module Rulesを参照)のテストも同様に`tests/unit/lib/`に置く(例: `tests/unit/lib/auth_test.py`)。`tests/e2e/`はページ単位のテストのため、このレイヤー分割は行わない。

## Layout Rules

もっとも低レイヤーの共通テンプレート(全ページの土台となるレイアウト)は `templates/layouts/` ディレクトリに置く。既定のレイアウトファイル名は `default.html` とする。将来的に別のレイアウトが必要になった場合は `layouts/admin.html` のように用途名を付けたファイルを追加する。

レイアウト本体はHTMLの骨格(`<head>`の共通アセット読み込みと`{% block %}`)だけにとどめ、極力コンパクトに保つ。ナビゲーションバーやフラッシュメッセージ表示のような、ページ間で共通だが内容として独立した部品は、レイアウトに直書きせず `app/templates/common/` 配下のパーシャル(`_navbar.html`, `_messages.html` など)に切り出し、レイアウトから `{% include %}` で読み込む(置き場所の考え方は下記Common Module Rulesを参照)。

### Example

```
app/templates/layouts/
└── default.html       # 骨格のみ。{% include %}で各パーシャルを読み込む

app/templates/common/
├── _navbar.html        # ナビゲーションバー
└── _messages.html      # フラッシュメッセージ表示
```

```html
<!-- layouts/default.html -->
<body>
    {% include 'common/_navbar.html' %}
    <div class="container">
        {% include 'common/_messages.html' %}
        {% block content %}{% endblock %}
    </div>
</body>
```

## Template Rules

テンプレートの継承は3段階にする。各ページ側は`{% block %}`の中身だけを記述する最小限の内容にする。

1. `layouts/default.html`: サイト全体の骨格(`<head>`の共通アセット読み込みと`{% block %}`定義)。詳細はLayout Rulesを参照
2. `app/<model>/base.html`: モデル単位の中間テンプレート。`layouts/default.html`を継承し、そのモデルの全ページで共通の`{% block %}`(モデル別CSSの読み込み等)をここで埋める。詳細はCSS Rulesを参照
3. `app/<model>/<page>.html`: ページごとのテンプレート。`app/<model>/base.html`を継承し、`title`/`content`など、そのページ固有の`{% block %}`だけを埋める

### Example

```html
<!-- app/article/base.html -->
{% extends 'layouts/default.html' %}
{% load static %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'app/article.css' %}">
{% endblock %}
```

```html
<!-- app/article/index.html -->
{% extends 'app/article/base.html' %}

{% block title %}記事一覧{% endblock %}

{% block content %}
<div class="container mt-5">
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="mb-0">記事一覧</h1>
    <a href="{% url 'app:article_create' %}" class="btn btn-success">新規作成</a>
  </div>

  {% if articles %}
    <div class="list-group">
      {% for article in articles %}
        <a href="{% url 'app:article_detail' article.pk %}" class="list-group-item list-group-item-action">
          <div class="d-flex w-100 justify-content-between">
            <h5 class="mb-1">{{ article.title }}</h5>
            <small class="text-muted">{{ article.created_at|date:"Y/m/d H:i" }}</small>
          </div>
          <p class="mb-1">{{ article.content|truncatewords:30 }}</p>
          <small class="text-muted">投稿者: {{ article.user.username }}</small>
        </a>
      {% endfor %}
    </div>
  {% else %}
    <div class="alert alert-info" role="alert">
      記事がまだありません。
    </div>
  {% endif %}
</div>
{% endblock %}
```

CSSフレームワークの採用は問わない(プロジェクトごとに選定する)。上記例のBootstrapクラスはあくまで一例。

## Template Directory Rules

テンプレートが増えても1つのディレクトリに大量にファイルが並んで名前が衝突しないよう、Railsのようにモデルごとにディレクトリを切り、決められたファイル名で管理する。

- `index.html`: 一覧
- `show.html`: 詳細
- `new.html`: 新規作成フォーム
- `edit.html`: 編集フォーム

### Example

```
templates/app/task/index.html
templates/app/task/show.html
templates/app/task/new.html
templates/app/task/edit.html
```

## View Naming Rules

ビューは関数ベースビュー(FBV)で実装する。関数名・テンプレートファイル名・URL名の3つの対応が一目でわかるよう、以下のルールで揃える。

- **関数名**: テンプレートファイル名(上記Template Directory Rulesの`index`/`show`/`new`/`edit`)と同じ名前にする。削除確認ページを伴う場合は`delete`とする。
- **URL名**: `<モデル名>_<関数名>` とする(例: `task_index`, `task_show`, `task_new`, `task_edit`, `task_delete`)。同一Djangoアプリ内で複数モデルのURL名が衝突しないようにするため。
- **関数の配置**: `app/views/<model>.py` に関数として定義する。複数モデルの関数名(`index`/`show`等)が衝突するため、`app/views/__init__.py` では個々の関数をフラットに再エクスポートせず、モジュール単位でインポートする。`urls.py`側は `views.<model>.<関数名>` の形で参照する。

### Example

```python
# app/views/__init__.py
from . import home
from . import task

__all__ = ['home', 'task']
```

```python
# app/views/task.py
def index(request):
    ...

def show(request, pk):
    ...
```

```python
# app/urls.py
from . import views

urlpatterns = [
    path('tasks/', views.task.index, name='task_index'),
    path('tasks/<int:pk>/', views.task.show, name='task_show'),
    path('tasks/new/', views.task.new, name='task_new'),
    path('tasks/<int:pk>/edit/', views.task.edit, name='task_edit'),
    path('tasks/<int:pk>/delete/', views.task.delete, name='task_delete'),
]
```

## View Method-Branch Rules

CBVを使わずFBVを選んでいるのは、Railsのコントローラーのように「1つの関数の中で自分がすべて制御している」明示性を保つため。ただし`request.method`でGET/POSTを分岐する関数が肥大化しやすいので、以下のルールで整理する。

- **分岐関数は振り分けだけにする**: `new`/`edit`のようにGET/POSTで処理が変わる関数は、分岐と委譲だけを行う薄い実装にする。実際の処理はprivateヘルパー関数(`_`始まり)に切り出す。
- **ヘルパー名は処理内容で付ける**: `_edit_get`/`_edit_post`のようにHTTPメソッド名をそのまま使う命名は避ける。中身を見なくても分岐関数を読むだけで何をしているか分かるよう、`_display_edit_form`/`_update_task`のように行う処理そのもので名付ける。
- **ファイル内の並び順**: モデルの公開アクション(`index`/`show`/`new`/`edit`/`delete`など)をファイル上部にまとめて書き、ファイル全体を見ればそのビューが持つアクション一覧が把握できるようにする。その下に区切りコメントを置き、privateヘルパーをまとめて配置する。

### Example

```python
# app/views/task.py

# タスク編集
def edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        return _update_task(request, task)
    return _display_edit_form(request, task)


# (他の公開アクションが続く)


# ============================================================
# ここから先はprivateヘルパー
# ============================================================


# 編集フォームを表示する
def _display_edit_form(request, task):
    form = TaskForm(instance=task)
    return _render_edit_form(request, task, form)


# タスクの更新処理を行う
def _update_task(request, task):
    form = TaskForm(request.POST, instance=task)
    if form.is_valid():
        form.save()
        messages.success(request, 'タスクを更新しました。')
        return redirect('app:task_show', pk=task.pk)
    return _render_edit_form(request, task, form)


# タスク編集フォームのレンダリング
def _render_edit_form(request, task, form):
    return render(request, 'app/task/edit.html', {'form': form, 'task': task})
```

## Control Flow Rules

`if`のネストを深くしない。条件が成立しない場合や異常系は早期に`return`し、`else`で包まずインデントを1段に保つ(ガード節/早期return)。ビューに限らず、モデル・フォーム・共有モジュールなど全てのPythonコードに適用する。

### Example

```python
# 避ける書き方(ネストが深い)
def _create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            messages.success(request, 'タスクを作成しました。')
            return redirect('app:task_show', pk=task.pk)
        else:
            return _render_new_form(request, form)
    else:
        return _render_new_form(request, TaskForm())

# 良い書き方(早期returnでネストを浅く保つ)
def _create_task(request):
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save()
        messages.success(request, 'タスクを作成しました。')
        return redirect('app:task_show', pk=task.pk)
    return _render_new_form(request, form)
```

## Partial Template Rules

Djangoにはpartialに関するネーミング規則が無いため、Railsに倣い、`{% include %}` で読み込むパーシャルテンプレートのファイル名の先頭には `_` を付ける。

### Example

```
templates/app/task/_form.html
templates/app/task/_task_card.html
```

## Comment Rules

関数・メソッド・クラスの説明にはdocstringを使わず、定義の上に通常のコメントで記述する。

### Example

```python
# タスク管理のためのモデル
class Task(models.Model):

    # 期限を過ぎているかチェック
    def is_overdue(self):
        ...
```

## CSS Rules

CSSは「共通ファイル」と「モデルごとのファイル」に分ける。モデルごとのファイルは、そのモデルのindex/show/new/editページで共通のファイルを1つ使う(ページ単位には分けない)。

自前で書くCSSは(共通・モデル別を問わず)全てDjangoアプリの`app/static/app/`に置く。トップレベルの`static/`は、Bootstrap等サードパーティ製のvendorファイル専用とする(自前のCSSと混在させない)。

### ディレクトリ構成

```
static/
└── vendor/            # サードパーティ製ファイル(Bootstrap等)専用
    └── bootstrap/...
app/static/app/
├── common.css          # 全ページ共通のスタイル(自前CSSはここに置く)
└── task.css            # taskモデル関連ページ(index/show/new/edit)共通のスタイル
```

### 読み込み方法

`layouts/default.html` で `app/common.css` を常に読み込む。モデル別CSSは、`index`/`show`/`new`/`edit`/`delete`の各ページが個別に`{% block extra_css %}`を書くと重複するため、Template Rulesの`app/<model>/base.html`(モデル単位の中間テンプレート)の`extra_css`ブロックにまとめる。`_form.html`のような`{% include %}`用パーシャルとは役割が違うため、`base.html`に`_`は付けない。

```html
<!-- layouts/default.html -->
<link rel="stylesheet" href="{% static 'vendor/bootstrap/css/bootstrap.min.css' %}">
<link rel="stylesheet" href="{% static 'app/common.css' %}">
{% block extra_css %}{% endblock %}
```

## Common Module Rules

共有モジュールは、共有する範囲によって置き場所を分ける。Pythonモジュールに限らず、テンプレートも同じ考え方で置き場所を分ける。

- **1つのアプリ内で共有**: `app/lib/` に置く(Railsの`lib/`相当。models/views/forms等どこにも属さない、app固有の共有コードの置き場)。`urls.py`/`apps.py`/`admin.py`のような、Djangoの規約でアプリ直下に置くと決まっているファイルはそのままアプリ直下に残し、開発者が追加した「app内で共有するロジック」だけを`app/lib/`にまとめる。役割ごとにファイルを分ける: 認証(ログイン等、誰であるかの検証)は`app/lib/auth.py`、権限(何ができるかの判定)は`app/lib/permissions.py`、複数モデルで使い回すバリデータは`app/lib/validators.py`、汎用ユーティリティは`app/lib/utils.py`(増えてきたら`app/lib/utils/`ディレクトリ化し、関心事ごとにファイル分割する。例: `utils/date.py`)。ナビゲーションバー・フラッシュメッセージ表示のような特定のモデルに属さないパーシャルテンプレート(`app/templates/common/`)も同じ考え方で、このアプリ専用の置き場に置く。「複数アプリ間で共有」に見えても、実際に共有先の別アプリが存在しない限りは、このアプリ内に留める。
  - 例外: `app/management/commands/`(Djangoがこの場所を前提にコマンドを自動検出する)と`app/seeds/`(Seed Data Rules参照、モデルごとのデータ生成スクリプト群という別カテゴリ)は`app/lib/`に含めない。
- **複数アプリ間で共有**: `app/` と同列に共有専用アプリ `common/` を作り、`INSTALLED_APPS` に登録して置く。これは実際に2つ以上のアプリから使われるようになった時点で行う。

```
config/
app/
├── urls.py                  # Djangoの規約でアプリ直下に置くファイル(そのまま)
├── apps.py
├── admin.py
├── lib/                     # app内で共有する、開発者が追加したロジック
│   ├── __init__.py
│   ├── auth.py              # 認証ロジック(ログイン等、誰であるかの検証)
│   ├── permissions.py       # 権限判定ロジック(何ができるかの判定)
│   ├── validators.py        # 複数モデルで使い回すカスタムバリデータ
│   └── utils.py             # 汎用ユーティリティ
└── templates/
    └── common/              # appアプリ内で共有するパーシャルテンプレート
        ├── _navbar.html
        └── _messages.html
common/                    # 複数アプリ間で共有するモジュール(実際に複数アプリができてから使う)
├── __init__.py
├── utils.py
└── mixins.py
```

## Validator Rules

モデルの複数フィールド・複数モデルで使い回したいカスタムバリデーションは、モデルファイルに直接書かず `app/lib/validators.py` に置く(増えてきたら `app/lib/utils/` と同様に `app/lib/validators/` ディレクトリ化する)。

- **単純な条件で使い回さない場合**: ただの関数で書く。値を1つ受け取り、不正なら`django.core.exceptions.ValidationError`を送出するだけでよい。
- **パラメータ化して複数箇所で使い回したい場合**: `__call__(self, value)` を実装したクラスにする(Rails の `ActiveModel::EachValidator` に相当)。インスタンス化時の引数で条件をカスタマイズできる。
- **クラスにする場合は必ず `@deconstructible` を付ける**: モデルフィールドの `validators=[...]` に渡すインスタンスは、マイグレーションファイルにシリアライズ(Pythonコードとして書き出し)できる必要がある。`django.utils.deconstruct.deconstructible` を付けないと `makemigrations` が `ValueError: Cannot serialize` で失敗する。

### Example

```python
# app/lib/validators.py
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


# 指定した文字を含むことを要求するバリデータ
@deconstructible
class ContainsCharacterValidator:
    def __init__(self, character, message=None):
        self.character = character
        self.message = message or f'{character}を含めてください。'

    def __call__(self, value):
        if self.character not in value:
            raise ValidationError(self.message)
```

```python
# app/models/task.py
from app.lib.validators import ContainsCharacterValidator

description = models.TextField(
    blank=True,
    validators=[ContainsCharacterValidator('#', message='説明には関連するIssue番号(例: #123)を含めてください。')],
)
```

## Mixin/Base Naming Rules

多重継承に使うクラスは、役割によって名前の末尾を使い分ける。

- **`XxxBase`**: そのクラスが「is-a」の主軸(本体)であることを示す。抽象基底クラスとして、そこから具体的なクラスが1本の系譜として派生していくイメージ。
- **`XxxMixin`**: 単体では完結しない、部品としての機能追加であることを示す。他のクラスと組み合わせて使う前提で、単体でインスタンス化されることは想定しない。

### Example

```python
# 「is-a」の主軸となる抽象モデル
class TaskBase(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)


# 部品として機能を追加するだけのmixin
class TimestampMixin:
    updated_at = models.DateTimeField(auto_now=True)


class Task(TaskBase, TimestampMixin):
    ...
```

## Migration Rules

マイグレーションファイルは、まだどこにも適用されていない間(自分のローカルDB以外に、共有DB・他の開発者・CI等で`migrate`が実行されていない間)は、自由に編集・統合してよい。逆に、一度でも共有された環境に適用されたマイグレーションは書き換えない(適用先の`django_migrations`テーブルとの整合性が壊れるため)。

- 同一ブランチ内(mainに未マージ)で同じモデルへの変更を続ける場合、新しいマイグレーションファイルを都度追加せず、まだ未適用のマイグレーションファイルを直接編集して1つにまとめる。
- ブランチがmainにマージされた後にさらに変更が必要になった場合は、既存のマイグレーションを書き換えず、新しいマイグレーションファイルを追加する。
- マイグレーションを直接編集した後は、`python manage.py makemigrations --check --dry-run`でモデル定義とのズレがないことを確認する。

## Seed Data Rules

開発・動作確認用のシードデータ生成ロジックは、models/views/forms等と同様にモデルごとにファイル分割し、`app/seeds/` ディレクトリに置く。`app/management/commands/seed_database.py` は各`app/seeds/*.py`の`create()`を呼び出すだけの薄い実装にする。

- **モデルを追加したら、そのモデルにシードデータが必要か検討する**: 画面確認やログインに使うようなモデル(例: Employee)は追加時にシードデータも作成する。参照専用のマスタ的なモデルなど不要な場合はスキップしてよい。
- **配置場所**: `app/seeds/<model>.py` に `create()` 関数を定義する。他のシードから参照される可能性がある場合は、作成したオブジェクトを返す。
- **呼び出し順序**: `seed_database.py`の`handle()`で、モデルの依存関係(外部キー等)を考慮した順序で各`create()`を呼び出す。
- **シードデータは最小限にする**: ログイン確認用など個別に参照したいレコードは社員番号などを固定して少数だけ作る。一覧・ページネーションなど「複数件あること」の確認が必要な場合のみ、`Faker`(`Faker('ja_JP')`)でダミーデータを追加生成する。用途がないのに機械的に大量のダミーデータを生成しない。
- **パスワードは固定の簡易値でよい**: `password123` のような開発用の固定パスワードを使う(本番相当のランダム生成は不要)。

### Example

```
app/seeds/
├── __init__.py       # from . import employee のようにモジュール単位でインポート
└── employee.py        # def create(): ...
```

```python
# app/seeds/employee.py
from django.contrib.auth.models import User
from faker import Faker
from app.models import Employee

fake = Faker('ja_JP')
DUMMY_EMPLOYEE_COUNT = 10


# 社員のシードデータを作成する
def create():
    # ログイン確認用に社員番号を固定した社員
    _create_employee('E0001', '太郎', '山田', is_staff=True)
    _create_employee('E0002', '花子', '鈴木')

    # 一覧・ページネーション確認用のダミー社員
    for i in range(1, DUMMY_EMPLOYEE_COUNT + 1):
        _create_employee(f'E9{i:03d}', fake.first_name(), fake.last_name())


def _create_employee(employee_number, first_name, last_name, is_staff=False):
    user = User.objects.create_user(
        username=employee_number, password='password123',
        first_name=first_name, last_name=last_name, is_staff=is_staff,
    )
    return Employee.objects.create(user=user, employee_number=employee_number)
```

```python
# app/management/commands/seed_database.py
from django.core.management.base import BaseCommand
from app import seeds


class Command(BaseCommand):
    help = '動作確認用のシードデータを投入する'

    def handle(self, *_args, **_options):
        seeds.employee.create()
```

## Model Validation Rules

Djangoは`save()`時に自動でバリデーション(フィールドの`validators`、`clean()`)を実行しない(ModelFormの`is_valid()`経由でのみ実行される)。フォームを経由しないシェル・管理コマンド・データ移行などでもバリデーションが素通りしないよう、バリデーションロジックを持つモデルは`save()`をオーバーライドして`full_clean()`を必ず呼ぶ。

- フィールドの`validators=[...]`や`clean()`に検証ロジックを書く。複数フィールドにまたがるユニーク制約(重複禁止)も、DBの`UniqueConstraint`ではなく`clean()`で`django.core.exceptions.ValidationError`を送出する形にする
- `save()`をオーバーライドし、`super().save()`を呼ぶ前に`self.full_clean()`を呼ぶ(Railsのように、`save()`のたびに必ずバリデーションが走るようにする)
- 理由: DB制約の追加・削除・変更にはマイグレーションが必要で、コードを読むだけでは制約の存在に気づきにくいため。また`save()`でバリデーションを効かせないと、フォームを経由しない直接作成(シェル操作等)でルール違反のデータが作られてしまう
- ModelForm経由の保存では`is_valid()`(内部で`full_clean()`)とこの`save()`の両方でバリデーションが走るが、二重に検証されるだけで害はない

(注: この方針はまだ確信が持てていない試験的なルールで、今後変更する可能性がある)

### Example

```python
from django.core.exceptions import ValidationError
from django.db import models


class Department(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    # 同じ会社内で部門名が重複しないようにする
    def clean(self):
        duplicates = Department.objects.filter(company=self.company, name=self.name).exclude(pk=self.pk)
        if duplicates.exists():
            raise ValidationError('この会社には同じ名前の部門が既に存在します。')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
```
