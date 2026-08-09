# アクセス制御 設計ドキュメント

## 背景・目的

`docs/superpowers/specs/2026-08-04-employee-permission-model-design.md`(以下「ロール決定ロジック設計」)で、ログインした社員にどの`ManagementGroup`が適用されるかを決定する`get_applicable_management_groups(user)`を実装した(PR #9)。

同ドキュメントは「アクセス制御(適用された`ManagementGroup`が、具体的にどの範囲のCompany/Department/Employeeを閲覧・操作できるか)」を意図的にスコープ外とし、`app/views/company.py`/`department.py`/`employee.py`には以下12件のTODOが残っている。

- `index`: 閲覧範囲を絞り込む
- `new`: 作成可否をチェックする
- `edit`: 編集可否をチェックする
- `delete`: 削除可否をチェックする

(3モデル × 4TODO = 12件)

本設計は、このアクセス制御を対象とする。

## スコープ

- 対象: `ManagementGroup`に「権限セット」を紐づけ、Company/Department/Employeeの各ビューで閲覧・作成・編集・削除・実行の可否を判定する仕組み
- 対象外:
  - フィールド単位(カラム)権限の実際のテンプレート・フォームへの組み込み(判定APIは用意するが、現状の12件のTODOはいずれもレコード単位の制御であり、フィールド単位を要求するものが無いため)
  - `execute`アクションを実際に使う具体的な業務操作(現時点でCompany/Department/EmployeeのCRUD画面に対応する操作が無い。将来の拡張に備えて型として用意するのみ)
  - `own`(自分自身のレコードのみ)に相当する概念は、このアプリには存在しないため扱わない

## 権限モデルの全体像

権限は「どのManagementGroupに所属しているか」(ロール決定ロジック、実装済み)と「そのManagementGroupにどんな権限セットが割り当てられているか」(本設計)の2段階で決まる。

```
User -- (members) --> ManagementGroup -- (permission_set_id) --> 権限セット(ハードコード)
                            |
                            +-- is_admin=True の場合: 権限セットを介さず常に全権限
```

- 1人のユーザーは複数の`ManagementGroup`に同時に所属できる(既存仕様)
- 複数の`ManagementGroup`が同時に適用される場合、それぞれの権限セットの判定結果を**deny優先**でマージする(後述)

## ディレクトリ構成

`app/lib/permissions.py`を`app/permissions/`(トップレベルディレクトリ)に昇格する。

```
app/permissions/
├── __init__.py
├── roles.py            # 既存のis_admin/can_edit_task/can_delete_task/get_applicable_management_groups(app/lib/permissions.pyから移動)
├── access.py            # 新規: can_view/can_create/can_edit/can_delete/can_execute(レコード・カラム権限判定)
└── rule_sets/
    ├── __init__.py       # 各ルールセットファイルをimportしREGISTRY(番号→ルールセット)を構築する
    ├── 01_department_viewer_all.py
    └── 02_company_scoped_department_manager.py
```

`app/tests/unit/lib/permissions_test.py`は`app/tests/unit/permissions/roles_test.py`・`access_test.py`・`rule_sets_test.py`に分割移動する(既存規約「`tests/unit/`はソース側ディレクトリに対応」に従う)。

### `.claude/instructions.md`の更新

Common Module Rulesに、以下の内容を追記する(雛形として再利用可能な一般規約として)。

> `app/lib/`配下のモジュールが肥大化し、関心事が独立したサブシステムと呼べる規模になった場合、`app/permissions/`のようにmodels/views/forms等と同列のトップレベルディレクトリへ昇格してよい。昇格後は他のトップレベルディレクトリと同じ構成規則(ディレクトリ化・`__init__.py`配置・テストディレクトリの対応)に従う。

## データモデル変更

### `ManagementGroup`に`permission_set_id`を追加

```python
permission_set_id = models.IntegerField(null=True, blank=True, verbose_name='権限セット番号')
```

- `is_admin=True`の場合: `permission_set_id`は`NULL`(常に全権限がハードコードされているため不要)
- `is_admin=False`の場合: `permission_set_id`必須。`app.permissions.rule_sets.REGISTRY`に存在するIDでなければならない
- 上記の整合性は既存の`clean()`と同様の場所で検証する
- DBに権限セットのテーブルは作らない(後述の理由によりコードで管理するため)。`permission_set_id`はあくまで`REGISTRY`のキーを指す整数

## 権限セットをハードコードする理由・ファイル形式

### なぜDBテーブルではなくコードで管理するか

権限セットは実運用で2つ以上存在し、今後も追加されていく想定。DBの管理画面から動的に編集させるのではなく、Pythonファイルとして1セット1ファイルで管理し、Gitでレビュー・履歴管理できるようにする(既存の`app/seeds/`が「モデルごとにファイルを分け、`__init__.py`で明示的にimportする」パターンを踏襲)。

**起動時の読み込み・キャッシュ**: Pythonのimportは、あるモジュールを最初にimportした時点で1度だけ実行され、以降は`sys.modules`にキャッシュされた結果が再利用される(2回目以降のimportはファイルを再読み込みしない)。`app/permissions/rule_sets/__init__.py`はDjangoプロセスの起動時(`app.permissions.access`等、これをimportするモジュールが最初にロードされるタイミング)に1度だけ実行されて`REGISTRY`を構築し、以降はプロセスが生きている間メモリ上の`REGISTRY`がそのまま使い回される。この仕組みにより、キャッシュ用の独自コード(Djangoの`AppConfig.ready()`や`cache`フレームワーク等)を別途書く必要はない。

### 設計の決定経緯(実装時に`app/permissions/rule_sets/__init__.py`の先頭コメントとして残すこと)

**ルールの並べ方**について、以下の2案を比較検討した。

1. **Claude Codeのsettings.json方式**(`allow`/`deny`のパターン文字列配列。例: `"Employee(department):view"`)
   - 短所: モデル・スコープ・アクション・フィールドを1つの文字列に詰め込むため、後から表の列に分解するにはパターンのパースが必要になる
2. **1行=1権限のフラットな辞書リスト**(採用)
   - 長所: `model`/`level`/`action`/`scope`/`effect`が最初から列として分離されているため、パース不要でそのまま表になる。今回の目的である「AIが表にまとめてConfluenceに記述する」運用に直結する

**スコープの表現方法**についても、以下の案を検討した。

1. `own`/`department`/`department_tree`/`company`/`all`のような固定の列挙型 → 実際の業務要件(例:「部門は原則アクセス不可だが特定の管理グループは全部門にアクセス可能」「会社情報は全員閲覧可能だが特定の会社の部門情報にのみアクセス可能な管理グループがある」)には合わず、部門階層を辿る計算(`department_tree`)のような「決まった計算式」では表現しきれないケースが多いことが分かった
2. **フィールドパス→期待値の辞書によるフィルタ**(採用。詳細は後述の「スコープの表現方法」節)

**採用理由**: 権限セットのドキュメント化(AIが表に変換してConfluenceに記述する運用)を優先して1を、業務要件の実例に基づき固定列挙型では対応できないと判断して2を、それぞれ採用した。この経緯は`app/permissions/rule_sets/__init__.py`の先頭にコメントとして残す。

### ファイル形式

```python
# app/permissions/rule_sets/01_department_viewer_all.py
# 「部門情報は原則アクセス不可だが、全部門を閲覧できる」権限セットの例

ID = 1
NAME = '全部門閲覧者'
DESCRIPTION = '部門情報を、会社・部門を問わず全件閲覧できる権限セット。編集・削除・作成は不可。'

RULES = [
    {'model': 'Department', 'level': 'record', 'action': 'view', 'scope': {}, 'effect': 'allow'},
    {'model': 'Department', 'level': 'record', 'action': 'create', 'scope': {}, 'effect': 'deny'},
    {'model': 'Department', 'level': 'record', 'action': 'edit', 'scope': {}, 'effect': 'deny'},
    {'model': 'Department', 'level': 'record', 'action': 'delete', 'scope': {}, 'effect': 'deny'},
    {'model': 'Department', 'level': 'record', 'action': 'execute', 'scope': {}, 'effect': 'deny'},
]
```

```python
# app/permissions/rule_sets/02_company_scoped_department_manager.py
# 「会社情報は全員閲覧可能、特定の会社の部門情報のみ閲覧・編集できる」権限セットの例

ID = 2
NAME = 'サンプル株式会社 部門管理者'
DESCRIPTION = 'サンプル株式会社に属する部門情報のみ閲覧・編集できる権限セット。会社情報は全社共通で閲覧のみ許可する。'

RULES = [
    {'model': 'Company', 'level': 'record', 'action': 'view', 'scope': {}, 'effect': 'allow'},

    {'model': 'Department', 'level': 'record', 'action': 'view',
     'scope': {'company.name': 'サンプル株式会社'}, 'effect': 'allow'},
    {'model': 'Department', 'level': 'record', 'action': 'edit',
     'scope': {'company.name': 'サンプル株式会社'}, 'effect': 'allow'},
    {'model': 'Department', 'level': 'record', 'action': 'create',
     'scope': {'company.name': 'サンプル株式会社'}, 'effect': 'allow'},
    {'model': 'Department', 'level': 'record', 'action': 'delete',
     'scope': {'company.name': 'サンプル株式会社'}, 'effect': 'deny'},

    # --- カラム権限(record権限がallowの範囲でのみ意味を持つ。今回はテンプレート・フォームへの組み込みは行わない) ---
    {'model': 'Department', 'level': 'field', 'field': 'company', 'action': 'edit', 'effect': 'deny',
     'note': '所属会社の変更(会社をまたぐ移動)はこの権限セットからは行えない'},
]
```

- `level='record'`の行に`field`キーは無し、`level='field'`の行に`scope`キーは無し(意味を持たないため)
- `scope`は`{}`(絞り込み無し=全件一致)か、`{'フィールドパス': 期待値}`の辞書。`'company.name'`のように`.`区切りで関連先フィールドを辿れる
- `effect`は`'allow'`/`'deny'`の2種類(AWS IAM・Kubernetes・Claude Code設定ファイル等、現代のアクセス制御で広く使われる語を採用。`permit`は使わない)
- `note`は任意の人間向け説明(表のドキュメント化で「備考」列に使う)
- ルールに存在しない組み合わせは常にデフォルト`deny`

### `app/permissions/rule_sets/__init__.py`

```python
# 設計の決定経緯: docs/superpowers/specs/2026-08-08-access-control-design.md 参照
# - ルール形式: Claude Code settings.json風のallow/denyパターン文字列ではなく、AIが表に変換して
#   Confluenceに転記しやすいよう「1行=1権限」のフラットな辞書リスト形式を採用した
# - スコープ形式: 部門階層等の固定列挙型ではなく、実際の業務要件に合わせて任意のフィールドパスで
#   絞り込める汎用フィルタ辞書を採用した

from . import department_viewer_all
from . import company_scoped_department_manager

REGISTRY = {
    department_viewer_all.ID: department_viewer_all,
    company_scoped_department_manager.ID: company_scoped_department_manager,
}
```

新しい権限セットを追加する時は、`rule_sets/`にファイルを1つ追加し、`__init__.py`に1行importとREGISTRYへの登録を足すだけでよい。

## スコープの表現方法

`scope`はDjangoの`QuerySet.filter(**kwargs)`のような「フィールドパス→期待値」の辞書だが、実際の絞り込みはDBに問い合わせず、Python側で対象の属性を直接辿って比較する(`index`一覧のフィルタリング・`show`/`edit`/`delete`の既存レコードチェック・`create`のフォーム入力値チェックのすべてで同じ評価関数を使い回すため)。

```python
# app/permissions/access.py

# scopeの各条件がtargetに一致するかを判定する
def _matches(target, scope):
    for path, expected in scope.items():
        actual = _resolve_path(target, path)
        if isinstance(expected, (list, tuple, set)):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True


# 'company.name'のような'.'区切りのパスをtargetの属性から辿って値を取得する
def _resolve_path(target, path):
    value = target
    for attr in path.split('.'):
        value = getattr(value, attr)
    return value
```

- `path`が`target`に存在しない属性を指す場合(ルールファイルのフィールド名の誤り等)は`AttributeError`をそのまま送出する(サイレントに`deny`扱いにせず、設定ミスとして検知できるようにする)。`rule_sets_test.py`でルールセットごとに代表的なインスタンスを使い評価が例外にならないことを検証する

## 権限判定API

```python
# app/permissions/access.py
def can_view(user, model_name, instance, field=None): ...
def can_create(user, model_name, candidate): ...   # candidateはフォームのcleaned_dataから組み立てた未保存インスタンス
def can_edit(user, model_name, instance, field=None): ...
def can_delete(user, model_name, instance): ...
def can_execute(user, model_name, instance): ...
```

### `create`の判定

`create`時点では対象レコードがまだDBに存在しないため、フォームの`cleaned_data`から`Model(**cleaned_data)`(保存はしない)を組み立て、`instance`と同じように`_matches()`にかける。

### 複数グループ判定のマージロジック(3状態)

ユーザーに適用される`ManagementGroup`(`get_applicable_management_groups`で取得)ごとに、対象(既存レコード、または`create`時は未保存の候補インスタンス)に対する判定を求める。各グループの判定は以下の3状態のいずれかになる。

1. **棄権**: グループの`scope`が対象に一致しない(そのグループは何も主張しない)
2. **`allow`**: `scope`が一致し、該当するルールの`effect`が`allow`
3. **`deny`**: `scope`が一致し、該当するルールの`effect`が`deny`、またはそもそも該当するルールが無い(デフォルト拒否)

最終判定は、棄権を無視した上で「1つでも`deny`があれば`deny`、それ以外に`allow`が1つでもあれば`allow`、誰も判定しなければ`deny`」とする(deny優先)。

*棄権を`deny`と同列に扱うと、対象外のグループが存在するだけで他グループの`allow`を打ち消してしまうため、明示的に区別する。*

```python
def _check(user, model_name, action, instance=None, field=None):
    decisions = [
        _decide(group, model_name, action, instance, field)
        for group in get_applicable_management_groups(user)
    ]
    decisions = [d for d in decisions if d is not None]  # 棄権を除外
    if 'deny' in decisions:
        return False
    return 'allow' in decisions


def _decide(group, model_name, action, instance, field):
    if group.is_admin:
        return 'allow'
    rule_set = rule_sets.REGISTRY[group.permission_set_id]
    rule = _find_rule(rule_set, model_name, action, field)
    if rule is None:
        return 'deny'
    if not _matches(instance, rule['scope']):
        return None  # 棄権
    return rule['effect']
```

## ビューへの組み込み方針

- **`index`(一覧)**: 全件取得 → Pythonの`can_view`でフィルタ → `Paginator`にフィルタ後のリストを渡す(`Paginator`はクエリセットだけでなくリストにも使えるため)。今回のデータ規模ではSQL側での絞り込みは行わず、シンプルさを優先する
- **`show`/`edit`/`delete`**: `get_object_or_404`の後に`can_view`/`can_edit`/`can_delete`をチェックし、不許可なら403(`HttpResponseForbidden`)を返す。既存の`management_group`ビューのテストパターン(403返却)に合わせる
- **`new`(作成)**:
  - GET: 適用グループのいずれかが対象モデルに対して`create`の`allow`を持てば(具体的な入力値はまだ無いため広めに)フォームを表示する
  - POST: `form.cleaned_data`から未保存インスタンスを組み立て、`can_create(user, model_name, candidate)`で判定する
- **カラム権限(表示/編集)**: `can_view`/`can_edit`のフィールド版APIは`access.py`に実装するが、テンプレート・フォームへの組み込みは今回のスコープ外(元の12件のTODOはいずれもレコード単位のため)

## テスト方針

- `app/tests/unit/permissions/roles_test.py`(`app/tests/unit/lib/permissions_test.py`から移動、内容はそのまま)
- `app/tests/unit/permissions/access_test.py`(新規): `can_view`/`can_create`/`can_edit`/`can_delete`/`can_execute`の判定ロジック。スコープ一致・棄権・deny優先マージ・`is_admin`のハードコード動作を検証
- `app/tests/unit/permissions/rule_sets_test.py`(新規): `REGISTRY`内の全ルールセットが定義形式(必須キーの組み合わせ)を満たしていること、代表的なインスタンスに対して`_matches()`が例外なく評価できることを検証する(ファイルを増やす運用のため、壊れたルールセットを早期検知する安全網)
- `app/tests/unit/models/management_group_test.py`: `permission_set_id`追加に伴うテスト更新
- `app/tests/unit/views/company_test.py`/`department_test.py`/`employee_test.py`: 既存テストは`auth_client`(どの`ManagementGroup`にも属さない一般ユーザー)で作成・編集・削除が成功する前提になっているため、`management_group_test.py`で確立したパターン(403確認 + `admin_client`や権限セットを持つユーザーでの成功確認)に合わせて全面的に書き換える

## エッジケース・データ整合性

- **`permission_set_id`が`REGISTRY`に存在しない値**: `ManagementGroup.clean()`でエラーにする
- **`is_admin=True`かつ`permission_set_id`が設定されている**: エラーにする(`department`と同様の整合性ルール)
- **ルールセットファイルの構造不正**(必須キー欠落等): `rule_sets_test.py`で検知する
- **`scope`のフィールドパスが対象に存在しない**(ルールファイルの誤り): `_resolve_path`が`AttributeError`を送出し、サイレントに`deny`にはしない

## 今後の課題(スコープ外)

- カラム権限(フィールド単位のview/edit)を実際にテンプレート・フォームへ組み込む
- `execute`アクションを使う具体的な業務操作の実装
