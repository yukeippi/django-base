# 社員権限モデル(ロール決定ロジック) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ログインした社員に、どの`ManagementGroup`(管理グループ)が適用されるかを決定するロール決定ロジックを実装する。

**Architecture:** 権限判定専用の部門階層モデル`DepartmentHierarchy`を新設し、`ManagementGroup`に`is_admin`(全社管理者フラグ)と`department`(割当部門)を追加する。適用判定は`app/lib/permissions.py`にライブラリ関数`get_applicable_management_groups(user)`として実装し、既存の`is_admin()`/`can_edit_task()`と同じ置き場所・パターンに揃える。

**Tech Stack:** Django 6.0 (Model, ModelForm), pytest-django (unit test)

参照仕様書: `docs/superpowers/specs/2026-08-04-employee-permission-model-design.md`

## Global Constraints

- クリーンロジック(`clean()`)を持つモデルは`save()`をオーバーライドして`self.full_clean()`を必ず呼ぶ(`.claude/instructions.md` Model Validation Rules)
- 部門の親子関係は同一`Company`内に閉じる(会社をまたいだ親子関係は不正)
- 1人の社員が複数の`ManagementGroup`に同時に所属してよく、複数の`ManagementGroup`が同時に適用されてもよい(1人1グループには制限しない)
- `ManagementGroup.is_admin=True`のグループは`department`を`NULL`にする。`is_admin=False`のグループは`department`必須
- `DepartmentHierarchy`は全ての`Department`がレコードを持つ必要はない(既存アプリからの移行データを許容するため)。レコードが無い部門は「親・兄弟なし(自分自身のみ判定対象)」として扱う
- 「親・兄弟」の判定は1階層のみ(祖父母部門・孫部門は対象外)
- テストは既存のレイヤー分割(`app/tests/unit/models/`, `app/tests/unit/forms/`, `app/tests/unit/lib/`)に従う
- コミットメッセージに`Co-Authored-By: Claude ...`のようなAI署名のトレーラーは含めない
- 本設計は「アクセス制御(権限が及ぶ範囲)」を対象外とする。`get_applicable_management_groups()`の呼び出し元(各ビューへの組み込み)は本プランでは実装しない

---

### Task 1: `DepartmentHierarchy`モデルを追加する

**Files:**
- Create: `app/models/department_hierarchy.py`
- Modify: `app/models/__init__.py`
- Test: `app/tests/unit/models/department_hierarchy_test.py`
- Migration: `app/migrations/`配下に新規ファイルが自動生成される

**Interfaces:**
- Produces: `app.models.DepartmentHierarchy`(`department`: `Department`への`OneToOneField`, `parent_department`: `Department`への`ForeignKey`, null許可)。Task 3で`get_applicable_management_groups()`から利用する。

- [ ] **Step 1: 失敗するテストを書く**

`app/tests/unit/models/department_hierarchy_test.py`を新規作成する。

