# アクセス制御 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `ManagementGroup`に「権限セット」を紐づけ、Company/Department/Employeeの各ビューに残る12件のTODO(閲覧範囲の絞り込み、作成/編集/削除可否のチェック)を解消する。

**Architecture:** `app/lib/permissions.py`を`app/permissions/`(トップレベルディレクトリ)に昇格し、既存のロール決定ロジック(`roles.py`)とは別に、レコード・カラム単位の権限判定(`access.py`)を追加する。権限セットはDBテーブルではなく`app/permissions/rule_sets/`配下のPythonファイル(1セット1ファイル)としてハードコードし、`ManagementGroup.permission_set_id`(整数)で参照する。判定は「フィールドパス→期待値」の汎用フィルタ辞書(`scope`)をPython側で評価する方式とし、DBクエリには依存しない。

**Tech Stack:** Django 6.0 (Model, ModelForm, FBV), pytest-django (unit test)

参照仕様書: `docs/superpowers/specs/2026-08-08-access-control-design.md`

## Global Constraints

- クリーンロジック(`clean()`)を持つモデルは`save()`をオーバーライドして`self.full_clean()`を必ず呼ぶ(`.claude/instructions.md` Model Validation Rules)
- ビューは関数ベースビュー(FBV)。GET/POSTの分岐関数は振り分けのみとし、実処理はprivateヘルパーに切り出す(`.claude/instructions.md` View Method-Branch Rules)
- 権限が無い場合は`django.core.exceptions.PermissionDenied`を送出する(Djangoが自動的に403として処理する。既存の`app/views/management_group.py`の`_require_admin`と同じパターン)
- `scope`の評価(`_resolve_path`)はスカラー属性・単一の外部キー(`company.name`等)の走査のみをサポートする。`Employee.departments`のような多対多リレーションは`_resolve_path`では辿れない(`RelatedManager`は単純な属性比較にそぐわないため)。本プランで用意する2つの例示ルールセットはEmployeeモデルへのscope指定を行わないため、この制約が問題になることはない
- `own`(自分自身のレコードのみ)に相当する概念はこのアプリに存在しないため、実装しない
- 同一ブランチ内(mainに未マージ)でのモデル変更のため、`ManagementGroup`関連の新規マイグレーションは既存の未適用マイグレーション(`0010_managementgroup_department_managementgroup_is_admin.py`)に追記し、新規ファイルは作らない(`.claude/instructions.md` Migration Rules)
- コミットメッセージに`Co-Authored-By: Claude ...`のようなAI署名のトレーラーは含めない

---

### Task 1: `app/lib/permissions.py`を`app/permissions/roles.py`に昇格する

**Files:**
- Create: `app/permissions/__init__.py`(空ファイル)
- Create: `app/permissions/roles.py`
- Delete: `app/lib/permissions.py`
- Create: `app/tests/unit/permissions/__init__.py`(空ファイル)
- Create: `app/tests/unit/permissions/roles_test.py`
- Delete: `app/tests/unit/lib/permissions_test.py`
- Modify: `app/views/task.py`(import文のみ)
- Modify: `app/views/management_group.py`(import文のみ)
- Modify: `.claude/instructions.md`(Common Module Rulesに昇格ルールを追記)

**Interfaces:**
- Produces: `app.permissions.roles.is_admin(user)`, `can_edit_task(user, task)`, `can_delete_task(user, task)`, `get_applicable_management_groups(user)`(すべて`app/lib/permissions.py`から中身そのまま移動)。Task 4で`app.permissions.access`から利用される。

- [ ] **Step 1: `app/permissions/__init__.py`と`app/tests/unit/permissions/__init__.py`を空ファイルとして作成する**

```bash
mkdir -p app/permissions app/tests/unit/permissions
touch app/permissions/__init__.py app/tests/unit/permissions/__init__.py
```

- [ ] **Step 2: `app/lib/permissions.py`の内容をそのまま`app/permissions/roles.py`に移動する**

```bash
git mv app/lib/permissions.py app/permissions/roles.py
```

- [ ] **Step 3: `app/lib/permissions.py`を参照している箇所のimportを`app.permissions.roles`に書き換える**

`app/views/task.py`の該当行を書き換える。

```python
# 変更前
from app.lib.permissions import can_delete_task, can_edit_task
# 変更後
from app.permissions.roles import can_delete_task, can_edit_task
```

`app/views/management_group.py`の該当行を書き換える。

```python
# 変更前
from app.lib.permissions import is_admin
# 変更後
from app.permissions.roles import is_admin
```

- [ ] **Step 4: テストファイルを移動し、importを書き換える**

```bash
git mv app/tests/unit/lib/permissions_test.py app/tests/unit/permissions/roles_test.py
```

`app/tests/unit/permissions/roles_test.py`の先頭のimportを書き換える。

```python
# 変更前
from app.lib.permissions import can_delete_task, can_edit_task, get_applicable_management_groups, is_admin
# 変更後
from app.permissions.roles import can_delete_task, can_edit_task, get_applicable_management_groups, is_admin
```

- [ ] **Step 5: テストを実行し、移動後も全件PASSすることを確認する**

Run: `pytest app/tests/unit/permissions/roles_test.py app/tests/unit/views/task_test.py app/tests/unit/views/management_group_test.py -v`
Expected: 全件PASS

- [ ] **Step 6: `.claude/instructions.md`のCommon Module Rulesに、モジュールをトップレベルディレクトリへ昇格させてよい旨を追記する**

`.claude/instructions.md`の「例外: `app/management/commands/`(Djangoがこの場所を前提に...)は`app/lib/`に含めない。」の行の直後に、以下の段落を追加する。

```markdown
- **`app/lib/`配下のモジュールが肥大化した場合の昇格**: 関心事が独立したサブシステムと呼べる規模になった場合、`app/permissions/`のように`models/`/`views/`/`forms/`等と同列のトップレベルディレクトリへ昇格してよい。昇格後は他のトップレベルディレクトリと同じ構成規則(ディレクトリ化・`__init__.py`配置・テストディレクトリの対応)に従う。
```

- [ ] **Step 7: プロジェクト全体のユニットテストを実行し、回帰が無いことを確認する**

Run: `pytest app/tests/unit/ -v`
Expected: 全テストPASS

- [ ] **Step 8: コミットする**

```bash
git add app/permissions/ app/tests/unit/permissions/ app/lib/permissions.py app/tests/unit/lib/permissions_test.py \
  app/views/task.py app/views/management_group.py .claude/instructions.md
git commit -m "app/lib/permissions.pyをapp/permissions/roles.pyへ昇格する"
```

---

### Task 2: `app/permissions/rule_sets/`ディレクトリと2つの例示ルールセットを作成する

**Files:**
- Create: `app/permissions/rule_sets/__init__.py`
- Create: `app/permissions/rule_sets/department_viewer_all.py`
- Create: `app/permissions/rule_sets/company_scoped_department_manager.py`
- Test: `app/tests/unit/permissions/rule_sets_test.py`

**Interfaces:**
- Produces: `app.permissions.rule_sets.REGISTRY`(`dict[int, module]`。キーは各ルールセットの`ID`)。Task 3で`ManagementGroup.clean()`から、Task 4で`app.permissions.access`から利用される。
- Produces (各ルールセットモジュール): `ID`(`int`)、`NAME`(`str`)、`DESCRIPTION`(`str`)、`RULES`(`list[dict]`)。各ルールは`level='record'`なら`{'model', 'level', 'action', 'scope', 'effect'}`キー、`level='field'`なら`{'model', 'level', 'field', 'action', 'effect'}`キーを持つ(`note`は任意)。

- [ ] **Step 1: 失敗するテストを書く**

`app/tests/unit/permissions/rule_sets_test.py`を新規作成する。

