# Excel 汎用ハンドラー実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `ColumnDef` + `ExcelHandler` を `app/excel_base.py` に実装し、`app/excel.py` を `TaskExcelHandler` のみに置き換える。

**Architecture:** `ColumnDef` データクラスに列の定義（モデルフィールド名・Excelヘッダー名・変換関数）を持たせ、`ExcelHandler` 基底クラスが汎用ロジックを実装する。インポートはエラー1件でも全件ロールバック（`transaction.atomic()`）。バリデーションは Django の `Model.full_clean()` に委譲し、変換エラーは `cell_to_value` から `ValueError` を送出して捕捉する。`excel_base.py` は `openpyxl` と Django のみに依存し、他プロジェクトへのコピー転用を想定した自己完結モジュールとする。

**Tech Stack:** Python 3.14, Django 5.x, openpyxl, pytest, pytest-django

---

## ファイル構成

| 操作 | パス | 役割 |
|------|------|------|
| 作成 | `app/excel_base.py` | `ColumnDef` + `ExcelHandler`（汎用ロジック） |
| 作成 | `app/tests/unit/test_excel_base.py` | 汎用ロジックのテスト |
| 置換 | `app/excel.py` | `TaskExcelHandler` のみ（現行の関数を削除） |
| 置換 | `app/tests/unit/test_excel.py` | 新インターフェース対応 + ロールバックテスト追加 |
| 修正 | `app/views.py` | `TaskExcelHandler` インスタンス経由に変更 |

---

### Task 1: `ColumnDef` データクラスを作成する

**Files:**
- Create: `app/excel_base.py`
- Create: `app/tests/unit/test_excel_base.py`

- [ ] **Step 1: テストを書く**

`app/tests/unit/test_excel_base.py` を新規作成する:

```python
from app.excel_base import ColumnDef


class TestColumnDef:

    def test_必須パラメータのみで作成できる(self):
        col = ColumnDef(model_field='title', excel_header='タイトル')
        assert col.model_field == 'title'
        assert col.excel_header == 'タイトル'
        assert col.required is False
        assert col.cell_to_value is None
        assert col.value_to_cell is None

    def test_全パラメータを指定できる(self):
        to_val = lambda v: v.strip() if v else ''
        to_cell = str
        col = ColumnDef(
            model_field='title',
            excel_header='タイトル',
            required=True,
            cell_to_value=to_val,
            value_to_cell=to_cell,
        )
        assert col.required is True
        assert col.cell_to_value is to_val
        assert col.value_to_cell is to_cell
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest app/tests/unit/test_excel_base.py -v
```

期待: `ModuleNotFoundError: No module named 'app.excel_base'`

- [ ] **Step 3: `ColumnDef` を実装する**

`app/excel_base.py` を新規作成する:

```python
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class ColumnDef:
    model_field: str
    excel_header: str
    required: bool = False
    cell_to_value: Optional[Callable] = None
    value_to_cell: Optional[Callable] = None
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
pytest app/tests/unit/test_excel_base.py::TestColumnDef -v
```

期待: 2件 PASSED

- [ ] **Step 5: コミット**

```bash
git add app/excel_base.py app/tests/unit/test_excel_base.py
git commit -m "feat: ColumnDefデータクラスを追加"
```

---

### Task 2: `ExcelHandler.import_from_excel` 正常系を実装する

**Files:**
- Modify: `app/excel_base.py`
- Modify: `app/tests/unit/test_excel_base.py`

- [ ] **Step 1: テストを追加する**

`app/tests/unit/test_excel_base.py` の冒頭の import 行を以下に更新し（`ExcelHandler` を追加）、その後に続くコードを `TestColumnDef` クラスの後ろに追加する:

```python
from app.excel_base import ColumnDef, ExcelHandler  # ExcelHandler を追加
```

