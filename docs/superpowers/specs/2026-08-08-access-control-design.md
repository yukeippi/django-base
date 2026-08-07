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
  - スコープ種別`field_value`(部門階層と無関係な、任意フィールド値による絞り込み。例:「会社区分=1のみアクセス可」)の実装(形式としては受け入れられるように設計するが、今回はルールとして書かない)

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
    ├── 01_department_manager.py
    └── 02_department_viewer.py
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

### ルール形式の決定経緯(実装時にコードコメントとして残すこと)

以下の2案を比較検討した。

1. **Claude Codeのsettings.json方式**(`allow`/`deny`のパターン文字列配列。例: `"Employee(department_tree):view"`)
   - 長所: 1行が短い
   - 短所: モデル・スコープ・アクション・フィールドを1つの文字列に詰め込むため、後から表の列に分解するにはパターンのパースが必要になる。パターンの優先順位(具体的なパターン vs ワイルドカード)判定も別途必要
2. **1行=1権限のフラットな辞書リスト**(採用)
   - 長所: `model`/`level`/`action`/`scope`/`effect`が最初から列として分離されているため、パース不要でそのまま表になる。今回の目的である「AIが表にまとめてConfluenceに記述する」運用に直結する
   - 短所: 1行がやや長い

**採用理由**: 権限セットのドキュメント化(AIが表に変換してConfluenceに記述する運用)を優先し、2番目の形式を採用した。この経緯は`app/permissions/rule_sets/__init__.py`の先頭にコメントとして残す。

### ファイル形式

```python
# app/permissions/rule_sets/01_department_manager.py

ID = 1
NAME = '部門管理者'
DESCRIPTION = '自部門および配下部門(部門ツリー)の社員・部門情報を管理する権限セット。会社情報は閲覧のみ許可する。'

RULES = [
    # --- レコード権限 ---
    {'model': 'Employee', 'level': 'record', 'action': 'view', 'scope': {'type': 'department_tree'}, 'effect': 'permit'},
    {'model': 'Employee', 'level': 'record', 'action': 'create', 'scope': {'type': 'department_tree'}, 'effect': 'permit'},
    {'model': 'Employee', 'level': 'record', 'action': 'edit', 'scope': {'type': 'department_tree'}, 'effect': 'permit'},
    {'model': 'Employee', 'level': 'record', 'action': 'delete', 'scope': {'type': 'department_tree'}, 'effect': 'deny',
     'note': '社員の削除は全社管理者のみ(部門管理者は不可)'},
    {'model': 'Employee', 'level': 'record', 'action': 'execute', 'scope': {'type': 'department_tree'}, 'effect': 'deny'},

    {'model': 'Department', 'level': 'record', 'action': 'view', 'scope': {'type': 'department_tree'}, 'effect': 'permit'},
    {'model': 'Department', 'level': 'record', 'action': 'create', 'scope': {'type': 'department_tree'}, 'effect': 'deny'},
    {'model': 'Department', 'level': 'record', 'action': 'edit', 'scope': {'type': 'department_tree'}, 'effect': 'deny'},
    {'model': 'Department', 'level': 'record', 'action': 'delete', 'scope': {'type': 'department_tree'}, 'effect': 'deny'},
    {'model': 'Department', 'level': 'record', 'action': 'execute', 'scope': {'type': 'department_tree'}, 'effect': 'deny'},

    {'model': 'Company', 'level': 'record', 'action': 'view', 'scope': {'type': 'company'}, 'effect': 'permit'},
    {'model': 'Company', 'level': 'record', 'action': 'create', 'scope': {'type': 'company'}, 'effect': 'deny'},
    {'model': 'Company', 'level': 'record', 'action': 'edit', 'scope': {'type': 'company'}, 'effect': 'deny'},
    {'model': 'Company', 'level': 'record', 'action': 'delete', 'scope': {'type': 'company'}, 'effect': 'deny'},
    {'model': 'Company', 'level': 'record', 'action': 'execute', 'scope': {'type': 'company'}, 'effect': 'deny'},

    # --- カラム権限(record権限がpermitの範囲でのみ意味を持つ。今回はテンプレート・フォームへの組み込みは行わない) ---
    {'model': 'Employee', 'level': 'field', 'field': 'employee_number', 'action': 'edit', 'effect': 'deny',
     'note': '社員番号(ログインID)は部門管理者からは変更できない'},
]
```

