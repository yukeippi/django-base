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
- services/todo.py
- tests/unit/models/todo_test.py
- tests/unit/forms/todo_test.py
- tests/unit/views/todo_test.py
- tests/unit/services/todo_test.py
- tests/e2e/todo_test.py

各ディレクトリに__init__.pyを配置すること。

`tests/unit/`配下は、ソース側の`models/`, `forms/`, `views/`, `services/`, `lib/`と対応するレイヤーごとのディレクトリにさらに分割する(Railsの`test/models/`, `test/controllers/`に相当)。`app/lib/`(`auth.py`/`permissions.py`/`validators.py`等、app内で共有するロジック。詳細はCommon Module Rulesを参照)のテストも同様に`tests/unit/lib/`に置く(例: `tests/unit/lib/auth_test.py`)。`tests/e2e/`はページ単位のテストのため、このレイヤー分割は行わない。

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
    if not form.is_valid():
        return _render_edit_form(request, task, form)
    services.task.update(form=form)
    messages.success(request, 'タスクを更新しました。')
    return redirect('app:task_show', pk=task.pk)


# タスク編集フォームのレンダリング
def _render_edit_form(request, task, form):
    return render(request, 'app/task/edit.html', {'form': form, 'task': task})
```

privateヘルパーは、フォームの束縛・serviceの呼び出し・messages・リダイレクトのみを行う。モデルへの書き込みはヘルパー内に書かず、必ず`app/services/`の関数を呼ぶ(Service Rules参照)。

更新系のPOSTは、成功時に必ずリダイレクトする(POST-Redirect-GET)。ブラウザの再送信を防ぎ、「GETは表示・POSTは更新」の境界を保つため。

## Control Flow Rules

`if`のネストを深くしない。条件が成立しない場合や異常系は早期に`return`し、`else`で包まずインデントを1段に保つ(ガード節/早期return)。ビューに限らず、モデル・フォーム・共有モジュールなど全てのPythonコードに適用する。

### Example

```python
# 避ける書き方(ネストが深い)
def _create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = services.task.create(form=form)
            messages.success(request, 'タスクを作成しました。')
            return redirect('app:task_show', pk=task.pk)
        else:
            return _render_new_form(request, form)
    else:
        return _render_new_form(request, TaskForm())

# 良い書き方(早期returnでネストを浅く保つ)
def _create_task(request):
    form = TaskForm(request.POST)
    if not form.is_valid():
        return _render_new_form(request, form)
    task = services.task.create(form=form)
    messages.success(request, 'タスクを作成しました。')
    return redirect('app:task_show', pk=task.pk)
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

`app/lib/`は、`models/`/`views/`/`forms/`/`services/`のいずれにも属さない補助的なコードの置き場である。業務ロジック(モデルへの書き込みを伴う処理)は`app/lib/`ではなく`app/services/`に置く(Service Rules参照)。serviceは補助的な共有コードではなく、`models/`/`views/`/`forms/`と同列の層として扱う。

- **1つのアプリ内で共有**: `app/lib/` に置く(Railsの`lib/`相当)。`urls.py`/`apps.py`/`admin.py`のような、Djangoの規約でアプリ直下に置くと決まっているファイルはそのままアプリ直下に残し、開発者が追加した「app内で共有するロジック」だけを`app/lib/`にまとめる。役割ごとにファイルを分ける: 認証(ログイン等、誰であるかの検証)は`app/lib/auth.py`、権限(何ができるかの判定)は`app/lib/permissions.py`、複数モデルで使い回すバリデータは`app/lib/validators.py`、汎用ユーティリティは`app/lib/utils.py`(増えてきたら`app/lib/utils/`ディレクトリ化し、関心事ごとにファイル分割する。例: `utils/date.py`)。ナビゲーションバー・フラッシュメッセージ表示のような特定のモデルに属さないパーシャルテンプレート(`app/templates/common/`)も同じ考え方で、このアプリ専用の置き場に置く。「複数アプリ間で共有」に見えても、実際に共有先の別アプリが存在しない限りは、このアプリ内に留める。
  - 例外: `app/management/commands/`(Djangoがこの場所を前提にコマンドを自動検出する)と`app/seeds/`(Seed Data Rules参照、モデルごとのデータ生成スクリプト群という別カテゴリ)は`app/lib/`に含めない。
  - **`app/lib/`配下のモジュールが肥大化した場合の昇格**: 関心事が独立したサブシステムと呼べる規模になった場合、`app/permissions/`のように`models/`/`views/`/`forms/`/`services/`等と同列のトップレベルディレクトリへ昇格してよい。昇格後は他のトップレベルディレクトリと同じ構成規則(ディレクトリ化・`__init__.py`配置・テストディレクトリの対応)に従う。
