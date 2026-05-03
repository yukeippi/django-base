from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class ColumnDef:
    model_field: str
    excel_header: str
    required: bool = False
    cell_to_value: Optional[Callable] = None
    value_to_cell: Optional[Callable] = None