```python
import io

import openpyxl
import pytest

from app.excel_base import ColumnDef, ExcelHandler
from app.models import Task


# テスト用Excelファイルをメモリ上に作成するヘルパー
def make_excel(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# Taskモデルを使った最小構成のハンドラー（汎用ロジックのテスト用）
class MinimalTaskHandler(ExcelHandler):
    model = Task
    filename = 'test.xlsx'
    columns = [
        ColumnDef(model_field='title', excel_header='タイトル', required=True),
    ]


@pytest.mark.django_db
class TestExcelHandlerImport正常系:

    def test_ヘッダーありで1件インポートできる(self):
        f = make_excel([
            ['タイトル'],
            ['テストタスク'],
        ])
        count, errors = MinimalTaskHandler().import_from_excel(f, has_header=True)

        assert count == 1
        assert errors == []
        assert Task.objects.filter(title='テストタスク').exists()

    def test_ヘッダーなしで1行目からデータとして読み込まれる(self):
        f = make_excel([['テストタスク2']])
        count, errors = MinimalTaskHandler().import_from_excel(f, has_header=False)

        assert count == 1
        assert errors == []
        assert Task.objects.filter(title='テストタスク2').exists()

    def test_複数行を一括インポートできる(self):
        f = make_excel([
            ['タイトル'],
            ['タスクA'],
            ['タスクB'],
            ['タスクC'],
        ])
        count, errors = MinimalTaskHandler().import_from_excel(f, has_header=True)

        assert count == 3
        assert errors == []

    def test_cell_to_valueで変換された値が保存される(self):
        class UpperHandler(ExcelHandler):
            model = Task
            filename = 'test.xlsx'
            columns = [
                ColumnDef(
                    model_field='title',
                    excel_header='タイトル',
                    required=True,
                    cell_to_value=lambda v: v.upper() if v else v,
                ),
            ]

        f = make_excel([['タイトル'], ['hello']])
        count, errors = UpperHandler().import_from_excel(f, has_header=True)

        assert count == 1
        assert Task.objects.filter(title='HELLO').exists()
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest app/tests/unit/test_excel_base.py::TestExcelHandlerImport正常系 -v
```

期待: `AttributeError: type object 'ExcelHandler' has no attribute 'import_from_excel'` または同等のエラー

- [ ] **Step 3: `ExcelHandler` と `import_from_excel` を実装する**

`app/excel_base.py` を以下に置き換える:

```python
from dataclasses import dataclass
from typing import Callable, Optional

import openpyxl
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse


@dataclass
class ColumnDef:
    model_field: str
    excel_header: str
    required: bool = False
    cell_to_value: Optional[Callable] = None
    value_to_cell: Optional[Callable] = None


class ExcelHandler:
    model = None
    columns = []
    sheet_name = 'Sheet1'
    filename = 'export.xlsx'

    def import_from_excel(self, file, has_header=True):
        wb = openpyxl.load_workbook(file, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))

        data_rows = rows[1:] if has_header else rows
        start_row = 2 if has_header else 1

        instances = []
        errors = []

        for offset, row in enumerate(data_rows):
            row_num = start_row + offset
            padded = list(row) + [None] * len(self.columns)
            kwargs = {}
            row_error = None

            for i, col_def in enumerate(self.columns):
                raw_value = padded[i]

                if col_def.required and (raw_value is None or str(raw_value).strip() == ''):
                    row_error = {'row': row_num, 'message': f'{col_def.excel_header}が空です'}
                    break

                try:
                    value = col_def.cell_to_value(raw_value) if col_def.cell_to_value else raw_value
                except (ValueError, TypeError) as e:
                    row_error = {'row': row_num, 'message': str(e)}
                    break

                kwargs[col_def.model_field] = value

            if row_error:
                errors.append(row_error)
                continue

            instance = self.model(**kwargs)
            try:
                instance.full_clean()
                instances.append(instance)
            except ValidationError as e:
                errors.append({'row': row_num, 'message': str(e)})

        if errors:
            return 0, errors

        with transaction.atomic():
            for instance in instances:
                instance.save()

        return len(instances), []
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
pytest app/tests/unit/test_excel_base.py::TestExcelHandlerImport正常系 -v
```

期待: 4件 PASSED

- [ ] **Step 5: コミット**

```bash
git add app/excel_base.py app/tests/unit/test_excel_base.py
git commit -m "feat: ExcelHandler.import_from_excelを実装"
```

---

### Task 3: `import_from_excel` エラー系・ロールバックのテストを追加する

（`import_from_excel` の実装はTask 2で完了しているため、テストを追加するだけ）

**Files:**
- Modify: `app/tests/unit/test_excel_base.py`

- [ ] **Step 1: テストを追加する**