```python
import pytest
from django.core.exceptions import ValidationError
from app.models import Company, Department, DepartmentHierarchy


# DepartmentHierarchyモデルのテストクラス
@pytest.mark.django_db
class TestDepartmentHierarchyModel:

    # 親部門を指定して作成できることを確認
    def test_create_with_parent(self):
        company = Company.objects.create(name='サンプル株式会社')
        parent = Department.objects.create(company=company, name='本社')
        child = Department.objects.create(company=company, name='営業部')

        hierarchy = DepartmentHierarchy.objects.create(department=child, parent_department=parent)

        assert hierarchy.id is not None
        assert hierarchy.department == child
        assert hierarchy.parent_department == parent

    # 親部門なし(最上位の部門)で作成できることを確認
    def test_create_without_parent(self):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='本社')

        hierarchy = DepartmentHierarchy.objects.create(department=department)

        assert hierarchy.id is not None
        assert hierarchy.parent_department is None

    # 親部門が別の会社に属している場合はエラーになることを確認
    def test_parent_must_be_same_company(self):
        company_a = Company.objects.create(name='A株式会社')
        company_b = Company.objects.create(name='B株式会社')
        department = Department.objects.create(company=company_a, name='営業部')
        other_company_department = Department.objects.create(company=company_b, name='本社')

        with pytest.raises(ValidationError):
            DepartmentHierarchy.objects.create(department=department, parent_department=other_company_department)

    # 同じ部門で2件目のレコードを作成しようとするとエラーになることを確認(1部門につき1レコード)
    def test_department_must_be_unique(self):
        company = Company.objects.create(name='サンプル株式会社')
        department = Department.objects.create(company=company, name='営業部')
        DepartmentHierarchy.objects.create(department=department)

        with pytest.raises(ValidationError):
            DepartmentHierarchy.objects.create(department=department)

    # __str__が「部門 (親: 親部門)」の形式を返すことを確認
    def test_str_includes_department_and_parent(self):
        company = Company.objects.create(name='サンプル株式会社')
        parent = Department.objects.create(company=company, name='本社')
        child = Department.objects.create(company=company, name='営業部')
        hierarchy = DepartmentHierarchy.objects.create(department=child, parent_department=parent)

        assert str(hierarchy) == f'{child} (親: {parent})'
```

- [ ] **Step 2: テストを実行し、`DepartmentHierarchy`が存在せず失敗することを確認する**

Run: `pytest app/tests/unit/models/department_hierarchy_test.py -v`
Expected: FAIL(`ImportError: cannot import name 'DepartmentHierarchy'`)

- [ ] **Step 3: `app/models/department_hierarchy.py`を作成する**

```python
from django.core.exceptions import ValidationError
from django.db import models
from app.models.department import Department


# 権限判定用の部門階層(親部門)を表すモデル。全ての部門がレコードを持つ必要はない
class DepartmentHierarchy(models.Model):
    department = models.OneToOneField(
        Department, on_delete=models.CASCADE, related_name='hierarchy', verbose_name='部門'
    )
    parent_department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.CASCADE,
        related_name='child_hierarchies', verbose_name='親部門'
    )

    class Meta:
        verbose_name = '部門階層'
        verbose_name_plural = '部門階層'

    def __str__(self):
        return f'{self.department} (親: {self.parent_department})'

    # 親部門は同じ会社に属していなければならない
    def clean(self):
        if self.parent_department and self.parent_department.company_id != self.department.company_id:
            raise ValidationError('親部門は同じ会社に属している必要があります。')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
```

- [ ] **Step 4: `app/models/__init__.py`に追加する**

```python
from .task import Task
from .company import Company
from .department import Department
from .department_hierarchy import DepartmentHierarchy
from .employee import Employee
from .employee_department import EmployeeDepartment
from .management_group import ManagementGroup

__all__ = [
    'Task', 'Company', 'Department', 'DepartmentHierarchy', 'Employee', 'EmployeeDepartment', 'ManagementGroup',
]
```

- [ ] **Step 5: マイグレーションを作成し、適用する**

Run: `python manage.py makemigrations`
Expected: `app/migrations/`配下に`DepartmentHierarchy`の`CreateModel`のみを含む新規マイグレーションファイルが生成される(例: `0009_departmenthierarchy.py`。実際のファイル名は`ls app/migrations/`で確認する)

Run: `python manage.py migrate`
Expected: マイグレーションが正常に適用される

- [ ] **Step 6: テストを実行し、PASSすることを確認する**

Run: `pytest app/tests/unit/models/department_hierarchy_test.py -v`
Expected: 5件PASS

- [ ] **Step 7: コミットする**

```bash
git add app/models/department_hierarchy.py app/models/__init__.py app/migrations/ app/tests/unit/models/department_hierarchy_test.py
git commit -m "DepartmentHierarchyモデルを追加し、権限判定用の部門階層を管理できるようにする"
```

---

### Task 2: `ManagementGroup`に`is_admin`/`department`を追加する

