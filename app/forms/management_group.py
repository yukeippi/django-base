from django import forms
from app.models import ManagementGroup


# 管理グループの新規作成・編集で使うフォーム
class ManagementGroupForm(forms.ModelForm):
    class Meta:
        model = ManagementGroup
        fields = ['name', 'permission_level', 'members']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'permission_level': forms.Select(attrs={'class': 'form-select'}),
            'members': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }
