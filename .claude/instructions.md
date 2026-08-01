# Django Development Guidelines

## File Structure Rules

models、forms、views、tests、templatesはディレクトリ化し、機能ごとにファイル分割してください。

### Examples
- models/todo.py
- views/todo.py
- tests/unit/todo_test.py
- tests/e2e/todo_test.py

各ディレクトリに__init__.pyを配置すること。

## Layout Rules

もっとも低レイヤーの共通テンプレート(全ページの土台となるレイアウト)は `templates/layouts/` ディレクトリに置く。既定のレイアウトファイル名は `default.html` とする。将来的に別のレイアウトが必要になった場合は `layouts/admin.html` のように用途名を付けたファイルを追加する。

### Example

```
templates/layouts/default.html
```

## Template Rules

`layouts/default.html` のような基底テンプレートを作成し、各ページのテンプレートは `{% extends %}` で継承すること。各ページ側は `{% block %}` の中身だけを記述する最小限の内容にする。

### Example

```html
{% extends 'layouts/default.html' %}

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

### ディレクトリ構成

```
static/
├── common.css        # 全ページ共通のスタイル
└── app/
    └── task.css       # taskモデル関連ページ(index/show/new/edit)共通のスタイル
```

### 読み込み方法

`layouts/default.html` で `common.css` を常に読み込み、各モデルのテンプレート側で `{% block extra_css %}` を使ってモデル別CSSを読み込む。

```html
<!-- layouts/default.html -->
<link rel="stylesheet" href="{% static 'common.css' %}">
{% block extra_css %}{% endblock %}

<!-- app/task/index.html -->
{% block extra_css %}
<link rel="stylesheet" href="{% static 'app/task.css' %}">
{% endblock %}
```

## Common Module Rules

共有モジュールは、共有する範囲によって置き場所を分ける。

- **1つのアプリ内で共有**: `app/utils.py` に置く。増えてきたら `app/utils/` ディレクトリ化し、関心事ごとにファイル分割する(例: `utils/date.py`)。
- **複数アプリ間で共有**: `app/` と同列に共有専用アプリ `common/` を作り、`INSTALLED_APPS` に登録して置く。

```
config/
app/
common/          # 複数アプリ間で共有するモジュール
├── __init__.py
├── auth.py
├── utils.py
└── mixins.py
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
