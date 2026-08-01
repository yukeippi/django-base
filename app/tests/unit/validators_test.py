import pytest
from django.core.exceptions import ValidationError
from app.models import Task
from app.validators import ContainsCharacterValidator


# ContainsCharacterValidator単体のテストクラス
class TestContainsCharacterValidator:

    # 指定した文字が含まれていれば例外が発生しないことを確認
    def test_valid_when_character_present(self):
        validator = ContainsCharacterValidator('@')
        validator('user@example.com')

    # 指定した文字が含まれていなければValidationErrorが発生することを確認
    def test_invalid_when_character_missing(self):
        validator = ContainsCharacterValidator('@')
        with pytest.raises(ValidationError):
            validator('user-example.com')

    # messageを指定した場合、そのメッセージがエラーに使われることを確認
    def test_custom_message_is_used(self):
        validator = ContainsCharacterValidator('@', message='カスタムメッセージ')
        with pytest.raises(ValidationError, match='カスタムメッセージ'):
            validator('invalid')


# Task.descriptionへの適用箇所のテストクラス
@pytest.mark.django_db
class TestTaskDescriptionValidator:

    # 説明が空の場合はバリデータが適用されないことを確認
    def test_blank_description_is_valid(self):
        task = Task(title='Task', description='')
        task.full_clean()

    # 説明に#が含まれる場合は妥当であることを確認
    def test_description_with_hash_is_valid(self):
        task = Task(title='Task', description='関連Issue: #123')
        task.full_clean()

    # 説明に#が含まれない場合はValidationErrorが発生することを確認
    def test_description_without_hash_is_invalid(self):
        task = Task(title='Task', description='Issue番号を含まない説明文')
        with pytest.raises(ValidationError):
            task.full_clean()
