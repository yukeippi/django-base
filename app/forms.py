from django import forms


class TaskImportForm(forms.Form):
    file = forms.FileField(
        label='Excelファイル',
        help_text='.xlsx形式のファイルを選択してください',
    )
    has_header = forms.BooleanField(
        label='1行目をヘッダー行として扱う',
        required=False,
        initial=True,
    )
