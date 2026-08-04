from django.core.exceptions import ValidationError
from django.db import models
from app.models.department import Department


# 権限判定用の部門階層(親部門)を表すモデル。全ての部門がレコードを持つ必要はない
class DepartmentHierarchy(models.Model):
    department = models.OneToOneField(
        Department, on_delete=models.CASCADE, related_name='hierarchy', verbose_name='部門'
    )
    parent_department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.CASCADE,
        related_name='child_hierarchies', verbose_name='親部門'
    )

    class Meta:
        verbose_name = '部門階層'
        verbose_name_plural = '部門階層'

    def __str__(self):
        return f'{self.department} (親: {self.parent_department})'

    # 親部門は同じ会社に属していなければならない
    def clean(self):
        if self.parent_department and self.parent_department.company_id != self.department.company_id:
            raise ValidationError('親部門は同じ会社に属している必要があります。')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