**Files:**
- Modify: `app/models/management_group.py`
- Modify: `app/forms/management_group.py`
- Modify: `app/templates/app/management_group/_form.html`
- Modify: `app/seeds/management_group.py`
- Modify: `app/tests/unit/models/management_group_test.py`
- Modify: `app/tests/unit/forms/management_group_test.py`
- Modify: `app/tests/unit/views/management_group_test.py`
- Migration: `app/migrations/`配下に新規ファイルが自動生成される

**Interfaces:**
- Consumes: `app.models.Department`(既存)
- Produces: `ManagementGroup.is_admin`(`BooleanField`, default `False`)、`ManagementGroup.department`(`Department`への`ForeignKey`, null許可)。Task 3で`get_applicable_management_groups()`から利用する。

- [ ] **Step 1: モデルテストを新しい仕様に合わせて書き換える(失敗させる)**

`app/tests/unit/models/management_group_test.py`を以下の内容で置き換える。

```python
import pytest
from django.core.exceptions import ValidationError
from app.models import Company, Department, ManagementGroup


# ManagementGroupモデルのテストクラス
@pytest.mark.django_db
class TestManagementGroupModel:

    # is_admin=Trueなら部門なしでグループを作成できることを確認
    def test_create_admin_group_without_department(self):
        group = ManagementGroup.objects.create(name='全社管理者グループ', is_admin=True)

        assert group.id is not None
        assert group.name == '全社管理者グループ'
        assert group.department is None

    # is_admin=Falseの場合は部門を指定してグループを作成できることを確認
    def test_create_non_admin_group_with_department(self):
        department = _create_department('開発部')

        group = ManagementGroup.objects.create(name='開発部管理グループ', department=department)

        assert group.id is not None
        assert group.is_admin is False
        assert group.department == department

    # is_admin=Falseなのに部門が未設定の場合はエラーになることを確認
    def test_department_required_when_not_admin(self):
        with pytest.raises(ValidationError):
            ManagementGroup.objects.create(name='不正なグループ')

    # is_admin=Trueなのに部門が設定されている場合はエラーになることを確認
    def test_department_forbidden_when_admin(self):
        department = _create_department('開発部')

        with pytest.raises(ValidationError):
            ManagementGroup.objects.create(name='不正なグループ', is_admin=True, department=department)

    # 名前が重複する場合はエラーになることを確認
    def test_name_must_be_unique(self):
        ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        with pytest.raises(ValidationError):
            ManagementGroup.objects.create(name='開発チーム', is_admin=True)

    # メンバーを複数のユーザーで構成できることを確認
    def test_members_can_have_multiple_users(self, sample_user, other_user):
        group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)
        group.members.add(sample_user, other_user)

        assert group.members.count() == 2

    # __str__が名前を返すことを確認
    def test_str_returns_name(self):
        group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        assert str(group) == '開発チーム'


def _create_department(name):
    company = Company.objects.create(name=f'{name}の会社')
    return Department.objects.create(company=company, name=name)
```

- [ ] **Step 2: テストを実行し、失敗することを確認する**

Run: `pytest app/tests/unit/models/management_group_test.py -v`
Expected: FAIL(`is_admin`/`department`が未知のキーワード引数のため`TypeError`、または`ValidationError`が発生せず失敗するテストが混在する)

- [ ] **Step 3: `app/models/management_group.py`を書き換える**

```python
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from app.models.department import Department


# ユーザーをグループ化し、権限を付与するためのモデル
class ManagementGroup(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='管理グループ名')
    members = models.ManyToManyField(User, related_name='management_groups', blank=True, verbose_name='メンバー')
    is_admin = models.BooleanField(default=False, verbose_name='全社管理者')
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.CASCADE,
        related_name='management_groups', verbose_name='割当部門'
    )

    class Meta:
        ordering = ['name']
        verbose_name = '管理グループ'
        verbose_name_plural = '管理グループ'

    def __str__(self):
        return self.name

    # is_adminと部門設定の整合性を検証する(全社管理者は部門を持たず、それ以外は部門必須)
    def clean(self):
        if self.is_admin and self.department_id is not None:
            raise ValidationError('全社管理者グループには部門を設定できません。')
        if not self.is_admin and self.department_id is None:
            raise ValidationError('全社管理者でない場合は部門の設定が必須です。')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
```

