from io import StringIO
from django.core.management import call_command
from django.test import override_settings


# app/management/commands/notes.pyのテストクラス
class TestNotesCommand:

    # TODOコメントが1件も無い場合、その旨のメッセージが出力されることを確認
    def test_no_notes_found(self, tmp_path):
        (tmp_path / 'app').mkdir()
        (tmp_path / 'app' / 'sample.py').write_text('# 通常のコメント\n')

        with override_settings(BASE_DIR=tmp_path):
            out = StringIO()
            call_command('notes', stdout=out)

        assert '該当するコメントは見つかりませんでした。' in out.getvalue()

    # Pythonファイル中のTODOコメントが検出されることを確認
    def test_detects_todo_in_python_file(self, tmp_path):
        (tmp_path / 'app').mkdir()
        (tmp_path / 'app' / 'sample.py').write_text('# 通常のコメント\n# TODO: 後で直す\n')

        with override_settings(BASE_DIR=tmp_path):
            out = StringIO()
            call_command('notes', stdout=out)

        output = out.getvalue()
        assert 'app/sample.py' in output
        assert '[2] TODO 後で直す' in output

    # HTMLファイル中のTODOコメントが検出されることを確認
    def test_detects_todo_in_html_file(self, tmp_path):
        (tmp_path / 'app').mkdir()
        (tmp_path / 'app' / 'sample.html').write_text('<!-- TODO: テンプレートを整える -->\n')

        with override_settings(BASE_DIR=tmp_path):
            out = StringIO()
            call_command('notes', stdout=out)

        output = out.getvalue()
        assert 'app/sample.html' in output
        assert '[1] TODO テンプレートを整える' in output

    # --tagオプションで指定したタグのみ抽出されることを確認
    def test_tag_option_filters_by_tag(self, tmp_path):
        (tmp_path / 'app').mkdir()
        (tmp_path / 'app' / 'sample.py').write_text('# TODO: todoの方\n# FIXME: fixmeの方\n')

        with override_settings(BASE_DIR=tmp_path):
            out = StringIO()
            call_command('notes', tag='FIXME', stdout=out)

        output = out.getvalue()
        assert 'fixmeの方' in output
        assert 'todoの方' not in output

    # migrationsディレクトリ配下は除外されることを確認
    def test_excludes_migrations_directory(self, tmp_path):
        migrations_dir = tmp_path / 'app' / 'migrations'
        migrations_dir.mkdir(parents=True)
        (migrations_dir / '0001_initial.py').write_text('# TODO: 無視されるはず\n')

        with override_settings(BASE_DIR=tmp_path):
            out = StringIO()
            call_command('notes', stdout=out)

        assert '該当するコメントは見つかりませんでした。' in out.getvalue()
