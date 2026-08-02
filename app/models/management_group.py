from django.db import models
from django.contrib.auth.models import User


# 権限レベルを持つグループ(社員情報・部門情報などの閲覧・編集範囲を決める)
class ManagementGroup(models.Model):
    VIEW = 'view'
    EDIT = 'edit'
    ADMIN = 'admin'
    PERMISSION_CHOICES = [
        (VIEW, '閲覧のみ'),
        (EDIT, '閲覧・編集'),
        (ADMIN, '全体管理者'),
    ]

    name = models.CharField(max_length=100, unique=True, verbose_name='管理グループ名')
    permission_level = models.CharField(
        max_length=10, choices=PERMISSION_CHOICES, default=VIEW, verbose_name='権限レベル'
    )
    members = models.ManyToManyField(User, related_name='management_groups', blank=True, verbose_name='メンバー')

    class Meta:
        ordering = ['name']
        verbose_name = '管理グループ'
        verbose_name_plural = '管理グループ'

    def __str__(self):
        return self.name
