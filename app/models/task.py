from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from app.validators import ContainsCharacterValidator


# タスク管理のためのサンプルモデル
class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]

    title = models.CharField(max_length=200, verbose_name='タイトル')
    # サンプル: 自作の(__call__を実装した)カスタムバリデータクラスを使う例。
    # 説明を入力する場合は、関連するIssue番号(#123のような形式)を含めることを求める。
    description = models.TextField(
        blank=True,
        verbose_name='説明',
        validators=[ContainsCharacterValidator('#', message='説明には関連するIssue番号(例: #123)を含めてください。')],
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='todo',
        verbose_name='ステータス'
    )
    priority = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='優先度'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name='担当者'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tasks',
        verbose_name='作成者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    due_date = models.DateField(null=True, blank=True, verbose_name='期限')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'タスク'
        verbose_name_plural = 'タスク'

    def __str__(self):
        return self.title

    # 期限を過ぎているかチェック
    def is_overdue(self):
        if not self.due_date:
            return False
        from django.utils import timezone
        return self.due_date < timezone.now().date() and self.status != 'done'

    # 完了可能かチェック
    def can_be_completed(self):
        return self.status in ['todo', 'in_progress']
