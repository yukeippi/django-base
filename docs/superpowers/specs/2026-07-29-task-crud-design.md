# タスク管理CRUDの完成 設計ドキュメント

## 背景・目的

`app/models/task.py`の`Task`モデルと、一覧(`TaskListView`)・詳細(`TaskDetailView`)は実装済みだが、新規作成・編集・削除が未実装。まずはこのCRUDを完成させる。認証・権限管理(誰が作成・編集・削除できるか)は本設計のスコープ外とし、別途あらためて設計する。

## スコープ

- 対象: タスクの新規作成・編集・削除機能の追加
- 対象外: ログイン・認証・権限チェック(後続タスク)

## アーキテクチャ

### ビュー方式: 関数ベースビュー(FBV)への統一

既存の`TaskListView`(CBV) / `TaskDetailView`(CBV)を含め、`app/views/task.py`内の全ビューを関数ベースビューに統一する。命名規則の詳細は `.claude/instructions.md` の「View Naming Rules」セクションに追記済み。要点:

- 関数名はテンプレートファイル名と揃える: `index` / `show` / `new` / `edit` / `delete`
- URL名は `<モデル名>_<関数名>` とする: `task_index` / `task_show` / `task_new` / `task_edit` / `task_delete`
- `app/views/__init__.py` はモジュール単位でインポートし(`from . import home, task`)、`urls.py`側は `views.task.show` のように参照する。複数モデルの関数名(`index`/`show`等)が衝突しないようにするため。

### フォーム

`app/forms/task.py` に `TaskForm(ModelForm)` を新規配置する(`app/forms/`ディレクトリを新設、`.claude/instructions.md`のFile Structure Rulesに従う)。

- 編集可能フィールド: `title`, `description`, `status`, `priority`, `assigned_to`, `due_date`
- `created_at` / `updated_at` は自動のため含めない
- モデル側のバリデータ(`MinValueValidator`/`MaxValueValidator`等)はModelForm経由でそのまま適用される

### URL構成

```
tasks/            → task.index   (name: task_index)
tasks/<pk>/        → task.show    (name: task_show)
tasks/new/         → task.new     (name: task_new)
tasks/<pk>/edit/    → task.edit    (name: task_edit)
tasks/<pk>/delete/  → task.delete  (name: task_delete)
api/tasks/          → task.task_api (既存のまま、変更なし)
```

### ビューの振る舞い

- `index`: `Task.objects.all()`をページネーション(`Paginator`、既存の`paginate_by=10`相当)して`index.html`に渡す
- `show`: `get_object_or_404`で取得し`show.html`へ
- `new` / `edit`: GETでフォーム表示。POSTで`TaskForm`にバインドし、valid時は保存して`show`へリダイレクト+messagesでフラッシュメッセージ表示。invalid時はフォーム再表示(エラーメッセージ付き)
- `delete`: GETで確認ページ(`delete.html`)を表示。POSTで削除し`index`へリダイレクト+messagesでフラッシュメッセージ表示

### テンプレート

- `app/templates/app/task/new.html` / `edit.html` を追加し、フォーム本体は `app/templates/app/task/_form.html` に共通化して`{% include %}`する(Partial Template Rulesに従い`_`プレフィックス)
- `app/templates/app/task/delete.html` を追加(削除確認ページ)
- `index.html`に「新規作成」リンクを追加
- `show.html`に「編集」「削除」リンクを追加
- 成功時のフラッシュメッセージ表示のため、`base/base.html`に`django.contrib.messages`の表示ブロックを追加する(現状base.htmlはmessagesを表示していないため)

### スタイル

既存の`app/static/app/task.css`を新規テンプレートでも共通利用する(Model単位で1ファイルというCSS Rulesに従い、新規ファイルは作らない)。

## テスト方針

- ユニットテスト(`app/tests/unit/task_test.py`に追加):
  - `TaskForm`のバリデーション(必須項目、priority範囲外など)
  - 各ビュー(`new`/`edit`/`delete`)の正常系・異常系(Django test clientを使用)
- E2Eテスト(`app/tests/e2e/task_test.py`に追加):
  - 新規作成〜詳細確認〜編集〜削除までの一連のシナリオ(Playwright)

既存のユニット・E2Eテストは、ビュー方式変更(CBV→FBV)およびURL名変更(`task_list`→`task_index`, `task_detail`→`task_show`)による参照箇所を追従修正する。影響箇所:
  - `app/templates/app/task/show.html`(`{% url 'app:task_list' %}`)
  - `app/templates/app/index.html`(`{% url 'app:task_list' %}`)

## 実装後の扱い

本タスク完了後もユーザーの指示により **コミットは行わない**。