- [ ] **Step 4: マイグレーションを作成し、適用する**

Run: `python manage.py makemigrations`
Expected: `is_admin`/`department`の`AddField`を含む新規マイグレーションファイルが生成される(例: `0010_managementgroup_department_managementgroup_is_admin.py`。実際のファイル名は`ls app/migrations/`で確認する)

補足: `ManagementGroup`を定義した既存の`0005_managementgroup.py`は`Department`モデル追加前(`0007_department.py`より前)のマイグレーションのため、今回のフィールド追加をそこに統合すると`0005`が`0007`に依存する逆転した依存関係になってしまう。そのため今回は統合せず、新規マイグレーションファイルのまま残す。

Run: `python manage.py migrate`
Expected: マイグレーションが正常に適用される

- [ ] **Step 5: モデルテストを実行し、PASSすることを確認する**

Run: `pytest app/tests/unit/models/management_group_test.py -v`
Expected: 7件PASS

- [ ] **Step 6: フォームテストを新しい仕様に合わせて書き換える(失敗させる)**

`app/tests/unit/forms/management_group_test.py`を以下の内容で置き換える。

```python
import pytest
from app.forms.management_group import ManagementGroupForm


# ManagementGroupFormのテストクラス
@pytest.mark.django_db
class TestManagementGroupForm:

    # 全社管理者として有効なデータでフォームが妥当と判定されることを確認
    def test_valid_data_is_valid(self, sample_user):
        form = ManagementGroupForm(data={
            'name': '開発チーム',
            'members': [sample_user.id],
            'is_admin': True,
        })
        assert form.is_valid()

    # 名前が空の場合、フォームが無効と判定されることを確認
    def test_blank_name_is_invalid(self):
        form = ManagementGroupForm(data={
            'name': '',
            'members': [],
            'is_admin': True,
        })
        assert not form.is_valid()
        assert 'name' in form.errors

    # メンバー未選択でも妥当と判定されることを確認(members=blank許可)
    def test_no_members_is_valid(self):
        form = ManagementGroupForm(data={
            'name': '開発チーム',
            'members': [],
            'is_admin': True,
        })
        assert form.is_valid()

    # 全社管理者でないのに部門が未指定の場合、フォームが無効と判定されることを確認
    def test_department_required_when_not_admin(self):
        form = ManagementGroupForm(data={
            'name': '開発チーム',
            'members': [],
            'is_admin': False,
        })
        assert not form.is_valid()

    # saveすると指定したメンバーが設定されることを確認
    def test_save_sets_members(self, sample_user, other_user):
        form = ManagementGroupForm(data={
            'name': '開発チーム',
            'members': [sample_user.id, other_user.id],
            'is_admin': True,
        })
        assert form.is_valid()

        group = form.save()

        assert group.members.count() == 2
```

- [ ] **Step 7: フォームテストを実行し、失敗することを確認する**

Run: `pytest app/tests/unit/forms/management_group_test.py -v`
Expected: FAIL(`ManagementGroupForm`が`is_admin`フィールドを持たないため無視され、`test_department_required_when_not_admin`などが失敗する)

- [ ] **Step 8: `app/forms/management_group.py`を書き換える**

```python
from django import forms
from app.models import ManagementGroup


# 管理グループの新規作成・編集で使うフォーム
class ManagementGroupForm(forms.ModelForm):
    class Meta:
        model = ManagementGroup
        fields = ['name', 'members', 'is_admin', 'department']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'members': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'is_admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
        }
```

- [ ] **Step 9: フォームテストを実行し、PASSすることを確認する**

Run: `pytest app/tests/unit/forms/management_group_test.py -v`
Expected: 5件PASS

- [ ] **Step 10: `app/templates/app/management_group/_form.html`に`is_admin`/`department`の入力欄を追加する**