```python
import pytest
from app.permissions import rule_sets

RECORD_ACTIONS = {'view', 'create', 'edit', 'delete', 'execute'}
FIELD_ACTIONS = {'view', 'edit'}
REQUIRED_RECORD_KEYS = {'model', 'level', 'action', 'scope', 'effect'}
REQUIRED_FIELD_KEYS = {'model', 'level', 'field', 'action', 'effect'}


# rule_sets.REGISTRYの構造をテストするクラス
class TestRuleSetsRegistry:

    # REGISTRYのキーが各ルールセットファイルのIDと一致することを確認
    def test_registry_keys_match_rule_set_ids(self):
        for permission_set_id, rule_set in rule_sets.REGISTRY.items():
            assert rule_set.ID == permission_set_id

    # 各ルールセットがNAME/DESCRIPTION/RULESを持つことを確認
    def test_each_rule_set_has_required_attributes(self):
        for rule_set in rule_sets.REGISTRY.values():
            assert isinstance(rule_set.NAME, str) and rule_set.NAME
            assert isinstance(rule_set.DESCRIPTION, str) and rule_set.DESCRIPTION
            assert isinstance(rule_set.RULES, list) and rule_set.RULES

    # 各ルールが定義形式(必須キーの組み合わせ)を満たすことを確認
    def test_each_rule_has_required_keys(self):
        for rule_set in rule_sets.REGISTRY.values():
            for rule in rule_set.RULES:
                if rule['level'] == 'record':
                    assert REQUIRED_RECORD_KEYS <= rule.keys()
                    assert rule['action'] in RECORD_ACTIONS
                    assert 'field' not in rule
                elif rule['level'] == 'field':
                    assert REQUIRED_FIELD_KEYS <= rule.keys()
                    assert rule['action'] in FIELD_ACTIONS
                    assert 'scope' not in rule
                else:
                    pytest.fail(f"未知のlevel: {rule['level']}")

    # 同じmodel・level・action(・field)の組み合わせのルールが重複していないことを確認
    def test_no_duplicate_rules(self):
        for rule_set in rule_sets.REGISTRY.values():
            keys = [
                (rule['model'], rule['level'], rule['action'], rule.get('field'))
                for rule in rule_set.RULES
            ]
            assert len(keys) == len(set(keys))
```

- [ ] **Step 2: テストを実行し、`app.permissions.rule_sets`が存在せず失敗することを確認する**

Run: `pytest app/tests/unit/permissions/rule_sets_test.py -v`
Expected: FAIL(`ModuleNotFoundError: No module named 'app.permissions.rule_sets'`)

- [ ] **Step 3: `app/permissions/rule_sets/department_viewer_all.py`を作成する**

```python
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

- [ ] **Step 4: `app/permissions/rule_sets/company_scoped_department_manager.py`を作成する**

```python
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

    # --- カラム権限(record権限がallowの範囲でのみ意味を持つ。テンプレート・フォームへの組み込みは別プランで行う) ---
    {'model': 'Department', 'level': 'field', 'field': 'company', 'action': 'edit', 'effect': 'deny',
     'note': '所属会社の変更(会社をまたぐ移動)はこの権限セットからは行えない'},
]
```

- [ ] **Step 5: `app/permissions/rule_sets/__init__.py`を作成する**

```python
# 設計の決定経緯: docs/superpowers/specs/2026-08-08-access-control-design.md 参照
# - ルール形式: Claude Code settings.json風のallow/denyパターン文字列ではなく、AIが表に変換して
#   Confluenceに転記しやすいよう「1行=1権限」のフラットな辞書リスト形式を採用した
# - スコープ形式: 部門階層等の固定列挙型ではなく、実際の業務要件に合わせて任意のフィールドパスで
#   絞り込める汎用フィルタ辞書を採用した
#
# 新しい権限セットを追加する時は、このディレクトリにファイルを1つ追加し、
# 下記のimportとREGISTRYへの登録を1行ずつ足す。

from . import department_viewer_all
from . import company_scoped_department_manager

REGISTRY = {
    department_viewer_all.ID: department_viewer_all,
    company_scoped_department_manager.ID: company_scoped_department_manager,
}
```

- [ ] **Step 6: テストを実行し、PASSすることを確認する**

Run: `pytest app/tests/unit/permissions/rule_sets_test.py -v`
Expected: 4件PASS

- [ ] **Step 7: コミットする**

```bash
git add app/permissions/rule_sets/ app/tests/unit/permissions/rule_sets_test.py
git commit -m "権限セットのルールをapp/permissions/rule_sets/にハードコードする仕組みを追加する"
```

---

### Task 3: `ManagementGroup`に`permission_set_id`を追加する

**Files:**
- Modify: `app/models/management_group.py`
- Modify: `app/migrations/0010_managementgroup_department_managementgroup_is_admin.py`
- Modify: `app/forms/management_group.py`
- Modify: `app/templates/app/management_group/_form.html`
- Modify: `app/tests/unit/models/management_group_test.py`
- Modify: `app/tests/unit/forms/management_group_test.py`

**Interfaces:**
- Consumes: `app.permissions.rule_sets.REGISTRY`(Task 2)
- Produces: `ManagementGroup.permission_set_id`(`IntegerField`, null許可)。Task 4で`app.permissions.access`から利用される。

- [ ] **Step 1: モデルテストに失敗するテストを追記する**

`app/tests/unit/models/management_group_test.py`の`TestManagementGroupModel`クラス内、`test_department_forbidden_when_admin`メソッドの直後に追記する。

```python
    # is_admin=Falseなのに権限セット番号が未設定の場合はエラーになることを確認
    def test_permission_set_id_required_when_not_admin(self):
        department = _create_department('開発部')

        with pytest.raises(ValidationError):
            ManagementGroup.objects.create(name='不正なグループ', department=department)

    # is_admin=Trueなのに権限セット番号が設定されている場合はエラーになることを確認
    def test_permission_set_id_forbidden_when_admin(self):
        with pytest.raises(ValidationError):
            ManagementGroup.objects.create(name='不正なグループ', is_admin=True, permission_set_id=1)

    # REGISTRYに存在しない権限セット番号を指定した場合はエラーになることを確認
    def test_unknown_permission_set_id_is_rejected(self):
        department = _create_department('開発部')

        with pytest.raises(ValidationError):
            ManagementGroup.objects.create(name='不正なグループ', department=department, permission_set_id=999)

    # REGISTRYに存在する権限セット番号を指定した場合は作成できることを確認
    def test_valid_permission_set_id_is_accepted(self):
        department = _create_department('開発部')

        group = ManagementGroup.objects.create(name='開発部管理グループ', department=department, permission_set_id=1)

        assert group.permission_set_id == 1
```

- [ ] **Step 2: テストを実行し、`permission_set_id`が未知のキーワード引数のため失敗することを確認する**

Run: `pytest app/tests/unit/models/management_group_test.py -v`
Expected: FAIL(`TypeError: ManagementGroup() got unexpected keyword arguments: 'permission_set_id'`)

- [ ] **Step 3: `app/models/management_group.py`を書き換える**

```python
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from app.models.department import Department
from app.permissions import rule_sets


# ユーザーをグループ化し、権限を付与するためのモデル
class ManagementGroup(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='管理グループ名')
    members = models.ManyToManyField(User, related_name='management_groups', blank=True, verbose_name='メンバー')
    is_admin = models.BooleanField(default=False, verbose_name='全社管理者')
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.CASCADE,
        related_name='management_groups', verbose_name='割当部門'
    )
    permission_set_id = models.IntegerField(null=True, blank=True, verbose_name='権限セット番号')

    class Meta:
        db_table = 'management_group'
        ordering = ['name']
        verbose_name = '管理グループ'
        verbose_name_plural = '管理グループ'

    def __str__(self):
        return self.name

    # is_adminと部門・権限セット設定の整合性を検証する(全社管理者は部門・権限セットを持たず、それ以外は両方必須)
    def clean(self):
        if self.is_admin and self.department_id is not None:
            raise ValidationError('全社管理者グループには部門を設定できません。')
        if not self.is_admin and self.department_id is None:
            raise ValidationError('全社管理者でない場合は部門の設定が必須です。')
        if self.is_admin and self.permission_set_id is not None:
            raise ValidationError('全社管理者グループには権限セットを設定できません。')
        if not self.is_admin and self.permission_set_id is None:
            raise ValidationError('全社管理者でない場合は権限セットの設定が必須です。')
        if not self.is_admin and self.permission_set_id not in rule_sets.REGISTRY:
            raise ValidationError('存在しない権限セット番号です。')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