`app/tests/unit/test_excel_base.py` に以下のクラスを追加する:

```python
@pytest.mark.django_db
class TestExcelHandlerImportエラー系:

    def test_requiredフィールドが空の場合はエラーになる(self):
        f = make_excel([['タイトル'], ['']])
        count, errors = MinimalTaskHandler().import_from_excel(f, has_header=True)

        assert count == 0
        assert len(errors) == 1
        assert errors[0]['row'] == 2
        assert 'タイトルが空です' in errors[0]['message']

    def test_full_cleanエラーが発生した場合はエラーリストに追加される(self):
        class InvalidStatusHandler(ExcelHandler):
            model = Task
            filename = 'test.xlsx'
            columns = [
                ColumnDef(model_field='title',  excel_header='タイトル', required=True),
                ColumnDef(model_field='status', excel_header='ステータス',
                          cell_to_value=lambda v: v or 'todo'),
            ]

        f = make_excel([
            ['タイトル', 'ステータス'],
            ['タスクA', 'invalid_status'],
        ])
        count, errors = InvalidStatusHandler().import_from_excel(f, has_header=True)

        assert count == 0
        assert len(errors) == 1

    def test_cell_to_valueがValueErrorを発生した場合はエラーになる(self):
        def strict_converter(v):
            if v == 'bad':
                raise ValueError('変換エラー')
            return v

        class StrictHandler(ExcelHandler):
            model = Task
            filename = 'test.xlsx'
            columns = [
                ColumnDef(
                    model_field='title',
                    excel_header='タイトル',
                    required=True,
                    cell_to_value=strict_converter,
                ),
            ]

        f = make_excel([['タイトル'], ['bad']])
        count, errors = StrictHandler().import_from_excel(f, has_header=True)

        assert count == 0
        assert len(errors) == 1
        assert '変換エラー' in errors[0]['message']

    def test_エラーが1件でもあれば全件ロールバックされる(self):
        f = make_excel([
            ['タイトル'],
            ['正常タスク'],
            [''],           # エラー行
            ['別の正常タスク'],
        ])
        count, errors = MinimalTaskHandler().import_from_excel(f, has_header=True)

        assert count == 0
        assert len(errors) == 1
        assert not Task.objects.filter(title='正常タスク').exists()
        assert not Task.objects.filter(title='別の正常タスク').exists()
```

- [ ] **Step 2: テストが通ることを確認する**

```bash
pytest app/tests/unit/test_excel_base.py::TestExcelHandlerImportエラー系 -v
```

期待: 4件 PASSED

- [ ] **Step 3: コミット**

```bash
git add app/tests/unit/test_excel_base.py
git commit -m "test: ExcelHandlerインポートのエラー系・ロールバックテストを追加"
```

---

### Task 4: `ExcelHandler.export_to_new_excel` を実装する

**Files:**
- Modify: `app/excel_base.py`
- Modify: `app/tests/unit/test_excel_base.py`

- [ ] **Step 1: テストを追加する**

`app/tests/unit/test_excel_base.py` に以下のクラスを追加する:

```python
@pytest.mark.django_db
class TestExcelHandlerExportNewExcel:

    def test_ヘッダー行が正しく出力される(self):
        response = MinimalTaskHandler().export_to_new_excel(Task.objects.none())

        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        rows = list(wb.active.iter_rows(values_only=True))
        assert rows[0] == ('タイトル',)

    def test_データ行が正しく出力される(self):
        Task.objects.create(title='出力テスト')
        response = MinimalTaskHandler().export_to_new_excel(Task.objects.all())

        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        rows = list(wb.active.iter_rows(values_only=True))
        assert len(rows) == 2
        assert rows[1][0] == '出力テスト'

    def test_value_to_cellで変換された値が出力される(self):
        class UpperExportHandler(ExcelHandler):
            model = Task
            filename = 'test.xlsx'
            columns = [
                ColumnDef(
                    model_field='title',
                    excel_header='タイトル',
                    value_to_cell=lambda v: v.upper() if v else v,
                ),
            ]

        Task.objects.create(title='hello')
        response = UpperExportHandler().export_to_new_excel(Task.objects.all())

        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        rows = list(wb.active.iter_rows(values_only=True))
        assert rows[1][0] == 'HELLO'

    def test_ContentTypeがExcel形式になっている(self):
        response = MinimalTaskHandler().export_to_new_excel(Task.objects.none())
        assert response['Content-Type'] == (
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_filenameがContentDispositionに含まれる(self):
        response = MinimalTaskHandler().export_to_new_excel(Task.objects.none())
        assert 'test.xlsx' in response['Content-Disposition']
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest app/tests/unit/test_excel_base.py::TestExcelHandlerExportNewExcel -v
```

