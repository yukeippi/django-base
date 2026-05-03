# Excel インポート・エクスポート 汎用ハンドラー設計

## 概要

openpyxl を使った Excel インポート・エクスポート機能を汎用化し、アプリケーション内の複数モデルで再利用できるようにする。

## 背景

現行の `app/excel.py` は `Task` モデルに特化した実装になっており、別モデルで同様の機能が必要になった際に流用できない。列定義（ヘッダー名・フィールド名）もインポート・エクスポートで別々に管理されており、ずれが生じるリスクがある。

## ファイル構成

```
app/
  excel_base.py     # ColumnDef + ExcelHandler（汎用ロジック）
  excel.py          # TaskExcelHandler（Task専用、現行を置き換え）
```

`excel_base.py` は特定のモデルに依存しない汎用モジュールとして設計し、他アプリからも `from app.excel_base import ExcelHandler` でインポートして使える。

## コンポーネント

### `ColumnDef`

1列分の定義を保持するデータクラス。インポートとエクスポートで同じインスタンスを共用する。

| パラメータ | 型 | 説明 |
|---|---|---|
| `model_field` | `str` | モデルのフィールド名（DBカラム名） |
| `excel_header` | `str` | Excelの列ヘッダー名 |
| `required` | `bool` | `True` の場合、空値をエラーとして扱う（デフォルト: `False`） |
| `cell_to_value` | `callable \| None` | インポート時: セル値 → Python値の変換関数。`None` の場合はそのまま使用 |
| `value_to_cell` | `callable \| None` | エクスポート時: Python値 → セル値の変換関数。`None` の場合はそのまま使用 |

### `ExcelHandler`

汎用のインポート・エクスポートロジックを持つ基底クラス。

```python
class ExcelHandler:
    model = None          # サブクラスで指定（Django Model）
    columns = []          # ColumnDef のリスト、サブクラスで指定
    sheet_name = 'Sheet1'
    filename = 'export.xlsx'  # エクスポート時のダウンロードファイル名
```

#### メソッド

| メソッド | 戻り値 | 説明 |
|---|---|---|
| `import_from_excel(file, has_header=True)` | `tuple[int, list[dict]]` | ファイルを読み込みインポート。`(作成件数, エラーリスト)` を返す |
| `export_to_new_excel(queryset)` | `HttpResponse` | 新規 Excel ファイルとして返す |
| `export_to_template(queryset, template_path)` | `HttpResponse` | 既存テンプレートに書き込んで返す |

### `TaskExcelHandler`

`Task` モデル用の列定義。

```python
class TaskExcelHandler(ExcelHandler):
    model = Task
    sheet_name = 'タスク'
    columns = [
        ColumnDef('title',       'タイトル',  required=True),
        ColumnDef('description', '説明'),
        ColumnDef('status',      'ステータス', cell_to_value=lambda v: v or 'todo'),
        ColumnDef('priority',    '優先度',    cell_to_value=lambda v: int(v) if v else 3),
        ColumnDef('due_date',    '期限',      cell_to_value=parse_date_cell,
                                              value_to_cell=lambda v: str(v) if v else ''),
    ]
```

## データフロー

### インポート

```
Excel ファイル
  → openpyxl でセル読み取り
  → ColumnDef.cell_to_value で各値を変換
  → required チェック（空値エラー収集）
  → model(**kwargs) でインスタンス生成
  → full_clean() でバリデーション（エラー収集）
  → 全行エラーなし → transaction.atomic() で全件 save()
  → エラーあり → 保存せず (0, エラーリスト) を返す
```

### エクスポート

```
QuerySet
  → 各インスタンスの model_field を取得
  → ColumnDef.value_to_cell で各値を変換
  → openpyxl でヘッダー行 + データ行を書き込み
  → HttpResponse として返す
```

## エラー処理

### インポート時

- エラーが **1件でもあれば全件ロールバック**（保存しない）
- エラーリスト形式: `[{'row': 行番号, 'message': エラー内容}, ...]`
- `required=True` の空値チェックは `full_clean()` の前に実施し、分かりやすいメッセージを返す
- それ以外のバリデーションは Django の `full_clean()` に委譲

## テスト方針

### `excel_base.py` のテスト（新規）

ダミーモデルを用いて汎用ロジックを検証する。

- 全行OKの場合は全件保存されること
- 1行でもエラーがある場合は0件保存されること（ロールバック）
- `cell_to_value` / `value_to_cell` の変換が正しく動作すること
- `required=True` で空値をエラーとして検出すること
- `full_clean()` のバリデーションエラーが正しくエラーリストに入ること

### `TaskExcelHandler` のテスト（`test_excel.py` を更新）

- 現行のテストケースをほぼ流用（インターフェース変更に合わせて修正）
- ロールバック動作のテストを追加

### テスト規約

CLAUDE.md に従い、テスト関数名は日本語で記述する。

## ビューからの呼び出し

```python
handler = TaskExcelHandler()

# インポート
created_count, errors = handler.import_from_excel(request.FILES['file'], has_header=True)

# エクスポート（新規）
return handler.export_to_new_excel(Task.objects.all())

# エクスポート（テンプレート）
return handler.export_to_template(Task.objects.all(), template_path)
```

現行の `views.py` の呼び出しは上記に置き換える。インターフェースがシンプルになるため、`views.py` の変更は最小限に留まる。