`{{ form.members }}`のフィールドブロックの直後、`<button type="submit" ...>`の直前に以下を追加する。

```html
    <div class="form-field mb-3 form-check">
        {{ form.is_admin }}
        <label for="{{ form.is_admin.id_for_label }}" class="form-check-label">全社管理者</label>
        <div class="text-danger small">{{ form.is_admin.errors }}</div>
    </div>
    <div class="form-field mb-3">
        <label for="{{ form.department.id_for_label }}" class="form-label">割当部門</label>
        {{ form.department }}
        <div class="text-danger small">{{ form.department.errors }}</div>
    </div>
```

- [ ] **Step 11: ビューテストを新しい仕様に合わせて書き換える(失敗させる)**

`app/tests/unit/views/management_group_test.py`を以下の内容で置き換える。

```python
import pytest
from app.models import ManagementGroup


@pytest.mark.django_db
class TestManagementGroupIndexView:

    # 未ログインの場合、ログインページにリダイレクトされることを確認
    def test_index_requires_login(self, client):
        response = client.get('/management_groups/')
        assert response.status_code == 302
        assert response.url.startswith('/login/')

    # 管理者以外がアクセスすると403が返ることを確認
    def test_index_by_non_admin_returns_403(self, auth_client):
        response = auth_client.get('/management_groups/')
        assert response.status_code == 403

    # 管理者は一覧を取得できることを確認
    def test_index_by_admin_succeeds(self, admin_client):
        ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        response = admin_client.get('/management_groups/')
        assert response.status_code == 200
        assert len(response.context['management_groups']) == 1


@pytest.mark.django_db
class TestManagementGroupShowView:

    # 管理者以外がアクセスすると403が返ることを確認
    def test_show_by_non_admin_returns_403(self, auth_client):
        group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        response = auth_client.get(f'/management_groups/{group.id}/')
        assert response.status_code == 403

    # 管理者は詳細を取得できることを確認
    def test_show_by_admin_succeeds(self, admin_client):
        group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        response = admin_client.get(f'/management_groups/{group.id}/')
        assert response.status_code == 200
        assert response.context['management_group'] == group


@pytest.mark.django_db
class TestManagementGroupCreateView:

    # 管理者以外がアクセスすると403が返ることを確認
    def test_new_by_non_admin_returns_403(self, auth_client):
        response = auth_client.get('/management_groups/new/')
        assert response.status_code == 403

    # 管理者はGETでフォームを取得できることを確認
    def test_get_returns_form(self, admin_client):
        response = admin_client.get('/management_groups/new/')
        assert response.status_code == 200
        assert 'form' in response.context

    # 有効なデータでPOSTするとグループが作成され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_creates_group_and_redirects(self, admin_client, sample_user):
        response = admin_client.post('/management_groups/new/', {
            'name': '開発チーム',
            'members': [sample_user.id],
            'is_admin': True,
        })

        group = ManagementGroup.objects.get(name='開発チーム')
        assert response.status_code == 302
        assert response.url == f'/management_groups/{group.id}/'


@pytest.mark.django_db
class TestManagementGroupEditView:

    # 管理者以外がアクセスすると403が返ることを確認
    def test_edit_by_non_admin_returns_403(self, auth_client):
        group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        response = auth_client.get(f'/management_groups/{group.id}/edit/')
        assert response.status_code == 403

    # 有効なデータでPOSTすると更新され詳細ページにリダイレクトされることを確認
    def test_post_valid_data_updates_group_and_redirects(self, admin_client):
        group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        response = admin_client.post(f'/management_groups/{group.id}/edit/', {
            'name': '運用チーム',
            'members': [],
            'is_admin': True,
        })

        group.refresh_from_db()
        assert response.status_code == 302
        assert group.name == '運用チーム'


@pytest.mark.django_db
class TestManagementGroupDeleteView:

    # 管理者以外がアクセスすると403が返ることを確認
    def test_delete_by_non_admin_returns_403(self, auth_client):
        group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        response = auth_client.post(f'/management_groups/{group.id}/delete/')
        assert response.status_code == 403
        assert ManagementGroup.objects.filter(id=group.id).count() == 1

    # 管理者はPOSTで削除でき、一覧ページにリダイレクトされることを確認
    def test_post_deletes_group_and_redirects_to_index(self, admin_client):
        group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)

        response = admin_client.post(f'/management_groups/{group.id}/delete/')

        assert response.status_code == 302
        assert response.url == '/management_groups/'
        assert ManagementGroup.objects.filter(id=group.id).count() == 0
```