期待: `AttributeError: type object 'ExcelHandler' has no attribute 'export_to_new_excel'`

- [ ] **Step 3: `export_to_new_excel` を実装する**

`app/excel_base.py` の `ExcelHandler` クラスに `import_from_excel` の後ろに追加する:

```python
    def export_to_new_excel(self, queryset):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = self.sheet_name

        ws.append([col.excel_header for col in self.columns])

        for obj in queryset:
            row = []
            for col_def in self.columns:
                value = getattr(obj, col_def.model_field)
                if col_def.value_to_cell:
                    value = col_def.value_to_cell(value)
                row.append(value)
            ws.append(row)

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{self.filename}"'
        wb.save(response)
        return response
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
pytest app/tests/unit/test_excel_base.py::TestExcelHandlerExportNewExcel -v
```

期待: 5件 PASSED

- [ ] **Step 5: コミット**

```bash
git add app/excel_base.py app/tests/unit/test_excel_base.py
git commit -m "feat: ExcelHandler.export_to_new_excelを実装"
```

---

### Task 5: `ExcelHandler.export_to_template` を実装する

**Files:**
- Modify: `app/excel_base.py`
- Modify: `app/tests/unit/test_excel_base.py`

- [ ] **Step 1: テストを追加する**

`app/tests/unit/test_excel_base.py` に以下のクラスを追加する:

```python
@pytest.mark.django_db
class TestExcelHandlerExportTemplate:

    def test_テンプレートの指定セルにデータが書き込まれる(self, tmp_path):
        template_path = tmp_path / 'template.xlsx'
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['タイトル'])
        wb.save(str(template_path))

        Task.objects.create(title='テンプレートテスト')
        response = MinimalTaskHandler().export_to_template(
            Task.objects.all(), str(template_path)
        )

        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        assert wb.active.cell(row=2, column=1).value == 'テンプレートテスト'

    def test_複数タスクが連続する行に書き込まれる(self, tmp_path):
        template_path = tmp_path / 'template.xlsx'
        openpyxl.Workbook().save(str(template_path))

        Task.objects.create(title='タスク1')
        Task.objects.create(title='タスク2')
        response = MinimalTaskHandler().export_to_template(
            Task.objects.all().order_by('id'), str(template_path)
        )

        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        ws = wb.active
        assert ws.cell(row=2, column=1).value == 'タスク1'
        assert ws.cell(row=3, column=1).value == 'タスク2'

    def test_filenameがContentDispositionに含まれる(self, tmp_path):
        template_path = tmp_path / 'template.xlsx'
        openpyxl.Workbook().save(str(template_path))

        response = MinimalTaskHandler().export_to_template(
            Task.objects.none(), str(template_path)
        )
        assert 'test.xlsx' in response['Content-Disposition']
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest app/tests/unit/test_excel_base.py::TestExcelHandlerExportTemplate -v
```

期待: `AttributeError: type object 'ExcelHandler' has no attribute 'export_to_template'`

- [ ] **Step 3: `export_to_template` を実装する**

`app/excel_base.py` の `ExcelHandler` クラスに `export_to_new_excel` の後ろに追加する:

```python
    def export_to_template(self, queryset, template_path):
        DATA_START_ROW = 2
        wb = openpyxl.load_workbook(template_path)
        ws = wb.active

        for offset, obj in enumerate(queryset):
            row = DATA_START_ROW + offset
            for col_idx, col_def in enumerate(self.columns, start=1):
                value = getattr(obj, col_def.model_field)
                if col_def.value_to_cell:
                    value = col_def.value_to_cell(value)
                ws.cell(row=row, column=col_idx, value=value)

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{self.filename}"'
        wb.save(response)
        return response
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
pytest app/tests/unit/test_excel_base.py::TestExcelHandlerExportTemplate -v
```

