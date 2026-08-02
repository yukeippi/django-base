from django.core.exceptions import ValidationError
from django.db import models
from app.models.employee import Employee
from app.models.department import Department


# 社員と部門の所属関係(主務/兼務)を表す中間モデル
class EmployeeDepartment(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='employee_departments', verbose_name='社員'
    )
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name='employee_departments', verbose_name='部門'
    )
    is_primary = models.BooleanField(default=False, verbose_name='主務')

    class Meta:
        verbose_name = '社員所属部門'
        verbose_name_plural = '社員所属部門'

    def __str__(self):
        return f'{self.employee} - {self.department}'

    # 同じ社員・部門の組み合わせが重複しないようにする(DB制約ではなくアプリ側でチェックする)
    def clean(self):
        duplicates = EmployeeDepartment.objects.filter(
            employee=self.employee, department=self.department
        ).exclude(pk=self.pk)
        if duplicates.exists():
            raise ValidationError('この社員は既にこの部門に所属しています。')

    # 主務(is_primary=True)を1人につき1件までにする(既存の主務があれば自動的にOFFにする)
    def save(self, *args, **kwargs):
        self.full_clean()
        if self.is_primary:
            EmployeeDepartment.objects.filter(
                employee=self.employee, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
