from app.models import Company


# 会社のシードデータを作成する
def create():
    Company.objects.create(name='サンプル株式会社')
    Company.objects.create(name='テスト工業株式会社')