期待: 3件 PASSED

- [ ] **Step 5: コミット**

```bash
git add app/excel_base.py app/tests/unit/test_excel_base.py
git commit -m "feat: ExcelHandler.export_to_templateを実装"
```

---

### Task 6: `TaskExcelHandler` を作成し `excel.py` と `test_excel.py` を置き換える

**Files:**
- Replace: `app/excel.py`
- Replace: `app/tests/unit/test_excel.py`

- [ ] **Step 1: `test_excel.py` を新インターフェースに置き換える**

`app/tests/unit/test_excel.py` を以下に全面置き換えする:

```python
import io
from datetime import date

import openpyxl
import pytest

from app.excel import TaskExcelHandler
from app.models import Task


def make_excel(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


@pytest.mark.django_db
class TestTaskExcelHandlerImport:

    def test_ヘッダーありで全フィールドが正しくインポートされる(self):
        f = make_excel([
            ['タイトル', '説明', 'ステータス', '優先度', '期限'],
            ['タスクA', '説明A', 'todo', 2, '2026-05-01'],
        ])
        count, errors = TaskExcelHandler().import_from_excel(f, has_header=True)

        assert count == 1
        assert errors == []
        task = Task.objects.get(title='タスクA')
        assert task.description == '説明A'
        assert task.status == 'todo'
        assert task.priority == 2
        assert task.due_date == date(2026, 5, 1)

    def test_ヘッダーなしで1行目からデータとして読み込まれる(self):
        f = make_excel([['タスクB', '', 'in_progress', 1, '']])
        count, errors = TaskExcelHandler().import_from_excel(f, has_header=False)

        assert count == 1
        assert errors == []
        assert Task.objects.get(title='タスクB').status == 'in_progress'

    def test_ステータスが空の場合はデフォルト値todoになる(self):
        f = make_excel([
            ['タイトル', '説明', 'ステータス', '優先度', '期限'],
            ['タスクC', '', '', '', ''],
        ])
        count, errors = TaskExcelHandler().import_from_excel(f, has_header=True)

        assert count == 1
        assert Task.objects.get(title='タスクC').status == 'todo'

    def test_優先度が空の場合はデフォルト値3になる(self):
        f = make_excel([
            ['タイトル', '説明', 'ステータス', '優先度', '期限'],
            ['タスクD', '', '', None, ''],
        ])
        count, errors = TaskExcelHandler().import_from_excel(f, has_header=True)

        assert count == 1
        assert Task.objects.get(title='タスクD').priority == 3

    def test_期限が空の場合はNoneになる(self):
        f = make_excel([
            ['タイトル', '説明', 'ステータス', '優先度', '期限'],
            ['タスクE', '', 'todo', 3, ''],
        ])
        count, errors = TaskExcelHandler().import_from_excel(f, has_header=True)

        assert count == 1
        assert Task.objects.get(title='タスクE').due_date is None

    def test_タイトルが空の行はエラーになる(self):
        f = make_excel([
            ['タイトル', '説明', 'ステータス', '優先度', '期限'],
            ['', '説明', 'todo', 3, ''],
        ])
        count, errors = TaskExcelHandler().import_from_excel(f, has_header=True)

        assert count == 0
        assert len(errors) == 1
        assert errors[0]['row'] == 2
        assert 'タイトルが空です' in errors[0]['message']

    def test_不正なステータスはエラーになる(self):
        f = make_excel([
            ['タイトル', '説明', 'ステータス', '優先度', '期限'],
            ['タスクF', '', 'invalid', 3, ''],
        ])
        count, errors = TaskExcelHandler().import_from_excel(f, has_header=True)

        assert count == 0
        assert len(errors) == 1

    def test_優先度が範囲外の場合はエラーになる(self):
        f = make_excel([
            ['タイトル', '説明', 'ステータス', '優先度', '期限'],
            ['タスクG', '', 'todo', 9, ''],
        ])
        count, errors = TaskExcelHandler().import_from_excel(f, has_header=True)

        assert count == 0
        assert len(errors) == 1

    def test_不正な日付形式はエラーになる(self):
        f = make_excel([
            ['タイトル', '説明', 'ステータス', '優先度', '期限'],
            ['タスクH', '', 'todo', 3, 'not-a-date'],
        ])
        count, errors = TaskExcelHandler().import_from_excel(f, has_header=True)

        assert count == 0
        assert len(errors) == 1
        assert '日付形式が不正' in errors[0]['message']

    def test_エラーがある場合は全件ロールバックされる(self):
        f = make_excel([
            ['タイトル', '説明', 'ステータス', '優先度', '期限'],
            ['正常タスク', '', 'todo', 3, ''],
            ['', '', 'todo', 3, ''],
            ['別の正常タスク', '', 'done', 1, ''],
        ])
        count, errors = TaskExcelHandler().import_from_excel(f, has_header=True)

        assert count == 0
        assert len(errors) == 1
        assert not Task.objects.filter(title='正常タスク').exists()
        assert not Task.objects.filter(title='別の正常タスク').exists()


@pytest.mark.django_db
class TestTaskExcelHandlerExportNewExcel:

    def test_タスクなしの場合はヘッダー行のみのファイルが返る(self):
        response = TaskExcelHandler().export_to_new_excel(Task.objects.none())

        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        rows = list(wb.active.iter_rows(values_only=True))
        assert len(rows) == 1
        assert rows[0] == ('タイトル', '説明', 'ステータス', '優先度', '期限')

    def test_タスクのデータが正しく書き出される(self):
        Task.objects.create(
            title='出力タスク',
            description='説明文',
            status='in_progress',
            priority=2,
            due_date=date(2026, 6, 1),
        )
        response = TaskExcelHandler().export_to_new_excel(Task.objects.all())

        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        rows = list(wb.active.iter_rows(values_only=True))
        assert len(rows) == 2
        assert rows[1][0] == '出力タスク'
        assert rows[1][1] == '説明文'
        assert rows[1][2] == 'in_progress'
        assert rows[1][3] == 2
        assert rows[1][4] == '2026-06-01'

    def test_ContentTypeがExcel形式になっている(self):
        response = TaskExcelHandler().export_to_new_excel(Task.objects.none())
        assert response['Content-Type'] == (
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_ContentDispositionにファイル名が含まれる(self):
        response = TaskExcelHandler().export_to_new_excel(Task.objects.none())
        assert 'attachment' in response['Content-Disposition']
        assert 'tasks.xlsx' in response['Content-Disposition']


@pytest.mark.django_db
class TestTaskExcelHandlerExportTemplate:

    def test_テンプレートの指定セルにデータが正しく書き込まれる(self, tmp_path):
        template_path = tmp_path / 'template.xlsx'
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['タイトル', '説明', 'ステータス', '優先度', '期限'])
        wb.save(str(template_path))

        Task.objects.create(
            title='テンプレートタスク',
            description='テスト説明',
            status='done',
            priority=5,
            due_date=date(2026, 7, 1),
        )
        response = TaskExcelHandler().export_to_template(
            Task.objects.all(), str(template_path)
        )

        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        ws = wb.active
        assert ws.cell(row=2, column=1).value == 'テンプレートタスク'
        assert ws.cell(row=2, column=2).value == 'テスト説明'
        assert ws.cell(row=2, column=4).value == 5

    def test_複数タスクが連続する行に書き込まれる(self, tmp_path):
        template_path = tmp_path / 'template.xlsx'
        openpyxl.Workbook().save(str(template_path))

        Task.objects.create(title='タスク1', status='todo', priority=1)
        Task.objects.create(title='タスク2', status='done', priority=2)
        response = TaskExcelHandler().export_to_template(
            Task.objects.all().order_by('id'), str(template_path)
        )

        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        ws = wb.active
        assert ws.cell(row=2, column=1).value == 'タスク1'
        assert ws.cell(row=3, column=1).value == 'タスク2'

    def test_ContentDispositionにファイル名が含まれる(self, tmp_path):
        template_path = tmp_path / 'template.xlsx'
        openpyxl.Workbook().save(str(template_path))

        response = TaskExcelHandler().export_to_template(
            Task.objects.none(), str(template_path)
        )
        assert 'tasks.xlsx' in response['Content-Disposition']
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest app/tests/unit/test_excel.py -v
```