```

- [ ] **Step 4: マイグレーションファイルに`permission_set_id`の`AddField`を追記する**

`app/migrations/0010_managementgroup_department_managementgroup_is_admin.py`の`operations`リストの末尾(`is_admin`の`AddField`の後)に追記する。

```python
        migrations.AddField(
            model_name='managementgroup',
            name='permission_set_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='権限セット番号'),
        ),
```

- [ ] **Step 5: マイグレーションがモデル定義とズレていないことを確認し、適用する**

Run: `python manage.py makemigrations --check --dry-run`
Expected: `No changes detected`(手動編集したマイグレーションがモデル定義と一致している)

Run: `python manage.py migrate`
Expected: マイグレーションが正常に適用される

- [ ] **Step 6: モデルテストを実行し、PASSすることを確認する**

Run: `pytest app/tests/unit/models/management_group_test.py -v`
Expected: 11件PASS

- [ ] **Step 7: フォームテストに失敗するテストを追記する**

`app/tests/unit/forms/management_group_test.py`の`test_department_required_when_not_admin`メソッドの直後に追記する。

```python
    # 全社管理者でないのに権限セット番号が未指定の場合、フォームが無効と判定されることを確認
    def test_permission_set_id_required_when_not_admin(self, sample_department):
        form = ManagementGroupForm(data={
            'name': '開発チーム',
            'members': [],
            'is_admin': False,
            'department': sample_department.id,
        })
        assert not form.is_valid()

    # 全社管理者でなく、部門・権限セット番号を指定していれば妥当と判定されることを確認
    def test_valid_non_admin_data_is_valid(self, sample_department):
        form = ManagementGroupForm(data={
            'name': '開発チーム',
            'members': [],
            'is_admin': False,
            'department': sample_department.id,
            'permission_set_id': 1,
        })
        assert form.is_valid()
```

ファイル末尾に、`sample_department`フィクスチャを追加する。

```python
@pytest.fixture
def sample_department():
    from app.models import Company, Department
    company = Company.objects.create(name='サンプル株式会社')
    return Department.objects.create(company=company, name='開発部')
```

- [ ] **Step 8: テストを実行し、`permission_set_id`がフォームに無いため失敗することを確認する**

Run: `pytest app/tests/unit/forms/management_group_test.py -v`
Expected: FAIL(`test_valid_non_admin_data_is_valid`が、フォームに`permission_set_id`フィールドが無いため`is_valid()`が`False`になり失敗する)

- [ ] **Step 9: `app/forms/management_group.py`を書き換える**

```python
from django import forms
from app.models import ManagementGroup


# 管理グループの新規作成・編集で使うフォーム
class ManagementGroupForm(forms.ModelForm):
    class Meta:
        model = ManagementGroup
        fields = ['name', 'members', 'is_admin', 'department', 'permission_set_id']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'members': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'is_admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'permission_set_id': forms.NumberInput(attrs={'class': 'form-control'}),
        }
```

- [ ] **Step 10: フォームテストを実行し、PASSすることを確認する**

Run: `pytest app/tests/unit/forms/management_group_test.py -v`
Expected: 7件PASS

- [ ] **Step 11: `app/templates/app/management_group/_form.html`に権限セット番号の入力欄を追加する**

`{{ form.department }}`のフィールドブロックの直後、`<button type="submit" ...>`の直前に追加する。

```html
    <div class="form-field mb-3">
        <label for="{{ form.permission_set_id.id_for_label }}" class="form-label">権限セット番号</label>
        {{ form.permission_set_id }}
        <div class="text-danger small">{{ form.permission_set_id.errors }}</div>
    </div>
```

- [ ] **Step 12: プロジェクト全体のユニットテストを実行し、回帰が無いことを確認する**

Run: `pytest app/tests/unit/ -v`
Expected: 全テストPASS

- [ ] **Step 13: コミットする**

```bash
git add app/models/management_group.py app/migrations/0010_managementgroup_department_managementgroup_is_admin.py \
  app/forms/management_group.py app/templates/app/management_group/_form.html \
  app/tests/unit/models/management_group_test.py app/tests/unit/forms/management_group_test.py
git commit -m "ManagementGroupにpermission_set_idを追加し、権限セットを紐づけられるようにする"
```

---

### Task 4: `app/permissions/access.py`を実装する

**Files:**
- Create: `app/permissions/access.py`
- Test: `app/tests/unit/permissions/access_test.py`

**Interfaces:**
- Consumes: `app.permissions.roles.get_applicable_management_groups(user)`(Task 1)、`app.permissions.rule_sets.REGISTRY`(Task 2)、`ManagementGroup.permission_set_id`(Task 3)
- Produces:
  - `can_view(user, model_name, instance, field=None) -> bool`
  - `can_create(user, model_name, candidate) -> bool`(`candidate`はフォームの`cleaned_data`から組み立てた未保存インスタンス)
  - `can_edit(user, model_name, instance, field=None) -> bool`
  - `can_delete(user, model_name, instance) -> bool`
  - `can_execute(user, model_name, instance) -> bool`
  - `can_display_create_form(user, model_name) -> bool`(具体的な対象が無い状態で、作成フォームを表示してよいかを判定する。`new`ビューのGETで使用)

  Task 5/6/7の各ビューから利用される。`model_name`は`'Company'`/`'Department'`/`'Employee'`のような文字列で、ルールセットの`RULES`内`model`キーと一致させる。

- [ ] **Step 1: 失敗するテストを書く**

`app/tests/unit/permissions/access_test.py`を新規作成する。

```python
import pytest
from app.models import Company, Department, EmployeeDepartment, ManagementGroup
from app.permissions.access import can_create, can_delete, can_display_create_form, can_edit, can_execute, can_view

DEPARTMENT_VIEWER_ALL = 1
COMPANY_SCOPED_DEPARTMENT_MANAGER = 2


@pytest.mark.django_db
class TestIsAdminBypass:

    # is_admin=Trueのグループに所属していれば、どのモデル・アクションでも常にallowと判定されることを確認
    def test_admin_group_member_can_do_anything(self, sample_user):
        company = Company.objects.create(name='サンプル株式会社')
        admin_group = ManagementGroup.objects.create(name='全社管理者', is_admin=True)
        admin_group.members.add(sample_user)

        assert can_view(sample_user, 'Company', company) is True
        assert can_edit(sample_user, 'Company', company) is True
        assert can_delete(sample_user, 'Company', company) is True
        assert can_execute(sample_user, 'Company', company) is True
        assert can_create(sample_user, 'Company', Company(name='新会社')) is True


