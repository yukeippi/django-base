from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


# 指定した文字を含むことを要求するバリデータ
# @deconstructibleを付けないと、マイグレーションファイルにこのバリデータのインスタンスを
# 書き出す(シリアライズする)ことができずエラーになる
@deconstructible
class ContainsCharacterValidator:
    def __init__(self, character, message=None):
        self.character = character
        self.message = message or f'{character}を含めてください。'

    def __call__(self, value):
        if self.character not in value:
            raise ValidationError(self.message)