期待: `ImportError: cannot import name 'TaskExcelHandler' from 'app.excel'`

- [ ] **Step 3: `excel.py` を `TaskExcelHandler` に全面置き換えする**

`app/excel.py` を以下に全面置き換えする:

```python
from django.utils.dateparse import parse_date

from .excel_base import ColumnDef, ExcelHandler
from .models import Task


def _parse_date_cell(value):
    if value is None or value == '':
        return None
    if hasattr(value, 'date'):
        return value.date()
    parsed = parse_date(str(value))
    if parsed is None:
        raise ValueError(f'期限の日付形式が不正です: {value}')
    return parsed


class TaskExcelHandler(ExcelHandler):
    model = Task
    sheet_name = 'タスク'
    filename = 'tasks.xlsx'
    columns = [
        ColumnDef(model_field='title',       excel_header='タイトル',  required=True),
        ColumnDef(model_field='description', excel_header='説明',
                  cell_to_value=lambda v: str(v) if v else ''),
        ColumnDef(model_field='status',      excel_header='ステータス',
                  cell_to_value=lambda v: v or 'todo'),
        ColumnDef(model_field='priority',    excel_header='優先度',
                  cell_to_value=lambda v: int(v) if v is not None and v != '' else 3),
        ColumnDef(model_field='due_date',    excel_header='期限',
                  cell_to_value=_parse_date_cell,
                  value_to_cell=lambda v: str(v) if v else ''),
    ]
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
pytest app/tests/unit/test_excel.py -v
```