- **複数アプリ間で共有**: `app/` と同列に共有専用アプリ `common/` を作り、`INSTALLED_APPS` に登録して置く。これは実際に2つ以上のアプリから使われるようになった時点で行う。

#### 判断に迷った場合

`app/lib/` に置くべきか `app/services/` に置くべきか迷ったら、次で判断する。

- モデルへの書き込みを行う、またはトランザクションを必要とする → `app/services/`
- 値の計算・変換・判定のみで、DBを変更しない → `app/lib/`

```
config/
app/
├── urls.py                  # Djangoの規約でアプリ直下に置くファイル(そのまま)
├── apps.py
├── admin.py
├── models/                  # 永続化・状態判定
├── views/                   # HTTPの入出力
├── forms/                   # 入力検証
├── services/                # 業務ロジック・トランザクション境界
├── lib/                     # 上記のどれにも属さない、app内で共有するコード
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

## Model Table Naming Rules

Djangoのデフォルトのテーブル名(`<applabel>_<モデル名を小文字化しただけの文字列>`)は、複数単語のモデル名だと単語の区切りが分からず読みにくい(例: `ManagementGroup` → `app_managementgroup`)。全モデルで`Meta.db_table`を明示し、アプリ名プレフィックスを付けず、単語間を`_`で区切ったスネークケースのテーブル名にする。

- 単語区切りだけでなくアプリ名プレフィックス(`app_`等)も付けない。テーブル名だけを見て何のデータか分かることを優先する
- モデルを追加・リネームしたら、`Meta.db_table`の設定と対応するマイグレーション(`makemigrations`で生成される`AlterModelTable`)の作成を忘れない

### Example

```python
class ManagementGroup(models.Model):
    class Meta:
        db_table = 'management_group'

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

## Service Rules

モデルへの書き込みは、すべて`app/services/`を経由する。viewから`form.save()`/`Model.objects.create()`/`instance.save()`/`instance.delete()`を直接呼ばない。

処理の複雑さによって置き場所を変えない。単純な作成・更新であっても例外を設けない。複雑さで分岐させると「これはserviceに置くべきか」という判断が毎回発生し、実装者ごと・セッションごとにブレるため。単純な処理のserviceは数行になるが、後から業務ルールが増えたときにviewを触らずに済み、変更のdiffが「機能追加」だけになる。

読み取りは対象外。一覧・詳細取得はviewから直接ORMを呼んでよい。絞り込み条件はQuerySet Rulesに従いカスタムQuerySetに置く。serviceは書き込み専用とする。

### 構成

- `app/services/<model>.py`に関数として定義する。`__init__.py`では`views/`と同様にモジュール単位でインポートし、呼び出し側は`services.<model>.<関数名>`の形で参照する
- 1関数1ユースケースとする。`TaskService`のようなクラスに操作を集約しない。クラスに集約するとモデル単位で肥大化し、分割できなくなる
- 関数名は業務操作名にする(`complete`, `approve`, `cancel`)。単純なCRUDは`create`/`update`/`delete`でよい
- ファイルが肥大化したら、関数の集合であることを活かして`app/services/<model>/`ディレクトリに分割する。`__init__.py`で再エクスポートすれば呼び出し側は変更不要

### 関数の書き方

- 引数はキーワード専用(`*`以降)にする。呼び出し側で各引数の意味が読めるようにするため
- `HttpRequest`を受け取らない。管理コマンド・バッチ・テストから同じ関数を呼べるようにするため。検証済みのフォーム(`Form`インスタンス)は受け取ってよい
- 引数と戻り値に型注釈を付ける
- `@transaction.atomic`はserviceに付ける。viewとmodelには書かない。1つの業務操作 = 1つのトランザクションとする
- serviceは他のserviceパッケージを呼ばない。`services/task.py`から`services/project.py`を呼ばない。トランザクション境界が追跡できなくなるため。同一ファイル内のprivateヘルパー(`_`始まり)への切り出しは可

