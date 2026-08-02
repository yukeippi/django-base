from django.contrib.auth.forms import AuthenticationForm


# 社員番号でログインするためのフォーム(usernameフィールドのラベルのみ変更)
class EmployeeLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = '社員番号'
