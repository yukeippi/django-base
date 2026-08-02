from django.db import models


# 会社情報のためのサンプルモデル
class Company(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='会社名')

    class Meta:
        ordering = ['name']
        verbose_name = '会社'
        verbose_name_plural = '会社'

    def __str__(self):
        return self.name