### 関数内部の並び順

処理は以下の順に書く。この順序により、ガード節が先頭に集まり、外部への通知がDB変更の確定後になる。該当しない段階は省略してよい。

1. **検証** — 業務条件を満たさなければ例外を送出して終了
2. **変更** — モデルの更新・関連レコードの作成
3. **記録** — 履歴・監査ログ
4. **通知** — メール送信・外部システム連携

通知は`transaction.on_commit()`に包む。トランザクション内で直接実行すると、後続処理がロールバックしても通知だけが送信される。

### serviceが持たないもの

- `django.contrib.messages`の呼び出し
- `redirect`/HTTPステータス/テンプレート名
- `get_object_or_404`
- 画面遷移に関する判断

業務条件を満たさない場合は、リダイレクトではなく例外を送出する。viewが受け取って`messages`と画面遷移に変換する。

### modelとの役割分担

serviceが持つのは操作の手順であり、状態の意味ではない。

- 「このオブジェクトが今どういう状態か」の判定はmodelに置く(`task.can_complete()`, `task.is_overdue()`)。テンプレートから`{% if task.can_complete %}`と呼べるのもmodel側にある場合のみ
- 「その状態でこの操作をしてよいか」の判断と、実際の手順はserviceに置く

判定ロジックをserviceに書くとserviceだけが太り、modelが空になる。判定はmodelへ、手順はserviceへ寄せる。

### Example

```python
# app/models/task.py

# タスク管理のためのモデル
class Task(models.Model):
    ...

    # 完了可能な状態かどうか
    def can_complete(self):
        if self.status == Task.Status.COMPLETED:
            return False
        return not self.children.exclude(status=Task.Status.COMPLETED).exists()
```

```python
# app/services/task.py
from django.db import transaction

# タスクを作成する
def create(*, form: TaskForm) -> Task:
    return form.save()

# タスクを完了にする
@transaction.atomic
def complete(*, task: Task, operator: User) -> Task:
    # 1. 検証
    if not task.can_complete():
        raise ValidationError('このタスクは完了できません。')

    # 2. 変更
    task.status = Task.Status.COMPLETED
    task.completed_at = timezone.now()
    task.save()

    # 3. 記録
    TaskHistory.objects.create(task=task, action='completed', operator=operator)

    # 4. 通知
    transaction.on_commit(lambda: send_completion_notice(task))
    return task
```

```python
# app/views/task.py

# タスク完了処理を行う
def _complete_task(request, task):
    try:
        services.task.complete(task=task, operator=request.user)
    except ValidationError as error:
        messages.error(request, error.message)
        return redirect('app:task_show', pk=task.pk)

    messages.success(request, 'タスクを完了しました。')
    return redirect('app:task_show', pk=task.pk)
```

```python
# app/services/__init__.py
from . import task

__all__ = ['task']
```

## QuerySet Rules

繰り返し使う絞り込み条件は、viewやserviceに書かず、カスタムQuerySetのメソッドとして定義する。同じ`filter()`が複数箇所に散ることを防ぎ、条件に業務上の名前を与えるため。

- `app/models/<model>.py`内に、対応するモデルと同じファイルで定義する。全モデル分を1ファイルに集約しない
- モデルには`objects = XxxQuerySet.as_manager()`で紐づける
- QuerySetは読み取り専用とする。状態変更や副作用を持たせない
- 一覧表示で関連を辿る場合の`select_related`/`prefetch_related`もQuerySetメソッドにまとめる

### Example

```python
# app/models/task.py

class TaskQuerySet(models.QuerySet):

    # 未完了のタスクに絞り込む
    def incomplete(self):
        return self.exclude(status=Task.Status.COMPLETED)

    # 期限を過ぎた未完了タスクに絞り込む
    def overdue(self):
        return self.incomplete().filter(due_on__lt=timezone.localdate())

    # 一覧表示で必要な関連をまとめて読み込む
    def with_details(self):
        return self.select_related('assignee').prefetch_related('children')


class Task(models.Model):
    objects = TaskQuerySet.as_manager()
    ...
```