- `level='record'`の行に`field`キーは無し、`level='field'`の行に`scope`キーは無し(意味を持たないため)
- `scope`は`{'type': ...}`という辞書にし、将来`field_value`のような新しいスコープ種別を追加できる形にする(今回実装するのは下記5種類のみ)
- `note`は任意の人間向け説明(表のドキュメント化で「備考」列に使う)
- ルールに存在しない組み合わせは常にデフォルト`deny`

### `app/permissions/rule_sets/__init__.py`

```python
# ルール形式の決定経緯: docs/superpowers/specs/2026-08-08-access-control-design.md 参照
# (Claude Code settings.json風のallow/denyパターン文字列ではなく、AIが表に変換してConfluenceに
#  転記しやすいよう「1行=1権限」のフラットな辞書リスト形式を採用した)

from . import department_manager
from . import department_viewer

REGISTRY = {
    department_manager.ID: department_manager,
    department_viewer.ID: department_viewer,
}
```

新しい権限セットを追加する時は、`rule_sets/`にファイルを1つ追加し、`__init__.py`に1行importとREGISTRYへの登録を足すだけでよい。

## スコープ種別

| type | 意味 |
|---|---|
| `own` | 自分自身のレコードのみ(現状Employeeにのみ意味を持つ。`employee.user == user`) |
| `department` | `ManagementGroup.department`(割当部門)自体のみ |
| `department_tree` | 割当部門 + 配下の子部門(`DepartmentHierarchy`を再帰的に辿った全階層) |
| `company` | 割当部門が属する`Company`全体 |
| `all` | 全件(`is_admin=True`は常にこれと同義としてハードコード) |
| `field_value`(将来・未実装) | 任意のフィールド値による絞り込み(例: `{'type': 'field_value', 'field': 'category', 'values': [1]}`) |

`department_tree`は、ロール決定ロジックの「自分自身・親・兄弟」判定(1階層のみ)とは別物であることに注意。こちらは`DepartmentHierarchy.child_hierarchies`を起点に何階層でも再帰的に子部門を辿る。

## 権限判定API

```python
# app/permissions/access.py
def can_view(user, model_name, instance, field=None): ...
def can_create(user, model_name, department=None): ...   # departmentは作成しようとしているレコードの所属部門。Companyの場合はNone
def can_edit(user, model_name, instance, field=None): ...
def can_delete(user, model_name, instance): ...
def can_execute(user, model_name, instance): ...
```

### `create`のスコープ判定の特殊性

`create`時点では対象`instance`がまだ存在しないため、他アクションのように「既存レコードの部門」と比較できない。フォームの入力値(作成しようとしている部門)を`department`引数として渡して判定する。

- `own`スコープは`create`に対して常に不一致(まだ自分のレコードが存在しないため)
- `company`スコープは`department`引数が`None`(=Company作成)の場合は不一致。`all`スコープ(実質`is_admin`)のみCompanyを作成できる

### 複数グループ判定のマージロジック(3状態)

ユーザーに適用される`ManagementGroup`(`get_applicable_management_groups`で取得)ごとに、対象レコード(または`create`時は対象部門)に対する判定を求める。各グループの判定は以下の3状態のいずれかになる。

1. **棄権**: グループの`scope`が対象に一致しない(そのグループは何も主張しない)
2. **`permit`**: `scope`が一致し、該当するルールの`effect`が`permit`
3. **`deny`**: `scope`が一致し、該当するルールの`effect`が`deny`、またはそもそも該当するルールが無い(デフォルト拒否)

最終判定は、棄権を無視した上で「1つでも`deny`があれば`deny`、それ以外に`permit`が1つでもあれば`permit`、誰も判定しなければ`deny`」とする(deny優先)。

