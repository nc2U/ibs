from django.urls import path

# 앱별 내보내기 모듈에서 가져오기
from company.exports import ExportStaffs, ExportDeparts, ExportPositions, ExportDuties, ExportGrades
# 아직 마이그레이션되지 않은 클래스들 (기존 views.py에서)
from .views import (
    ExportSites, ExportSitesByOwner,
    ExportSitesContracts, ExportSuitCases, ExportSuitCase
)

app_name = 'excel'

urlpatterns = [
    # 아직 마이그레이션되지 않은 항목들 (기존 views.py)

    path('suitcases/', ExportSuitCases.as_view(), name='suitcases'),
    path('suitcase/', ExportSuitCase.as_view(), name='suitcase'),
    path('staffs/', ExportStaffs.as_view(), name='staffs'),
    path('departs/', ExportDeparts.as_view(), name='departs'),
    path('positions/', ExportPositions.as_view(), name='positions'),
    path('duties/', ExportDuties.as_view(), name='duties'),
    path('grades/', ExportGrades.as_view(), name='grades'),
]