- [ ] **Step 12: ビューテストを実行し、PASSすることを確認する**

Run: `pytest app/tests/unit/views/management_group_test.py -v`
Expected: 全件PASS

- [ ] **Step 13: シードデータを修正する**

`app/seeds/management_group.py`を以下の内容で置き換える(既存の2グループを全社管理者グループとして扱う)。

```python
from django.contrib.auth.models import User
from app.models import ManagementGroup


# 管理グループのシードデータを作成する
def create():
    hr_group = ManagementGroup.objects.create(name='人事部', is_admin=True)
    hr_group.members.set(User.objects.filter(username='E0001'))

    dev_group = ManagementGroup.objects.create(name='開発チーム', is_admin=True)
    dev_group.members.set(User.objects.filter(username='E0002'))
```

- [ ] **Step 14: プロジェクト全体のユニットテストを実行し、回帰が無いことを確認する**

Run: `pytest app/tests/unit/ -v`
Expected: 全テストPASS

- [ ] **Step 15: コミットする**

```bash
git add app/models/management_group.py app/forms/management_group.py app/templates/app/management_group/_form.html \
  app/seeds/management_group.py app/migrations/ \
  app/tests/unit/models/management_group_test.py app/tests/unit/forms/management_group_test.py \
  app/tests/unit/views/management_group_test.py
git commit -m "ManagementGroupにis_admin/departmentを追加し、全社管理者か部門割当のいずれかを必須にする"
```

---

### Task 3: `get_applicable_management_groups()`を実装する

**Files:**
- Modify: `app/lib/permissions.py`
- Test: `app/tests/unit/lib/permissions_test.py`

**Interfaces:**
- Consumes: `app.models.ManagementGroup`(`is_admin`, `department`, `members`)、`app.models.DepartmentHierarchy`(`department`, `parent_department`)(Task 1/2)、`app.models.EmployeeDepartment`(`is_primary`)(既存)
- Produces: `app.lib.permissions.get_applicable_management_groups(user) -> list[ManagementGroup]`。今後のアクセス制御実装(本プランのスコープ外)から利用される想定。

- [ ] **Step 1: 失敗するテストを書く**

`app/tests/unit/lib/permissions_test.py`の末尾に追記する(先頭のimport文も以下のように変更する)。

```python
import pytest
from app.lib.permissions import can_delete_task, can_edit_task, get_applicable_management_groups, is_admin
from app.models import Company, Department, DepartmentHierarchy, EmployeeDepartment, ManagementGroup, Task
```

（既存の`TestIsAdmin`/`TestCanEditTask`/`TestCanDeleteTask`はそのまま残す)

ファイル末尾に追記:

