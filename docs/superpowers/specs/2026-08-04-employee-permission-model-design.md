# 社員権限モデル(ロール決定ロジック) 設計ドキュメント

## 背景・目的

現在、`ManagementGroup`は「ユーザーをグループ化するモデル」として存在するが、権限フラグや部門との紐付けは持たず(コミット`d9f1791`で一旦削除)、`Company`/`Department`/`Employee`の各ビューには「権限制御を再設計後、〜する」というTODOが残ったままになっている。

権限の仕組みは以下の2つに分かれる。

1. **ロール決定ロジック**: ログインした社員に、どの`ManagementGroup`が適用されるかを決定する
2. **アクセス制御**: 適用された`ManagementGroup`が、具体的にどの範囲のCompany/Department/Employeeを閲覧・操作できるかを決定する

本設計は **1. ロール決定ロジックのみ** を対象とする。2. アクセス制御(権限が及ぶ範囲)は意図的にスコープ外とし、別途あらためて設計する。

## スコープ

- 対象: ログインユーザーに適用される`ManagementGroup`を決定するロジックと、それに必要なデータモデルの追加・変更
- 対象外:
  - 適用された`ManagementGroup`が実際に何を閲覧・操作できるか(アクセス制御・権限の及ぶ範囲)
  - `company.py`/`department.py`/`employee.py`の各ビューへの権限チェック組み込み(アクセス制御の設計後に着手)
  - 5パターンあるとされる部門階層の汎用的な実装(今回は権限判定に必要な1系統の階層のみを新規に用意する。他の4パターンは、それを必要とする機能が実際に出てきた時点で別途設計する)

## 業務ルール

社員(`Employee`)がログインした際、以下の条件を満たす`ManagementGroup`が「適用される」。

1. ログインユーザー(`User`)がその`ManagementGroup`の`members`に含まれている
2. かつ、次のいずれかを満たす
   - その`ManagementGroup`が`is_admin=True`(部門に依存しない全社管理者グループ)である
   - その`ManagementGroup`の`department`が、ログインユーザーの社員としての**主務部門**(`EmployeeDepartment.is_primary=True`)から見て「自分自身・親部門・兄弟部門」のいずれかと一致する

補足:

- 「親・兄弟」の判定は1階層のみ(祖父母部門・孫部門は対象外)
- 1人の社員が複数の`ManagementGroup`に同時に所属してよく、複数の`ManagementGroup`が同時に適用されてもよい(「1人1グループ」に制限すると柔軟性が失われるため、意図的に許容する)
- `Company`は複数社運用する。部門の親子関係は同一`Company`内に閉じる(会社をまたいだ親子関係は不正)

## データモデル変更

### 新規: `DepartmentHierarchy`

権限判定専用の部門階層(将来的に他パターンの階層が必要になっても、それとは独立したテーブルとする)。

```python
class DepartmentHierarchy(models.Model):
    department = models.OneToOneField(
        Department, on_delete=models.CASCADE, related_name='hierarchy', verbose_name='部門'
    )
    parent_department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.CASCADE,
        related_name='child_hierarchies', verbose_name='親部門'
    )
```

- 1部門につき最大1レコード(`department`を`OneToOneField`とする)
- 最上位の部門は`parent_department=NULL`
- **すべての`Department`がレコードを持つ必要はない**(既存アプリからの移行データには階層未登録の部門が含まれる想定のため)。レコードが無い部門は「親・兄弟なし(自分自身のみ判定対象)」として扱う
- `clean()`で`parent_department.company == department.company`を検証し、会社をまたいだ親子関係を禁止する

### 変更: `ManagementGroup`

```python
class ManagementGroup(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='管理グループ名')
    members = models.ManyToManyField(User, related_name='management_groups', blank=True, verbose_name='メンバー')
    is_admin = models.BooleanField(default=False, verbose_name='全社管理者')
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.CASCADE,
        related_name='management_groups', verbose_name='割当部門'
    )
```

- `is_admin=True`の場合、`department`は`NULL`でなければならない(部門に依存しない全社的なグループのため)
- `is_admin=False`の場合、`department`は必須
- 上記の整合性は`clean()`で検証する

## ロール決定ロジック

`app/lib/permissions.py`に以下を追加する。

```python
# ログインユーザーに適用される管理グループの一覧を返す
def get_applicable_management_groups(user):
    groups = ManagementGroup.objects.filter(members=user)

    employee = getattr(user, 'employee', None)
    primary_department = _get_primary_department(employee) if employee else None

    applicable = []
    for group in groups:
        if group.is_admin:
            applicable.append(group)
            continue
        if primary_department and _is_self_parent_or_sibling(group.department, primary_department):
            applicable.append(group)
    return applicable
```

- 戻り値は0件〜複数件の`ManagementGroup`のリスト
- `_get_primary_department(employee)`: `employee.employee_departments`から`is_primary=True`の`Department`を取得する(無ければ`None`)
- `_is_self_parent_or_sibling(group_department, primary_department)`: `DepartmentHierarchy`を参照し、`group_department`が`primary_department`自身/親/兄弟のいずれかに一致するかを判定する。`primary_department`に`DepartmentHierarchy`のレコードが無い場合は「自分自身と一致するか」のみ判定する

この関数は、後続で設計する「アクセス制御」層から利用される想定(本設計では呼び出し元は作らない)。

## エッジケース・データ整合性

- **主務部門が無い社員**(`EmployeeDepartment`が0件、または`is_primary=True`が0件): `is_admin`グループの適用のみ判定される
- **`Employee`が無い`User`**(例: Djangoの管理者アカウント): 同様に`is_admin`グループの適用のみ判定される
- **未ログイン(`AnonymousUser`)**: `get_applicable_management_groups`は`@login_required`配下でのみ呼ばれる前提とし、関数自体では特別扱いしない(既存の`is_admin(request.user)`と同じ方針)
- **`DepartmentHierarchy`の循環**: 今回は防止しない(移行データの都合)。「自分自身・親・兄弟」という1階層の判定ロジックである限り、循環があっても無限ループにはならない
- **`ManagementGroup.is_admin`と`department`の不整合**: `clean()`で防止する

## テスト方針

既存のレイヤー分割(`app/tests/unit/models/`, `app/tests/unit/lib/`)に従う。

- `app/tests/unit/models/department_hierarchy_test.py`(新規): 会社をまたいだ親子関係が無効になること等
- `app/tests/unit/models/management_group_test.py`(既存を拡張): `is_admin`/`department`の整合性バリデーション
- `app/tests/unit/lib/permissions_test.py`(既存を拡張): `get_applicable_management_groups`について以下を検証
  - グループの`department`が自部門/親部門/兄弟部門と一致する場合に適用されること
  - 一致しない場合に適用されないこと
  - `is_admin=True`のグループはメンバーであれば無条件で適用されること
  - 主務部門が無い社員は`is_admin`グループ以外適用されないこと
  - `DepartmentHierarchy`にレコードが無い部門は自分自身のみ判定されること
  - 複数の`ManagementGroup`が同時に適用されるケース

## 今後の課題(スコープ外)

- アクセス制御: 適用された`ManagementGroup`が実際に閲覧・操作できる範囲(Company/Department/Employeeのどこまでか)
- `company.py`/`department.py`/`employee.py`の各ビューへの権限チェック組み込み
- 5パターンある部門階層のうち、今回用意しなかった他パターンの実装(必要になった機能が出た時点で別途設計)
