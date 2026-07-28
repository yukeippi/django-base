from django import forms
from app.models import Task


# タスクの新規作成・編集で使うフォーム
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'assigned_to', 'due_date']
