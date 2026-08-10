from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from app.models.department import Department
from app.permissions import rule_sets


# ユーザーをグループ化し、権限を付与するためのモデル
class ManagementGroup(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='管理グループ名')
    members = models.ManyToManyField(User, related_name='management_groups', blank=True, verbose_name='メンバー')
    is_admin = models.BooleanField(default=False, verbose_name='全社管理者')
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.CASCADE,
        related_name='management_groups', verbose_name='割当部門'
    )
    permission_set_id = models.IntegerField(null=True, blank=True, verbose_name='権限セット番号')

    class Meta:
        db_table = 'management_group'
        ordering = ['name']
        verbose_name = '管理グループ'
        verbose_name_plural = '管理グループ'

    def __str__(self):
        return self.name

    # is_adminと部門・権限セット設定の整合性を検証する(全社管理者は部門・権限セットを持たず、それ以外は両方必須)
    def clean(self):
        if self.is_admin and self.department_id is not None:
            raise ValidationError({'department': '全社管理者グループには部門を設定できません。'})
        if not self.is_admin and self.department_id is None:
            raise ValidationError({'department': '全社管理者でない場合は部門の設定が必須です。'})
        if self.is_admin and self.permission_set_id is not None:
            raise ValidationError({'permission_set_id': '全社管理者グループには権限セットを設定できません。'})
        if not self.is_admin and self.permission_set_id is None:
            raise ValidationError({'permission_set_id': '全社管理者でない場合は権限セットの設定が必須です。'})
        if not self.is_admin and self.permission_set_id not in rule_sets.REGISTRY:
            raise ValidationError({'permission_set_id': '存在しない権限セット番号です。'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
