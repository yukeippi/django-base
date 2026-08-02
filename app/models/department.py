from django.core.exceptions import ValidationError
from django.db import models
from app.models.company import Company


# 部門情報のためのサンプルモデル
class Department(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments', verbose_name='会社')
    name = models.CharField(max_length=100, verbose_name='部門名')

    class Meta:
        ordering = ['company', 'name']
        verbose_name = '部門'
        verbose_name_plural = '部門'

    def __str__(self):
        return f'{self.company.name} / {self.name}'

    # 同じ会社内で部門名が重複しないようにする(DB制約ではなくアプリ側でチェックする)
    def clean(self):
        duplicates = Department.objects.filter(company=self.company, name=self.name).exclude(pk=self.pk)
        if duplicates.exists():
            raise ValidationError('この会社には同じ名前の部門が既に存在します。')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
