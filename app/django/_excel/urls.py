from django.urls import path

# 앱별 내보내기 모듈에서 가져오기
from company.exports import ExportStaffs, ExportDeparts, ExportPositions, ExportDuties, ExportGrades
from project.exports import ExportSites, ExportSitesByOwner, ExportSitesContracts
from contract.exports import ExportContracts, ExportSuccessions, ExportReleases, ExportUnitStatus
from payment.exports import ExportPayments, ExportPaymentsByCont, ExportPaymentStatus, ExportOverallSummary
from cash.exports import (ExportProjectBalance, ExportProjectDateCashbook, ExportBalanceByAcc,
                          ExportBudgetExecutionStatus, ExportCashFlowForm, ExportDateCashbook,
                          export_cashbook_xls, export_project_cash_xls)

from docs.exports import ExportSuitCases, ExportSuitCase

app_name = 'excel'

urlpatterns = [
    # Company 관련 (새 모듈)
    path('staffs/', ExportStaffs.as_view(), name='staffs'),
    path('departs/', ExportDeparts.as_view(), name='departs'),
    path('positions/', ExportPositions.as_view(), name='positions'),
    path('duties/', ExportDuties.as_view(), name='duties'),
    path('grades/', ExportGrades.as_view(), name='grades'),

    # Project - site 관련 (새 모듈)
    path('sites/', ExportSites.as_view(), name='sites'),
    path('sites-by-owner/', ExportSitesByOwner.as_view(), name='sites-by-owner'),
    path('sites-contracts/', ExportSitesContracts.as_view(), name='sites-contracts'),

    # Contract 관련 (새 모듈)
    path('contracts/', ExportContracts.as_view(), name='contracts'),
    path('successions/', ExportSuccessions.as_view(), name='successions'),
    path('releases/', ExportReleases.as_view(), name='releases'),
    path('status/', ExportUnitStatus.as_view(), name='unit-status'),

    # Payment 관련 (새 모듈)
    path('payments/', ExportPayments.as_view(), name='payments'),
    path('paid-by-cont/', ExportPaymentsByCont.as_view(), name='paid-by-cont'),
    path('paid-status/', ExportPaymentStatus.as_view(), name='paid-status'),
    path('overall-sum/', ExportOverallSummary.as_view(), name='overall-summary'),

    # Cash 관련 (새 모듈)
    path('p-balance/', ExportProjectBalance.as_view(), name='project-balance'),
    path('p-daily-cash/', ExportProjectDateCashbook.as_view(), name='project-daily-cash'),
    path('p-budget/', ExportBudgetExecutionStatus.as_view(), name='budget'),
    path('cash-flow-form/', ExportCashFlowForm.as_view(), name='cash-flow-form'),
    path('p-cashbook/', export_project_cash_xls, name='project-cash'),
    path('balance/', ExportBalanceByAcc.as_view(), name='balance'),
    path('daily-cash/', ExportDateCashbook.as_view(), name='daily-cash'),
    path('cashbook/', export_cashbook_xls, name='cashbook'),

    # Docs 관련 (새 모듈)
    path('suitcases/', ExportSuitCases.as_view(), name='suitcases'),
    path('suitcase/', ExportSuitCase.as_view(), name='suitcase'),
]
