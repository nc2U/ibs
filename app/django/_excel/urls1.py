from django.urls import path, include

# 앱별 내보내기 모듈에서 가져오기
from contract.exports import ExportContracts, ExportApplicants, ExportSuccessions, ExportReleases, ExportUnitStatus
from payment.exports import ExportPayments, ExportPaymentsByCont, ExportPaymentStatus, ExportOverallSummary
from cash.exports import ExportProjectBalance, ExportProjectDateCashbook, ExportBalanceByAcc, ExportDateCashbook, \
    export_cashbook_xls, export_project_cash_xls
from company.exports import ExportStaffs, ExportDeparts, ExportPositions, ExportDuties, ExportGrades

# 아직 마이그레이션되지 않은 클래스들 (기존 views.py에서)
from .views import (
    ExportBudgetExecutionStatus, ExportSites, ExportSitesByOwner,
    ExportSitesContracts, ExportSuitCases, ExportSuitCase
)

app_name = 'excel'

urlpatterns = [
    # Cash 관련 (새 모듈)
    path('p-balance/', ExportProjectBalance.as_view(), name='project-balance'),
    path('p-daily-cash/', ExportProjectDateCashbook.as_view(), name='project-daily-cash'),
    path('balance/', ExportBalanceByAcc.as_view(), name='balance'),
    path('daily-cash/', ExportDateCashbook.as_view(), name='daily-cash'),

    # 아직 마이그레이션되지 않은 항목들 (기존 views.py)
    path('p-budget/', ExportBudgetExecutionStatus.as_view(), name='budget'),
    path('p-cashbook/', export_project_cash_xls, name='project-cash'),
    path('sites/', ExportSites.as_view(), name='sites'),
    path('sites-by-owner/', ExportSitesByOwner.as_view(), name='sites-by-owner'),
    path('sites-contracts/', ExportSitesContracts.as_view(), name='sites-contracts'),
    path('cashbook/', export_cashbook_xls, name='cashbook'),
    path('suitcases/', ExportSuitCases.as_view(), name='suitcases'),
    path('suitcase/', ExportSuitCase.as_view(), name='suitcase'),
    path('staffs/', ExportStaffs.as_view(), name='staffs'),
    path('departs/', ExportDeparts.as_view(), name='departs'),
    path('positions/', ExportPositions.as_view(), name='positions'),
    path('duties/', ExportDuties.as_view(), name='duties'),
    path('grades/', ExportGrades.as_view(), name='grades'),
]
