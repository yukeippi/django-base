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
