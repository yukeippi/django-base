from app.excel_base import ColumnDef, ExcelHandler


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


import io

import openpyxl
import pytest

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
