from django.utils.dateparse import parse_date

from .excel_base import ColumnDef, ExcelHandler
from .models import Task


# セル値を date オブジェクトに変換する
# datetime 型はそのまま .date() で変換、文字列は parse_date で解析する
# 解析できない場合は ValueError を送出する
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