```python
@pytest.mark.django_db
class TestGetApplicableManagementGroups:

    # 主務部門そのものに割り当てられたグループがメンバーに適用されることを確認
    def test_group_assigned_to_own_department_applies(self, sample_user):
        department = _create_department('開発部')
        _set_primary_department(sample_user, department)
        group = ManagementGroup.objects.create(name='開発部グループ', department=department)
        group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == [group]

    # 親部門に割り当てられたグループがメンバーに適用されることを確認
    def test_group_assigned_to_parent_department_applies(self, sample_user):
        company = Company.objects.create(name='サンプル株式会社')
        parent = Department.objects.create(company=company, name='本社')
        child = Department.objects.create(company=company, name='営業部')
        DepartmentHierarchy.objects.create(department=child, parent_department=parent)
        _set_primary_department(sample_user, child)
        group = ManagementGroup.objects.create(name='本社グループ', department=parent)
        group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == [group]

    # 兄弟部門に割り当てられたグループがメンバーに適用されることを確認
    def test_group_assigned_to_sibling_department_applies(self, sample_user):
        company = Company.objects.create(name='サンプル株式会社')
        parent = Department.objects.create(company=company, name='本社')
        sales = Department.objects.create(company=company, name='営業部')
        hr = Department.objects.create(company=company, name='人事部')
        DepartmentHierarchy.objects.create(department=sales, parent_department=parent)
        DepartmentHierarchy.objects.create(department=hr, parent_department=parent)
        _set_primary_department(sample_user, sales)
        group = ManagementGroup.objects.create(name='人事部グループ', department=hr)
        group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == [group]

    # 親・兄弟のいずれにも該当しない部門のグループは適用されないことを確認
    def test_unrelated_department_group_does_not_apply(self, sample_user):
        company = Company.objects.create(name='サンプル株式会社')
        own_department = Department.objects.create(company=company, name='開発部')
        unrelated_department = Department.objects.create(company=company, name='総務部')
        _set_primary_department(sample_user, own_department)
        group = ManagementGroup.objects.create(name='総務部グループ', department=unrelated_department)
        group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == []

    # is_admin=Trueのグループはメンバーであれば部門に関係なく適用されることを確認
    def test_admin_group_applies_regardless_of_department(self, sample_user):
        group = ManagementGroup.objects.create(name='全社管理者グループ', is_admin=True)
        group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == [group]

    # メンバーでなければ、部門が一致していても適用されないことを確認
    def test_non_member_does_not_get_group_applied(self, sample_user):
        department = _create_department('開発部')
        _set_primary_department(sample_user, department)
        ManagementGroup.objects.create(name='開発部グループ', department=department)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == []

    # 主務部門が無い社員には、is_admin以外のグループが適用されないことを確認
    def test_employee_without_primary_department_only_gets_admin_groups(self, sample_user):
        department = _create_department('開発部')
        non_admin_group = ManagementGroup.objects.create(name='開発部グループ', department=department)
        non_admin_group.members.add(sample_user)
        admin_group = ManagementGroup.objects.create(name='全社管理者グループ', is_admin=True)
        admin_group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == [admin_group]

    # Employeeが無いユーザーには、is_admin以外のグループが適用されないことを確認
    def test_user_without_employee_only_gets_admin_groups(self, admin_user):
        department = _create_department('開発部')
        non_admin_group = ManagementGroup.objects.create(name='開発部グループ', department=department)
        non_admin_group.members.add(admin_user)
        admin_group = ManagementGroup.objects.create(name='全社管理者グループ', is_admin=True)
        admin_group.members.add(admin_user)

        applicable = get_applicable_management_groups(admin_user)

        assert applicable == [admin_group]

    # 複数のグループが同時に適用されるケースを確認
    def test_multiple_groups_can_apply_simultaneously(self, sample_user):
        department = _create_department('開発部')
        _set_primary_department(sample_user, department)
        own_group = ManagementGroup.objects.create(name='開発部グループ', department=department)
        own_group.members.add(sample_user)
        admin_group = ManagementGroup.objects.create(name='全社管理者グループ', is_admin=True)
        admin_group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert set(applicable) == {own_group, admin_group}

    # 部門階層にレコードが無い場合は自分自身のみ判定されることを確認
    def test_department_without_hierarchy_record_only_matches_self(self, sample_user):
        company = Company.objects.create(name='サンプル株式会社')
        own_department = Department.objects.create(company=company, name='開発部')
        other_department = Department.objects.create(company=company, name='営業部')
        _set_primary_department(sample_user, own_department)
        matching_group = ManagementGroup.objects.create(name='開発部グループ', department=own_department)
        matching_group.members.add(sample_user)
        other_group = ManagementGroup.objects.create(name='営業部グループ', department=other_department)
        other_group.members.add(sample_user)

        applicable = get_applicable_management_groups(sample_user)

        assert applicable == [matching_group]


def _create_department(name):
    company = Company.objects.create(name=f'{name}の会社')
    return Department.objects.create(company=company, name=name)


def _set_primary_department(user, department):
    EmployeeDepartment.objects.create(employee=user.employee, department=department, is_primary=True)
```

