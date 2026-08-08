# 設計の決定経緯: docs/superpowers/specs/2026-08-08-access-control-design.md 参照
# - ルール形式: Claude Code settings.json風のallow/denyパターン文字列ではなく、AIが表に変換して
#   Confluenceに転記しやすいよう「1行=1権限」のフラットな辞書リスト形式を採用した
# - スコープ形式: 部門階層等の固定列挙型ではなく、実際の業務要件に合わせて任意のフィールドパスで
#   絞り込める汎用フィルタ辞書を採用した
#
# 新しい権限セットを追加する時は、このディレクトリにファイルを1つ追加し、
# 下記のimportとREGISTRYへの登録を1行ずつ足す。

from . import department_viewer_all
from . import company_scoped_department_manager

REGISTRY = {
    department_viewer_all.ID: department_viewer_all,
    company_scoped_department_manager.ID: company_scoped_department_manager,
}
