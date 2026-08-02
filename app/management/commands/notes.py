import re
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand

DEFAULT_TAGS = ['TODO', 'FIXME', 'OPTIMIZE']
SEARCH_DIRS = ['app', 'config', 'common']
EXCLUDE_DIR_NAMES = {'migrations', '__pycache__', 'node_modules', '.venv'}
COMMENT_PATTERNS = {
    '.py': r'#\s*(?P<tag>{tags})[:\s]+(?P<text>.+)',
    '.html': r'<!--\s*(?P<tag>{tags})[:\s]+(?P<text>.+?)\s*-->',
}


# コード中のTODO/FIXME/OPTIMIZEコメントを一覧表示する(rails notesのDjango版)
class Command(BaseCommand):
    help = 'コード中のTODO/FIXME/OPTIMIZEコメントを一覧表示する(rails notesのDjango版)'

    def add_arguments(self, parser):
        parser.add_argument('--tag', help='特定のタグのみ表示する(例: TODO)')

    def handle(self, *args, **options):
        tags = [options['tag'].upper()] if options['tag'] else DEFAULT_TAGS
        notes_by_file = self._collect_notes(tags)

        if not notes_by_file:
            self.stdout.write('該当するコメントは見つかりませんでした。')
            return

        for file_path, notes in sorted(notes_by_file.items()):
            self.stdout.write(str(file_path))
            for line_number, tag, text in notes:
                self.stdout.write(f'  * [{line_number}] {tag} {text}')

    # 対象ディレクトリを走査し、ファイルごとの注釈一覧を返す
    def _collect_notes(self, tags):
        base_dir = Path(settings.BASE_DIR)
        notes_by_file = {}
        for dir_name in SEARCH_DIRS:
            search_dir = base_dir / dir_name
            if not search_dir.is_dir():
                continue
            for path in search_dir.rglob('*'):
                if not path.is_file() or path.suffix not in COMMENT_PATTERNS:
                    continue
                if EXCLUDE_DIR_NAMES & set(path.parts):
                    continue
                notes = self._find_notes(path, tags)
                if notes:
                    notes_by_file[path.relative_to(base_dir)] = notes
        return notes_by_file

    # 1ファイル分の注釈([行番号, タグ, 本文]のリスト)を抽出する
    def _find_notes(self, path, tags):
        pattern = re.compile(COMMENT_PATTERNS[path.suffix].format(tags='|'.join(tags)))
        notes = []
        for line_number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
            match = pattern.search(line)
            if match:
                notes.append((line_number, match.group('tag'), match.group('text').strip()))
        return notes
