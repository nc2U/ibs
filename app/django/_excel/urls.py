from django.urls import path

from cash.exports import (ExportProjectBalance, ExportProjectDateCashbook, ExportBalanceByAcc,
                          ExportBudgetExecutionStatus, ExportCashFlowForm, ExportDateCashbook,
                          export_cashbook_xls)
# 앱별 내보내기 모듈에서 가져오기
from company.exports import ExportStaffs, ExportDeparts, ExportPositions, ExportDuties, ExportGrades
from contract.exports import ExportContracts, ExportSuccessions, ExportReleases, ExportUnitStatus
from docs.exports import ExportSuitCases, ExportSuitCase
from ledger.exports import export_pro_transaction_xls, export_com_transaction_xls
from payment.exports import (ExportPayments, ExportPaymentsByCont, ExportPaymentStatus, ExportOverallSummary,
                             ExportLedgerPaymentStatus, ExportLedgerOverallSummary)
from project.exports import ExportSites, ExportSitesByOwner, ExportSitesContracts

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

    path('ledger/payment/', ExportPayments.as_view(), name='ledger-payment'),
    path('ledger/paid-by-cont/', ExportPaymentsByCont.as_view(), name='ledger-paid-by-cont'),
    path('ledger/paid-status/', ExportLedgerPaymentStatus.as_view(), name='ledger-paid-status'),
    path('ledger/overall-sum/', ExportLedgerOverallSummary.as_view(), name='ledger-overall-summary'),

    # Cash 관련 (새 모듈)
    path('p-balance/', ExportProjectBalance.as_view(), name='project-balance'),
    path('p-daily-cash/', ExportProjectDateCashbook.as_view(), name='project-daily-cash'),
    path('p-budget/', ExportBudgetExecutionStatus.as_view(), name='budget'),
    path('cash-flow-form/', ExportCashFlowForm.as_view(), name='cash-flow-form'),
    path('pro-transaction/', export_pro_transaction_xls, name='pro-transaction'),
    path('balance/', ExportBalanceByAcc.as_view(), name='balance'),
    path('daily-cash/', ExportDateCashbook.as_view(), name='daily-cash'),
    path('cashbook/', export_cashbook_xls, name='cashbook'),
    path('com-transaction/', export_com_transaction_xls, name='com-transaction'),

    # Docs 관련 (새 모듈)
    path('suitcases/', ExportSuitCases.as_view(), name='suitcases'),
    path('suitcase/', ExportSuitCase.as_view(), name='suitcase'),
]
