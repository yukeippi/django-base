from django.db import models
from django.contrib.auth.models import User


# ユーザーをグループ化するためのモデル(権限制御の設計は別途行う)
class ManagementGroup(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='管理グループ名')
    members = models.ManyToManyField(User, related_name='management_groups', blank=True, verbose_name='メンバー')

    class Meta:
        db_table = 'management_group'
        ordering = ['name']
        verbose_name = '管理グループ'
        verbose_name_plural = '管理グループ'

    def __str__(self):
        return self.name