- [ ] **Step 2: テストを実行し、`get_applicable_management_groups`が存在せず失敗することを確認する**

Run: `pytest app/tests/unit/lib/permissions_test.py::TestGetApplicableManagementGroups -v`
Expected: FAIL(`ImportError: cannot import name 'get_applicable_management_groups'`)

- [ ] **Step 3: `app/lib/permissions.py`に関数を追加する**

`app/lib/permissions.py`を以下の内容で置き換える。

```python
# app内で共有する権限判定ロジックをここに置く

from app.models import DepartmentHierarchy, ManagementGroup


# 管理者かどうかを判定(is_staffを管理者フラグとして扱う)
def is_admin(user):
    return user.is_staff


# タスクを編集できるかどうかを判定
# 管理者、作成者本人、担当者本人のいずれかであれば編集可能
def can_edit_task(user, task):
    if is_admin(user):
        return True
    return task.created_by_id == user.id or task.assigned_to_id == user.id


# タスクを削除できるかどうかを判定
# 編集権限と同じ基準を採用する
def can_delete_task(user, task):
    return can_edit_task(user, task)


# ログインユーザーに適用される管理グループの一覧を返す
def get_applicable_management_groups(user):
    groups = ManagementGroup.objects.filter(members=user)

    primary_department = _get_primary_department(user)

    applicable = []
    for group in groups:
        if group.is_admin:
            applicable.append(group)
            continue
        if primary_department and _is_self_parent_or_sibling(group.department, primary_department):
            applicable.append(group)
    return applicable


# ============================================================
# ここから先はprivateヘルパー
# ============================================================


# ユーザーの社員情報から主務部門を取得する(Employeeが無い/主務が無い場合はNone)
def _get_primary_department(user):
    employee = getattr(user, 'employee', None)
    if employee is None:
        return None
    primary = employee.employee_departments.filter(is_primary=True).first()
    return primary.department if primary else None


# 対象部門(group_department)が、基準部門(primary_department)自身・親・兄弟のいずれかに一致するかを判定する
def _is_self_parent_or_sibling(group_department, primary_department):
    if group_department == primary_department:
        return True

    hierarchy = DepartmentHierarchy.objects.filter(department=primary_department).first()
    if hierarchy is None:
        return False

    if group_department == hierarchy.parent_department:
        return True

    if hierarchy.parent_department is None:
        return False

    return DepartmentHierarchy.objects.filter(
        department=group_department, parent_department=hierarchy.parent_department
    ).exists()
```

- [ ] **Step 4: テストを実行し、PASSすることを確認する**

Run: `pytest app/tests/unit/lib/permissions_test.py -v`
Expected: 全件PASS(既存の`TestIsAdmin`/`TestCanEditTask`/`TestCanDeleteTask`含む)

- [ ] **Step 5: プロジェクト全体のユニットテストを実行し、回帰が無いことを確認する**

Run: `pytest app/tests/unit/ -v`
Expected: 全テストPASS

- [ ] **Step 6: コミットする**

```bash
git add app/lib/permissions.py app/tests/unit/lib/permissions_test.py
git commit -m "get_applicable_management_groupsを追加し、社員に適用される管理グループを決定できるようにする"
```

---

## 完了条件

- `pytest app/tests/unit/ -v` が全件PASSする
- 本プランの範囲は「ロール決定ロジック」のみ。`get_applicable_management_groups()`を各ビュー(`company.py`/`department.py`/`employee.py`のTODO)へ組み込む「アクセス制御」は別プランとして今後あらためて設計する
