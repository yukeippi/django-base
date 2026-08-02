from django import forms
from django.contrib.auth.models import User
from app.models import Employee


# 社員の新規作成・編集で使うフォーム(UserとEmployeeにまたがって扱う)
class EmployeeForm(forms.Form):
    employee_number = forms.CharField(
        label='社員番号', max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='姓', max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        label='名', max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='パスワード', required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        if instance is None:
            self.fields['password'].required = True
            return
        self.initial.setdefault('employee_number', instance.employee_number)
        self.initial.setdefault('last_name', instance.user.last_name)
        self.initial.setdefault('first_name', instance.user.first_name)

    # 社員番号が他の社員と重複していないかチェック(自分自身は除外)
    def clean_employee_number(self):
        employee_number = self.cleaned_data['employee_number']
        duplicates = Employee.objects.filter(employee_number=employee_number)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError('この社員番号は既に使用されています。')
        return employee_number

    def save(self):
        if self.instance is None:
            return self._create_employee()
        return self._update_employee()

    # UserとEmployeeを新規作成する
    def _create_employee(self):
        user = User.objects.create_user(
            username=self.cleaned_data['employee_number'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            password=self.cleaned_data['password'],
        )
        return Employee.objects.create(user=user, employee_number=self.cleaned_data['employee_number'])

    # 既存のUserとEmployeeを更新する(パスワードは入力があった場合のみ変更)
    def _update_employee(self):
        employee = self.instance
        employee.employee_number = self.cleaned_data['employee_number']
        employee.save()

        user = employee.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])
        user.save()
        return employee
