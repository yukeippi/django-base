from django import forms
from app.models import ManagementGroup


# 管理グループの新規作成・編集で使うフォーム
class ManagementGroupForm(forms.ModelForm):
    class Meta:
        model = ManagementGroup
        fields = ['name', 'members', 'is_admin', 'department', 'permission_set_id']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'members': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'is_admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'permission_set_id': forms.NumberInput(attrs={'class': 'form-control'}),
        }