@pytest.mark.django_db
class TestScopeMatching:

    # scope={}(絞り込み無し)のルールはどのレコードにもallowすることを確認
    def test_empty_scope_matches_any_record(self, sample_user):
        anchor = _create_department('総務部', 'テスト工業株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('viewer', DEPARTMENT_VIEWER_ALL, anchor, sample_user)

        assert can_view(sample_user, 'Department', anchor) is True

    # 該当するeffect=denyのルールがあればdenyと判定されることを確認
    def test_explicit_deny_rule_denies(self, sample_user):
        anchor = _create_department('総務部', 'テスト工業株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('viewer', DEPARTMENT_VIEWER_ALL, anchor, sample_user)

        assert can_edit(sample_user, 'Department', anchor) is False

    # ルールが1件も無いモデル・アクションはデフォルトでdenyと判定されることを確認
    def test_no_matching_rule_defaults_to_deny(self, sample_user):
        anchor = _create_department('総務部', 'テスト工業株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('viewer', DEPARTMENT_VIEWER_ALL, anchor, sample_user)
        company = Company.objects.create(name='サンプル株式会社')

        assert can_view(sample_user, 'Company', company) is False

    # scopeのフィールドパスが一致する場合にallowと判定されることを確認
    def test_scope_field_path_matches(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)
        matching_department = Department.objects.create(company=anchor.company, name='開発部')

        assert can_view(sample_user, 'Department', matching_department) is True

    # scopeのフィールドパスが一致しない場合、そのグループは棄権しdenyになることを確認
    def test_scope_field_path_mismatch_defaults_to_deny(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)
        other_company = Company.objects.create(name='テスト工業株式会社')
        non_matching_department = Department.objects.create(company=other_company, name='総務部')

        assert can_view(sample_user, 'Department', non_matching_department) is False


@pytest.mark.django_db
class TestMultiGroupMerge:

    # 一方のグループがscope不一致で棄権しても、もう一方のグループのallowが有効になることを確認
    def test_abstaining_group_does_not_block_other_groups_allow(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)
        _create_group('viewer', DEPARTMENT_VIEWER_ALL, anchor, sample_user)
        other_company = Company.objects.create(name='テスト工業株式会社')
        target_department = Department.objects.create(company=other_company, name='総務部')

        # company_scoped_department_managerはscope不一致で棄権するが、department_viewer_allが常にallowするため最終的にTrue
        assert can_view(sample_user, 'Department', target_department) is True

    # 一方のグループが明示的にdeny、もう一方がallowの場合、deny優先で最終的にdenyになることを確認
    def test_explicit_deny_overrides_other_groups_allow(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)
        matching_department = Department.objects.create(company=anchor.company, name='開発部')

        # company_scoped_department_managerはこの部門の削除を明示的にdenyしている
        assert can_delete(sample_user, 'Department', matching_department) is False


@pytest.mark.django_db
class TestFieldLevelPermission:

    # フィールド権限にdenyルールがある場合、can_edit(..., field=...)がFalseになることを確認
    def test_field_level_deny(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)
        department = Department.objects.create(company=anchor.company, name='開発部')

        assert can_edit(sample_user, 'Department', department, field='company') is False

    # フィールド権限にルールが無い場合、デフォルトdenyになることを確認
    def test_field_level_no_rule_defaults_to_deny(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)
        department = Department.objects.create(company=anchor.company, name='開発部')

        assert can_edit(sample_user, 'Department', department, field='name') is False


@pytest.mark.django_db
class TestCanCreate:

    # フォーム入力値から組み立てた未保存インスタンスのscopeが一致すればallowと判定されることを確認
    def test_create_with_matching_scope_allows(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)
        candidate = Department(company=anchor.company, name='新部門')

        assert can_create(sample_user, 'Department', candidate) is True

    # 未保存インスタンスのscopeが一致しなければdenyと判定されることを確認
    def test_create_with_non_matching_scope_denies(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)
        other_company = Company.objects.create(name='テスト工業株式会社')
        candidate = Department(company=other_company, name='新部門')

        assert can_create(sample_user, 'Department', candidate) is False


@pytest.mark.django_db
class TestCanDisplayCreateForm:

    # createにallowのルールを持つグループに所属していれば、具体的な値が無くてもTrueと判定されることを確認
    def test_true_when_any_group_allows_create(self, sample_user):
        anchor = _create_department('人事部', 'サンプル株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('manager', COMPANY_SCOPED_DEPARTMENT_MANAGER, anchor, sample_user)

        assert can_display_create_form(sample_user, 'Department') is True

    # createがdeny(または未定義)のルールセットしか無ければFalseと判定されることを確認
    def test_false_when_no_group_allows_create(self, sample_user):
        anchor = _create_department('総務部', 'テスト工業株式会社')
        _set_primary_department(sample_user, anchor)
        _create_group('viewer', DEPARTMENT_VIEWER_ALL, anchor, sample_user)

        assert can_display_create_form(sample_user, 'Department') is False

    # どの管理グループにも所属していなければFalseと判定されることを確認
    def test_false_when_user_has_no_groups(self, sample_user):
        assert can_display_create_form(sample_user, 'Department') is False


def _create_department(name, company_name):
    company, _ = Company.objects.get_or_create(name=company_name)
    return Department.objects.create(company=company, name=name)


def _set_primary_department(user, department):
    EmployeeDepartment.objects.create(employee=user.employee, department=department, is_primary=True)


def _create_group(name, permission_set_id, department, member):
    group = ManagementGroup.objects.create(name=name, department=department, permission_set_id=permission_set_id)
    group.members.add(member)
    return group
```

- [ ] **Step 2: テストを実行し、`app.permissions.access`が存在せず失敗することを確認する**

Run: `pytest app/tests/unit/permissions/access_test.py -v`
Expected: FAIL(`ModuleNotFoundError: No module named 'app.permissions.access'`)

- [ ] **Step 3: `app/permissions/access.py`を作成する**

```python
from app.permissions import rule_sets
from app.permissions.roles import get_applicable_management_groups


# 対象レコードを閲覧できるかどうかを判定する(fieldを指定するとカラム単位の判定になる)
def can_view(user, model_name, instance, field=None):
    return _check(user, model_name, 'view', instance=instance, field=field)


# 新規作成しようとしている未保存インスタンス(candidate)を作成できるかどうかを判定する
def can_create(user, model_name, candidate):
    return _check(user, model_name, 'create', instance=candidate)


# 対象レコードを編集できるかどうかを判定する(fieldを指定するとカラム単位の判定になる)
def can_edit(user, model_name, instance, field=None):
    return _check(user, model_name, 'edit', instance=instance, field=field)


# 対象レコードを削除できるかどうかを判定する
def can_delete(user, model_name, instance):
    return _check(user, model_name, 'delete', instance=instance)


# 対象レコードに対して実行系の操作ができるかどうかを判定する
def can_execute(user, model_name, instance):
    return _check(user, model_name, 'execute', instance=instance)


# 具体的な入力値が無い状態(newのGET)で、作成フォームを表示してよいかどうかを判定する
# (scopeによる絞り込みは行わず、createにallowのルールを持つグループが1つでもあればTrue)
def can_display_create_form(user, model_name):
    for group in get_applicable_management_groups(user):
        if group.is_admin:
            return True
        rule_set = rule_sets.REGISTRY[group.permission_set_id]
        rule = _find_rule(rule_set, model_name, 'record', 'create')
        if rule is not None and rule['effect'] == 'allow':
            return True
    return False


# ============================================================
# ここから先はprivateヘルパー
# ============================================================


# ユーザーに適用される全ManagementGroupの判定をdeny優先でマージする
def _check(user, model_name, action, instance=None, field=None):
    level = 'field' if field is not None else 'record'
    decisions = [
        _decide(group, model_name, level, action, instance, field)
        for group in get_applicable_management_groups(user)
    ]
    decisions = [decision for decision in decisions if decision is not None]  # 棄権を除外
    if 'deny' in decisions:
        return False
    return 'allow' in decisions


# 1つのManagementGroupの判定を返す('allow'/'deny'/棄権を表すNone)
def _decide(group, model_name, level, action, instance, field):
    if group.is_admin:
        return 'allow'
    rule_set = rule_sets.REGISTRY[group.permission_set_id]
    rule = _find_rule(rule_set, model_name, level, action, field)
    if rule is None:
        return 'deny'
    if level == 'field':
        return rule['effect']
    if not _matches(instance, rule['scope']):
        return None  # 棄権
    return rule['effect']


# ルールセットの中から、model・level・action(・field)が一致するルールを1件探す
def _find_rule(rule_set, model_name, level, action, field=None):
    for rule in rule_set.RULES:
        if rule['model'] != model_name or rule['level'] != level or rule['action'] != action:
            continue
        if level == 'field' and rule.get('field') != field:
            continue
        return rule
    return None


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

- [ ] **Step 4: テストを実行し、PASSすることを確認する**

Run: `pytest app/tests/unit/permissions/access_test.py -v`
Expected: 全件PASS

- [ ] **Step 5: プロジェクト全体のユニットテストを実行し、回帰が無いことを確認する**

Run: `pytest app/tests/unit/ -v`
Expected: 全テストPASS

- [ ] **Step 6: コミットする**

```bash
git add app/permissions/access.py app/tests/unit/permissions/access_test.py
git commit -m "app/permissions/access.pyを追加し、レコード・カラム単位の権限判定APIを実装する"
```

---

### Task 5: Companyビューにアクセス制御を組み込む

**Files:**
- Modify: `app/views/company.py`
- Modify: `app/tests/unit/views/company_test.py`

**Interfaces:**
- Consumes: `app.permissions.access.can_view/can_create/can_edit/can_delete/can_display_create_form`(Task 4)

- [ ] **Step 1: 失敗するテストを書く(既存テストを全面的に置き換える)**

`app/tests/unit/views/company_test.py`を以下の内容で置き換える。

```python
import pytest
from app.models import Company, Department, EmployeeDepartment, ManagementGroup

DEPARTMENT_VIEWER_ALL = 1
COMPANY_SCOPED_DEPARTMENT_MANAGER = 2


@pytest.mark.django_db
class TestCompanyIndexView:

    # 未ログインの場合、ログインページにリダイレクトされることを確認
    def test_index_requires_login(self, client):
        response = client.get('/companies/')
        assert response.status_code == 302
        assert response.url.startswith('/login/')

    # 会社閲覧の権限が無いユーザーには一覧が0件になることを確認
    def test_index_by_user_without_permission_is_empty(self, auth_client):
        Company.objects.create(name='サンプル株式会社')

        response = auth_client.get('/companies/')
        assert response.status_code == 200
        assert len(response.context['companies']) == 0

    # 会社閲覧を許可する権限セットを持つユーザーには一覧に表示されることを確認
    def test_index_by_user_with_view_permission(self, sample_user, auth_client):
        Company.objects.create(name='サンプル株式会社')
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER)

        response = auth_client.get('/companies/')
        assert response.status_code == 200
        assert len(response.context['companies']) == 1

    # 管理者は一覧を取得できることを確認
    def test_index_by_admin_succeeds(self, admin_client):
        Company.objects.create(name='サンプル株式会社')

        response = admin_client.get('/companies/')
        assert response.status_code == 200
        assert len(response.context['companies']) == 1


@pytest.mark.django_db
class TestCompanyShowView:

    # 会社閲覧の権限が無いユーザーがアクセスすると403が返ることを確認
    def test_show_by_user_without_permission_returns_403(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')

        response = auth_client.get(f'/companies/{company.id}/')
        assert response.status_code == 403

    # 会社閲覧を許可する権限セットを持つユーザーは詳細を取得できることを確認
    def test_show_by_user_with_view_permission(self, sample_user, auth_client):
        company = Company.objects.create(name='サンプル株式会社')
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER)

        response = auth_client.get(f'/companies/{company.id}/')
        assert response.status_code == 200
        assert response.context['company'] == company

    # 存在しない会社の場合404が返ることを確認
    def test_show_nonexistent_company_returns_404(self, admin_client):
        response = admin_client.get('/companies/9999/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestCompanyCreateView:

    # 作成権限が無いユーザーがアクセスすると403が返ることを確認(会社閲覧のみの権限セットでは作成不可)
    def test_new_by_user_without_create_permission_returns_403(self, sample_user, auth_client):
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER)

        response = auth_client.get('/companies/new/')
        assert response.status_code == 403

    # 管理者はGETでフォームを取得できることを確認
    def test_get_returns_form(self, admin_client):
        response = admin_client.get('/companies/new/')
        assert response.status_code == 200
        assert 'form' in response.context

    # 管理者が有効なデータでPOSTすると会社が作成され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_creates_company_and_redirects(self, admin_client):
        response = admin_client.post('/companies/new/', {'name': 'サンプル株式会社'})

        company = Company.objects.get(name='サンプル株式会社')
        assert response.status_code == 302
        assert response.url == f'/companies/{company.id}/'

    # 管理者が無効なデータでPOSTするとフォームが再表示されることを確認
    def test_post_invalid_data_redisplays_form(self, admin_client):
        response = admin_client.post('/companies/new/', {'name': ''})

        assert response.status_code == 200
        assert response.context['form'].is_valid() is False


@pytest.mark.django_db
class TestCompanyEditView:

    # 編集権限が無いユーザーがアクセスすると403が返ることを確認
    def test_edit_by_user_without_permission_returns_403(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')

        response = auth_client.get(f'/companies/{company.id}/edit/')
        assert response.status_code == 403

    # 管理者が有効なデータでPOSTすると会社が更新され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_updates_company_and_redirects(self, admin_client):
        company = Company.objects.create(name='サンプル株式会社')

        response = admin_client.post(f'/companies/{company.id}/edit/', {'name': '更新後株式会社'})

        company.refresh_from_db()
        assert response.status_code == 302
        assert company.name == '更新後株式会社'

    # 存在しない会社の場合404が返ることを確認
    def test_edit_nonexistent_company_returns_404(self, admin_client):
        response = admin_client.get('/companies/9999/edit/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestCompanyDeleteView:

    # 削除権限が無いユーザーがアクセスすると403が返ることを確認
    def test_delete_by_user_without_permission_returns_403(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')

        response = auth_client.post(f'/companies/{company.id}/delete/')
        assert response.status_code == 403
        assert Company.objects.filter(id=company.id).count() == 1

    # 管理者はPOSTで削除でき、一覧ページにリダイレクトされることを確認
    def test_post_deletes_company_and_redirects_to_index(self, admin_client):
        company = Company.objects.create(name='サンプル株式会社')

        response = admin_client.post(f'/companies/{company.id}/delete/')

        assert response.status_code == 302
        assert response.url == '/companies/'
        assert Company.objects.filter(id=company.id).count() == 0

    # 存在しない会社の場合404が返ることを確認
    def test_delete_nonexistent_company_returns_404(self, admin_client):
        response = admin_client.get('/companies/9999/delete/')
        assert response.status_code == 404


def _grant(user, permission_set_id):
    company = Company.objects.create(name=f'権限セット{permission_set_id}用の会社')
    department = Department.objects.create(company=company, name='権限セット用部門')
    EmployeeDepartment.objects.create(employee=user.employee, department=department, is_primary=True)
    group = ManagementGroup.objects.create(
        name=f'test-group-{permission_set_id}-{user.username}', department=department, permission_set_id=permission_set_id
    )
    group.members.add(user)
```

- [ ] **Step 2: テストを実行し、権限チェックが無いため失敗することを確認する**

Run: `pytest app/tests/unit/views/company_test.py -v`
Expected: FAIL(権限チェックが無いため、`test_index_by_user_without_permission_is_empty`等が失敗する)

- [ ] **Step 3: `app/views/company.py`を書き換える**

```python
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from app.forms import CompanyForm
from app.models import Company
from app.permissions.access import can_create, can_delete, can_display_create_form, can_edit, can_view

MODEL_NAME = 'Company'


# 会社一覧
@login_required
def index(request):
    companies = [company for company in Company.objects.all() if can_view(request.user, MODEL_NAME, company)]
    paginator = Paginator(companies, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'app/company/index.html', {
        'companies': page_obj,
        'page_obj': page_obj,
    })


# 会社詳細
@login_required
def show(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if not can_view(request.user, MODEL_NAME, company):
        raise PermissionDenied
    return render(request, 'app/company/show.html', {'company': company})


# 会社新規作成
@login_required
def new(request):
    if not can_display_create_form(request.user, MODEL_NAME):
        raise PermissionDenied
    if request.method == 'POST':
        return _create_company(request)
    return _display_new_form(request)


# 会社編集
@login_required
def edit(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if not can_edit(request.user, MODEL_NAME, company):
        raise PermissionDenied
    if request.method == 'POST':
        return _update_company(request, company)
    return _display_edit_form(request, company)


# 会社削除
@login_required
def delete(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if not can_delete(request.user, MODEL_NAME, company):
        raise PermissionDenied
    if request.method == 'POST':
        company.delete()
        messages.success(request, '会社を削除しました。')
        return redirect('app:company_index')
    return render(request, 'app/company/delete.html', {'company': company})


# ============================================================
# ここから先はprivateヘルパー
# ============================================================


# 新規作成フォームを表示する
def _display_new_form(request):
    form = CompanyForm()
    return _render_new_form(request, form)


# 会社の新規作成処理を行う
def _create_company(request):
    form = CompanyForm(request.POST)
    if not form.is_valid():
        return _render_new_form(request, form)
    candidate = Company(**form.cleaned_data)
    if not can_create(request.user, MODEL_NAME, candidate):
        raise PermissionDenied
    company = form.save()
    messages.success(request, '会社を作成しました。')
    return redirect('app:company_show', pk=company.pk)


# 会社新規作成フォームのレンダリング
def _render_new_form(request, form):
    return render(request, 'app/company/new.html', {'form': form})


# 編集フォームを表示する
def _display_edit_form(request, company):
    form = CompanyForm(instance=company)
    return _render_edit_form(request, company, form)


# 会社の更新処理を行う
def _update_company(request, company):
    form = CompanyForm(request.POST, instance=company)
    if form.is_valid():
        form.save()
        messages.success(request, '会社情報を更新しました。')
        return redirect('app:company_show', pk=company.pk)
    return _render_edit_form(request, company, form)


# 会社編集フォームのレンダリング
def _render_edit_form(request, company, form):
    return render(request, 'app/company/edit.html', {'form': form, 'company': company})
```

- [ ] **Step 4: テストを実行し、PASSすることを確認する**

Run: `pytest app/tests/unit/views/company_test.py -v`
Expected: 全件PASS

- [ ] **Step 5: プロジェクト全体のユニットテストを実行し、回帰が無いことを確認する**

Run: `pytest app/tests/unit/ -v`
Expected: 全テストPASS

- [ ] **Step 6: コミットする**

```bash
git add app/views/company.py app/tests/unit/views/company_test.py
git commit -m "Companyビューにアクセス制御を組み込む"
```

---

### Task 6: Departmentビューにアクセス制御を組み込む

**Files:**
- Modify: `app/views/department.py`
- Modify: `app/tests/unit/views/department_test.py`

**Interfaces:**
- Consumes: `app.permissions.access.can_view/can_create/can_edit/can_delete/can_display_create_form`(Task 4)

- [ ] **Step 1: 失敗するテストを書く(既存テストを全面的に置き換える)**

`app/tests/unit/views/department_test.py`を以下の内容で置き換える。

```python
import pytest
from app.models import Company, Department, EmployeeDepartment, ManagementGroup

DEPARTMENT_VIEWER_ALL = 1
COMPANY_SCOPED_DEPARTMENT_MANAGER = 2


@pytest.mark.django_db
class TestDepartmentIndexView:

    # 未ログインの場合、ログインページにリダイレクトされることを確認
    def test_index_requires_login(self, client):
        response = client.get('/departments/')
        assert response.status_code == 302
        assert response.url.startswith('/login/')

    # 部門閲覧の権限が無いユーザーには一覧が0件になることを確認
    def test_index_by_user_without_permission_is_empty(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')
        Department.objects.create(company=company, name='開発部')

        response = auth_client.get('/departments/')
        assert response.status_code == 200
        assert len(response.context['departments']) == 0

    # 全部門閲覧を許可する権限セットを持つユーザーには会社を問わず一覧に表示されることを確認
    def test_index_by_user_with_view_all_permission(self, sample_user, auth_client):
        company = Company.objects.create(name='サンプル株式会社')
        Department.objects.create(company=company, name='開発部')
        _grant(sample_user, DEPARTMENT_VIEWER_ALL, 'テスト工業株式会社')

        response = auth_client.get('/departments/')
        assert response.status_code == 200
        assert len(response.context['departments']) == 1

    # 特定の会社に絞った権限セットを持つユーザーには、その会社の部門のみ表示されることを確認
    def test_index_by_user_with_company_scoped_permission(self, sample_user, auth_client):
        sample_company = Company.objects.create(name='サンプル株式会社')
        Department.objects.create(company=sample_company, name='開発部')
        other_company = Company.objects.create(name='別会社')
        Department.objects.create(company=other_company, name='総務部')
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER, 'サンプル株式会社')

        response = auth_client.get('/departments/')
        assert response.status_code == 200
        assert len(response.context['departments']) == 1
        assert response.context['departments'][0].company == sample_company

    # 管理者は一覧を取得できることを確認
    def test_index_by_admin_succeeds(self, admin_client):
        company = Company.objects.create(name='サンプル株式会社')
        Department.objects.create(company=company, name='開発部')

        response = admin_client.get('/departments/')
        assert response.status_code == 200
        assert len(response.context['departments']) == 1


@pytest.mark.django_db
class TestDepartmentShowView:

    # 部門閲覧の権限が無いユーザーがアクセスすると403が返ることを確認
    def test_show_by_user_without_permission_returns_403(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='開発部')

        response = auth_client.get(f'/departments/{department.id}/')
        assert response.status_code == 403

    # 存在しない部門の場合404が返ることを確認
    def test_show_nonexistent_department_returns_404(self, admin_client):
        response = admin_client.get('/departments/9999/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestDepartmentCreateView:

    # 作成権限が無いユーザーがアクセスすると403が返ることを確認
    def test_new_by_user_without_create_permission_returns_403(self, sample_user, auth_client):
        _grant(sample_user, DEPARTMENT_VIEWER_ALL, 'テスト工業株式会社')

        response = auth_client.get('/departments/new/')
        assert response.status_code == 403

    # 会社を絞った作成権限を持つユーザーはGETでフォームを取得できることを確認
    def test_get_returns_form(self, sample_user, auth_client):
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER, 'サンプル株式会社')

        response = auth_client.get('/departments/new/')
        assert response.status_code == 200
        assert 'form' in response.context

    # 権限の対象範囲内の会社であれば作成でき詳細ページにリダイレクトされることを確認
    def test_post_within_scope_creates_department_and_redirects(self, sample_user, auth_client):
        sample_company = Company.objects.create(name='サンプル株式会社')
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER, 'サンプル株式会社')

        response = auth_client.post('/departments/new/', {'company': sample_company.id, 'name': '新部門'})

        department = Department.objects.get(name='新部門')
        assert response.status_code == 302
        assert response.url == f'/departments/{department.id}/'

    # 権限の対象範囲外の会社を指定すると403が返ることを確認
    def test_post_outside_scope_returns_403(self, sample_user, auth_client):
        other_company = Company.objects.create(name='別会社')
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER, 'サンプル株式会社')

        response = auth_client.post('/departments/new/', {'company': other_company.id, 'name': '新部門'})

        assert response.status_code == 403
        assert Department.objects.filter(name='新部門').count() == 0

    # 管理者が無効なデータでPOSTするとフォームが再表示されることを確認
    def test_post_invalid_data_redisplays_form(self, admin_client):
        response = admin_client.post('/departments/new/', {'company': '', 'name': ''})

        assert response.status_code == 200
        assert response.context['form'].is_valid() is False


@pytest.mark.django_db
class TestDepartmentEditView:

    # 編集権限が無いユーザーがアクセスすると403が返ることを確認
    def test_edit_by_user_without_permission_returns_403(self, auth_client):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='開発部')

        response = auth_client.get(f'/departments/{department.id}/edit/')
        assert response.status_code == 403

    # 対象範囲内の部門であれば編集でき詳細ページにリダイレクトされることを確認
    def test_post_within_scope_updates_department_and_redirects(self, sample_user, auth_client):
        sample_company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=sample_company, name='開発部')
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER, 'サンプル株式会社')

        response = auth_client.post(f'/departments/{department.id}/edit/', {
            'company': sample_company.id, 'name': '更新後部門',
        })

        department.refresh_from_db()
        assert response.status_code == 302
        assert department.name == '更新後部門'

    # 存在しない部門の場合404が返ることを確認
    def test_edit_nonexistent_department_returns_404(self, admin_client):
        response = admin_client.get('/departments/9999/edit/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestDepartmentDeleteView:

    # company_scoped_department_managerは削除を明示的にdenyしているため、403が返ることを確認
    def test_delete_by_user_with_explicit_deny_rule_returns_403(self, sample_user, auth_client):
        sample_company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=sample_company, name='開発部')
        _grant(sample_user, COMPANY_SCOPED_DEPARTMENT_MANAGER, 'サンプル株式会社')

        response = auth_client.post(f'/departments/{department.id}/delete/')

        assert response.status_code == 403
        assert Department.objects.filter(id=department.id).count() == 1

    # 管理者はPOSTで削除でき、一覧ページにリダイレクトされることを確認
    def test_post_deletes_department_and_redirects_to_index(self, admin_client):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='開発部')

        response = admin_client.post(f'/departments/{department.id}/delete/')

        assert response.status_code == 302
        assert response.url == '/departments/'
        assert Department.objects.filter(id=department.id).count() == 0


def _grant(user, permission_set_id, anchor_company_name):
    company, _ = Company.objects.get_or_create(name=anchor_company_name)
    department = Department.objects.create(company=company, name=f'権限セット{permission_set_id}用部門')
    EmployeeDepartment.objects.create(employee=user.employee, department=department, is_primary=True)
    group = ManagementGroup.objects.create(
        name=f'test-group-{permission_set_id}-{user.username}', department=department, permission_set_id=permission_set_id
    )
    group.members.add(user)
```

- [ ] **Step 2: テストを実行し、権限チェックが無いため失敗することを確認する**

Run: `pytest app/tests/unit/views/department_test.py -v`
Expected: FAIL

- [ ] **Step 3: `app/views/department.py`を書き換える**

```python
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from app.forms import DepartmentForm
from app.models import Department
from app.permissions.access import can_create, can_delete, can_display_create_form, can_edit, can_view

MODEL_NAME = 'Department'


# 部門一覧
@login_required
def index(request):
    departments_qs = Department.objects.select_related('company').all()
    departments = [department for department in departments_qs if can_view(request.user, MODEL_NAME, department)]
    paginator = Paginator(departments, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'app/department/index.html', {
        'departments': page_obj,
        'page_obj': page_obj,
    })


# 部門詳細
@login_required
def show(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if not can_view(request.user, MODEL_NAME, department):
        raise PermissionDenied
    return render(request, 'app/department/show.html', {'department': department})


# 部門新規作成
@login_required
def new(request):
    if not can_display_create_form(request.user, MODEL_NAME):
        raise PermissionDenied
    if request.method == 'POST':
        return _create_department(request)
    return _display_new_form(request)


# 部門編集
@login_required
def edit(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if not can_edit(request.user, MODEL_NAME, department):
        raise PermissionDenied
    if request.method == 'POST':
        return _update_department(request, department)
    return _display_edit_form(request, department)


# 部門削除
@login_required
def delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if not can_delete(request.user, MODEL_NAME, department):
        raise PermissionDenied
    if request.method == 'POST':
        department.delete()
        messages.success(request, '部門を削除しました。')
        return redirect('app:department_index')
    return render(request, 'app/department/delete.html', {'department': department})


# ============================================================
# ここから先はprivateヘルパー
# ============================================================


# 新規作成フォームを表示する
def _display_new_form(request):
    form = DepartmentForm()
    return _render_new_form(request, form)


# 部門の新規作成処理を行う
def _create_department(request):
    form = DepartmentForm(request.POST)
    if not form.is_valid():
        return _render_new_form(request, form)
    candidate = Department(**form.cleaned_data)
    if not can_create(request.user, MODEL_NAME, candidate):
        raise PermissionDenied
    department = form.save()
    messages.success(request, '部門を作成しました。')
    return redirect('app:department_show', pk=department.pk)


# 部門新規作成フォームのレンダリング
def _render_new_form(request, form):
    return render(request, 'app/department/new.html', {'form': form})


# 編集フォームを表示する
def _display_edit_form(request, department):
    form = DepartmentForm(instance=department)
    return _render_edit_form(request, department, form)


# 部門の更新処理を行う
def _update_department(request, department):
    form = DepartmentForm(request.POST, instance=department)
    if form.is_valid():
        form.save()
        messages.success(request, '部門情報を更新しました。')
        return redirect('app:department_show', pk=department.pk)
    return _render_edit_form(request, department, form)


# 部門編集フォームのレンダリング
def _render_edit_form(request, department, form):
    return render(request, 'app/department/edit.html', {'form': form, 'department': department})
```

- [ ] **Step 4: テストを実行し、PASSすることを確認する**

Run: `pytest app/tests/unit/views/department_test.py -v`
Expected: 全件PASS

- [ ] **Step 5: プロジェクト全体のユニットテストを実行し、回帰が無いことを確認する**

Run: `pytest app/tests/unit/ -v`
Expected: 全テストPASS

- [ ] **Step 6: コミットする**

```bash
git add app/views/department.py app/tests/unit/views/department_test.py
git commit -m "Departmentビューにアクセス制御を組み込む"
```

---

### Task 7: Employeeビューにアクセス制御を組み込む

**Files:**
- Modify: `app/views/employee.py`
- Modify: `app/tests/unit/views/employee_test.py`

**Interfaces:**
- Consumes: `app.permissions.access.can_view/can_create/can_edit/can_delete/can_display_create_form`(Task 4)

- [ ] **Step 1: 失敗するテストを書く(既存テストを全面的に置き換える)**

`app/tests/unit/views/employee_test.py`を以下の内容で置き換える。今回用意した2つの例示ルールセット(`department_viewer_all`/`company_scoped_department_manager`)はいずれもEmployeeモデルへのルールを含まないため、`is_admin`グループ以外はEmployeeへの操作が常にdenyになる(`app/permissions/rule_sets/`にEmployeeを対象とするルールが無い場合の挙動)。

```python
import pytest
from app.models import Company, Department, EmployeeDepartment, ManagementGroup

DEPARTMENT_VIEWER_ALL = 1


@pytest.mark.django_db
class TestEmployeeIndexView:

    # 未ログインの場合、ログインページにリダイレクトされることを確認
    def test_index_requires_login(self, client):
        response = client.get('/employees/')
        assert response.status_code == 302
        assert response.url.startswith('/login/')

    # Employeeを対象とするルールを持たない権限セットのユーザーには一覧が0件になることを確認
    def test_index_by_user_without_permission_is_empty(self, sample_user, other_user, auth_client):
        _grant(sample_user, DEPARTMENT_VIEWER_ALL)

        response = auth_client.get('/employees/')
        assert response.status_code == 200
        assert len(response.context['employees']) == 0

    # 管理者は一覧を取得できることを確認
    def test_index_by_admin_succeeds(self, admin_client, sample_user):
        response = admin_client.get('/employees/')
        assert response.status_code == 200
        assert len(response.context['employees']) >= 1


@pytest.mark.django_db
class TestEmployeeShowView:

    # 閲覧権限が無いユーザーがアクセスすると403が返ることを確認
    def test_show_by_user_without_permission_returns_403(self, sample_user, other_user, auth_client):
        _grant(sample_user, DEPARTMENT_VIEWER_ALL)

        response = auth_client.get(f'/employees/{other_user.employee.id}/')
        assert response.status_code == 403

    # 管理者は詳細を取得できることを確認
    def test_show_by_admin_succeeds(self, admin_client, sample_user):
        response = admin_client.get(f'/employees/{sample_user.employee.id}/')
        assert response.status_code == 200
        assert response.context['employee'] == sample_user.employee

    # 存在しない社員の場合404が返ることを確認
    def test_show_nonexistent_employee_returns_404(self, admin_client):
        response = admin_client.get('/employees/9999/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestEmployeeCreateView:

    # 作成権限が無いユーザーがアクセスすると403が返ることを確認
    def test_new_by_user_without_create_permission_returns_403(self, sample_user, auth_client):
        _grant(sample_user, DEPARTMENT_VIEWER_ALL)

        response = auth_client.get('/employees/new/')
        assert response.status_code == 403

    # 管理者はGETでフォームを取得できることを確認
    def test_get_returns_form(self, admin_client):
        response = admin_client.get('/employees/new/')
        assert response.status_code == 200
        assert 'form' in response.context

    # 管理者が有効なデータでPOSTすると社員が作成され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_creates_employee_and_redirects(self, admin_client):
        response = admin_client.post('/employees/new/', {
            'employee_number': 'E0099', 'last_name': '山田', 'first_name': '太郎', 'password': 'password123',
        })

        from app.models import Employee
        employee = Employee.objects.get(employee_number='E0099')
        assert response.status_code == 302
        assert response.url == f'/employees/{employee.id}/'


@pytest.mark.django_db
class TestEmployeeEditView:

    # 編集権限が無いユーザーがアクセスすると403が返ることを確認
    def test_edit_by_user_without_permission_returns_403(self, sample_user, other_user, auth_client):
        _grant(sample_user, DEPARTMENT_VIEWER_ALL)

        response = auth_client.get(f'/employees/{other_user.employee.id}/edit/')
        assert response.status_code == 403

    # 存在しない社員の場合404が返ることを確認
    def test_edit_nonexistent_employee_returns_404(self, admin_client):
        response = admin_client.get('/employees/9999/edit/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestEmployeeDeleteView:

    # 削除権限が無いユーザーがアクセスすると403が返ることを確認
    def test_delete_by_user_without_permission_returns_403(self, sample_user, other_user, auth_client):
        _grant(sample_user, DEPARTMENT_VIEWER_ALL)

        response = auth_client.post(f'/employees/{other_user.employee.id}/delete/')
        assert response.status_code == 403

    # 管理者はPOSTで削除でき、一覧ページにリダイレクトされることを確認
    def test_post_deletes_employee_and_redirects_to_index(self, admin_client, other_user):
        response = admin_client.post(f'/employees/{other_user.employee.id}/delete/')

        assert response.status_code == 302
        assert response.url == '/employees/'


def _grant(user, permission_set_id):
    company = Company.objects.create(name=f'権限セット{permission_set_id}用の会社')
    department = Department.objects.create(company=company, name='権限セット用部門')
    EmployeeDepartment.objects.create(employee=user.employee, department=department, is_primary=True)
    group = ManagementGroup.objects.create(
        name=f'test-group-{permission_set_id}-{user.username}', department=department, permission_set_id=permission_set_id
    )
    group.members.add(user)
```

- [ ] **Step 2: テストを実行し、権限チェックが無いため失敗することを確認する**

Run: `pytest app/tests/unit/views/employee_test.py -v`
Expected: FAIL

- [ ] **Step 3: `app/views/employee.py`を書き換える**

```python
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from app.forms import EmployeeForm
from app.models import Employee
from app.permissions.access import can_create, can_delete, can_display_create_form, can_edit, can_view

MODEL_NAME = 'Employee'


# 社員一覧
@login_required
def index(request):
    employees_qs = Employee.objects.select_related('user').all()
    employees = [employee for employee in employees_qs if can_view(request.user, MODEL_NAME, employee)]
    paginator = Paginator(employees, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'app/employee/index.html', {
        'employees': page_obj,
        'page_obj': page_obj,
    })


# 社員詳細
@login_required
def show(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if not can_view(request.user, MODEL_NAME, employee):
        raise PermissionDenied
    return render(request, 'app/employee/show.html', {'employee': employee})


# 社員新規作成
@login_required
def new(request):
    if not can_display_create_form(request.user, MODEL_NAME):
        raise PermissionDenied
    if request.method == 'POST':
        return _create_employee(request)
    return _display_new_form(request)


# 社員編集
@login_required
def edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if not can_edit(request.user, MODEL_NAME, employee):
        raise PermissionDenied
    if request.method == 'POST':
        return _update_employee(request, employee)
    return _display_edit_form(request, employee)


# 社員削除
@login_required
def delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if not can_delete(request.user, MODEL_NAME, employee):
        raise PermissionDenied
    if request.method == 'POST':
        employee.user.delete()
        messages.success(request, '社員情報を削除しました。')
        return redirect('app:employee_index')
    return render(request, 'app/employee/delete.html', {'employee': employee})


# ============================================================
# ここから先はprivateヘルパー
# ============================================================


# 新規作成フォームを表示する
def _display_new_form(request):
    form = EmployeeForm()
    return _render_new_form(request, form)


# 社員の新規作成処理を行う(UserとEmployeeを同時作成)
def _create_employee(request):
    form = EmployeeForm(request.POST)
    if not form.is_valid():
        return _render_new_form(request, form)
    candidate = Employee(employee_number=form.cleaned_data['employee_number'])
    if not can_create(request.user, MODEL_NAME, candidate):
        raise PermissionDenied
    employee = form.save()
    messages.success(request, '社員を登録しました。')
    return redirect('app:employee_show', pk=employee.pk)


# 社員新規作成フォームのレンダリング
def _render_new_form(request, form):
    return render(request, 'app/employee/new.html', {'form': form})


# 編集フォームを表示する
def _display_edit_form(request, employee):
    form = EmployeeForm(instance=employee)
    return _render_edit_form(request, employee, form)


# 社員の更新処理を行う
def _update_employee(request, employee):
    form = EmployeeForm(request.POST, instance=employee)
    if form.is_valid():
        form.save()
        messages.success(request, '社員情報を更新しました。')
        return redirect('app:employee_show', pk=employee.pk)
    return _render_edit_form(request, employee, form)


# 社員編集フォームのレンダリング
def _render_edit_form(request, employee, form):
    return render(request, 'app/employee/edit.html', {'form': form, 'employee': employee})
```

- [ ] **Step 4: テストを実行し、PASSすることを確認する**

Run: `pytest app/tests/unit/views/employee_test.py -v`
Expected: 全件PASS

- [ ] **Step 5: プロジェクト全体のユニットテストを実行し、回帰が無いことを確認する**

Run: `pytest app/tests/unit/ -v`
Expected: 全テストPASS

- [ ] **Step 6: コミットする**

```bash
git add app/views/employee.py app/tests/unit/views/employee_test.py
git commit -m "Employeeビューにアクセス制御を組み込む"
```

---

### Task 8: シードデータを更新し、最終回帰を確認する

**Files:**
- Modify: `app/seeds/management_group.py`

- [ ] **Step 1: `app/seeds/management_group.py`に非管理者の権限セットを持つグループのシードデータを追加する**

既存の2グループ(全社管理者)はそのまま残し、末尾に非管理者グループを追加する。`company_scoped_department_manager`(ID=2)はE0002を、`department_viewer_all`(ID=1)もE0002を兼務として割り当てる(E0002は既に`app/seeds/employee_department.py`で開発部を兼務している)。

```python
from django.contrib.auth.models import User
from app.models import Department, ManagementGroup


# 管理グループのシードデータを作成する
def create():
    hr_group = ManagementGroup.objects.create(name='人事部', is_admin=True)
    hr_group.members.set(User.objects.filter(username='E0001'))

    dev_group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)
    dev_group.members.set(User.objects.filter(username='E0002'))

    # 権限セットの動作確認用(サンプル株式会社の部門のみ閲覧・編集できる)
    sample_department = Department.objects.get(company__name='サンプル株式会社', name='開発部')
    department_manager_group = ManagementGroup.objects.create(
        name='サンプル株式会社 部門管理者', department=sample_department, permission_set_id=2,
    )
    department_manager_group.members.set(User.objects.filter(username='E0002'))
```

- [ ] **Step 2: `app/management/commands/seed_database.py`の呼び出し順序を確認する**

`app/seeds/management_group.py`の`create()`は`app/seeds/department.py`の`create()`より後に呼ぶ必要がある(部門データを参照するため)。`app/management/commands/seed_database.py`の現在の呼び出し順序を確認する。

Run: `cat app/management/commands/seed_database.py`
Expected: `seeds.employee.create()` → `seeds.management_group.create()` → `seeds.company.create()` → `seeds.department.create()` の順になっている場合、`management_group`が`department`より先に呼ばれているため、`handle()`内の呼び出し順序を以下のように書き換える。

```python
    def handle(self, *_args, **_options):
        seeds.employee.create()
        seeds.company.create()
        seeds.department.create()
        seeds.management_group.create()
        seeds.employee_department.create()
```

- [ ] **Step 3: シードデータを投入して動作確認する**

Run: `python manage.py reset_database --seed --noinput`
Expected: エラーなくシードデータが投入される

- [ ] **Step 4: プロジェクト全体のユニットテストを実行し、全件PASSすることを確認する**

Run: `pytest app/tests/unit/ -v`
Expected: 全テストPASS

- [ ] **Step 5: コミットする**

```bash
git add app/seeds/management_group.py app/management/commands/seed_database.py
git commit -m "権限セットの動作確認用シードデータを追加する"
```

---

## 完了条件

- `pytest app/tests/unit/ -v` が全件PASSする
- `app/views/company.py`/`department.py`/`employee.py`に残っていた12件のTODOコメントがすべて解消されている
- `python manage.py makemigrations --check --dry-run`でモデル定義とマイグレーションのズレが無いことを確認済み
- カラム権限(フィールド単位)のテンプレート・フォームへの組み込み、`execute`アクションの具体的な業務操作は本プランのスコープ外(`docs/superpowers/specs/2026-08-08-access-control-design.md`「今後の課題」を参照)
