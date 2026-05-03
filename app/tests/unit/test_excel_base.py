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
