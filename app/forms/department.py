from django import forms
from app.models import Department


# 部門の新規作成・編集で使うフォーム
class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['company', 'name']
        widgets = {
            'company': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }
