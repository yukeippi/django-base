from django.db import models
from django.contrib.auth.models import User


# 社員情報のためのサンプルモデル
class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee', verbose_name='ユーザー')
    # ログインIDとして使用する社員番号
    employee_number = models.CharField(max_length=20, unique=True, verbose_name='社員番号')

    class Meta:
        verbose_name = '社員'
        verbose_name_plural = '社員'

    def __str__(self):
        return self.user.get_full_name() or self.user.username