期待: 全テスト PASSED

- [ ] **Step 5: コミット**

```bash
git add app/excel.py app/tests/unit/test_excel.py
git commit -m "feat: TaskExcelHandlerを実装しexcel.pyを置き換え"
```

---

### Task 7: `views.py` をハンドラーインスタンス経由に更新する

**Files:**
- Modify: `app/views.py`

- [ ] **Step 1: `views.py` を更新する**

`app/views.py` を以下に置き換えする:

```python
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.contrib import messages

from .models import Task
from .forms import TaskImportForm
from .excel import TaskExcelHandler


# ホームページビュー
def index(request):
    return render(request, 'app/index.html', {
        'title': 'Task Manager',
    })


# タスク一覧ビュー
class TaskListView(ListView):
    model = Task
    template_name = 'app/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10


# タスク詳細ビュー
class TaskDetailView(DetailView):
    model = Task
    template_name = 'app/task_detail.html'
    context_object_name = 'task'


# タスクAPI（E2Eテスト用）
def task_api(request):
    if request.method == 'GET':
        tasks = Task.objects.all().values('id', 'title', 'status', 'priority')
        return JsonResponse(list(tasks), safe=False)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ExcelファイルからTaskを一括インポートする
def task_import(request):
    if request.method == 'POST':
        form = TaskImportForm(request.POST, request.FILES)
        if form.is_valid():
            handler = TaskExcelHandler()
            created_count, errors = handler.import_from_excel(
                file=request.FILES['file'],
                has_header=form.cleaned_data['has_header'],
            )
            if errors:
                for err in errors:
                    messages.warning(request, f"行{err['row']}: {err['message']}")
            if created_count:
                messages.success(request, f'{created_count}件のタスクをインポートしました。')
            return redirect('app:task_list')
    else:
        form = TaskImportForm()

    return render(request, 'app/task_import.html', {'form': form})


# 全タスクを新規Excelファイルとしてダウンロードする
def task_export(request):
    return TaskExcelHandler().export_to_new_excel(Task.objects.all())


# テンプレートExcelに全タスクを書き込んでダウンロードする
# テンプレートファイルのパスは settings.EXCEL_TEMPLATE_PATH で指定すること
def task_export_template(request):
    from django.conf import settings
    template_path = getattr(settings, 'EXCEL_TEMPLATE_PATH', None)
    if not template_path:
        messages.error(request, 'settings.EXCEL_TEMPLATE_PATH が設定されていません。')
        return redirect('app:task_list')

    return TaskExcelHandler().export_to_template(Task.objects.all(), template_path)
```

- [ ] **Step 2: 全ユニットテストを実行して確認する**

```bash
pytest app/tests/unit/ -v
```

期待: 全テスト PASSED

- [ ] **Step 3: コミット**

```bash
git add app/views.py
git commit -m "refactor: views.pyをTaskExcelHandler経由に変更"
```