*棄権を`deny`と同列に扱うと、対象外のグループが存在するだけで他グループの`permit`を打ち消してしまうため、明示的に区別する。*

```python
def _check(user, model_name, action, instance=None, field=None, department=None):
    decisions = [
        _decide(group, model_name, action, instance, field, department)
        for group in get_applicable_management_groups(user)
    ]
    decisions = [d for d in decisions if d is not None]  # 棄権を除外
    if 'deny' in decisions:
        return False
    return 'permit' in decisions


def _decide(group, model_name, action, instance, field, department):
    if group.is_admin:
        return 'permit'
    rule_set = rule_sets.REGISTRY[group.permission_set_id]
    # scopeが対象に一致するかを判定し、一致しなければNone(棄権)を返す
    # 一致すれば、該当ルールのeffect('permit'/'deny')、ルールが無ければ'deny'を返す
    ...
```

## ビューへの組み込み方針

- **`index`(一覧)**: 全件取得 → Pythonの`can_view`でフィルタ → `Paginator`にフィルタ後のリストを渡す(`Paginator`はクエリセットだけでなくリストにも使えるため)。今回のデータ規模ではSQL側での絞り込みは行わず、シンプルさを優先する
- **`show`/`edit`/`delete`**: `get_object_or_404`の後に`can_view`/`can_edit`/`can_delete`をチェックし、不許可なら403(`HttpResponseForbidden`)を返す。既存の`management_group`ビューのテストパターン(403返却)に合わせる
- **`new`(作成)**:
  - GET: 適用グループのいずれかが対象モデルに対して`create`の`permit`を持てば(部門はまだ未確定のため広めに)フォームを表示する
  - POST: 送信された部門の値を使い`can_create(user, model_name, department=...)`で判定する
- **カラム権限(表示/編集)**: `can_view`/`can_edit`のフィールド版APIは`access.py`に実装するが、テンプレート・フォームへの組み込みは今回のスコープ外(元の12件のTODOはいずれもレコード単位のため)

## テスト方針

- `app/tests/unit/permissions/roles_test.py`(`app/tests/unit/lib/permissions_test.py`から移動、内容はそのまま)
- `app/tests/unit/permissions/access_test.py`(新規): `can_view`/`can_create`/`can_edit`/`can_delete`/`can_execute`の判定ロジック。スコープ一致・棄権・deny優先マージ・`is_admin`のハードコード動作を検証
- `app/tests/unit/permissions/rule_sets_test.py`(新規): `REGISTRY`内の全ルールセットが定義形式(必須キーの組み合わせ)を満たしていることを検証する構造チェック(ファイルを増やす運用のため、壊れたルールセットを早期検知する安全網)
- `app/tests/unit/models/management_group_test.py`: `permission_set_id`追加に伴うテスト更新
- `app/tests/unit/views/company_test.py`/`department_test.py`/`employee_test.py`: 既存テストは`auth_client`(どの`ManagementGroup`にも属さない一般ユーザー)で作成・編集・削除が成功する前提になっているため、`management_group_test.py`で確立したパターン(403確認 + `admin_client`や部門スコープ内ユーザーでの成功確認)に合わせて全面的に書き換える

## エッジケース・データ整合性

- **`permission_set_id`が`REGISTRY`に存在しない値**: `ManagementGroup.clean()`でエラーにする
- **`is_admin=True`かつ`permission_set_id`が設定されている**: エラーにする(`department`と同様の整合性ルール)
- **ルールセットファイルの構造不正**(必須キー欠落等): `rule_sets_test.py`で検知する。実行時には`access.py`側で必要なキーが無ければ例外を送出する(サイレントに無視しない)

## 今後の課題(スコープ外)

- カラム権限(フィールド単位のview/edit)を実際にテンプレート・フォームへ組み込む
- `execute`アクションを使う具体的な業務操作の実装
- スコープ種別`field_value`(任意フィールド値による絞り込み)の実装
