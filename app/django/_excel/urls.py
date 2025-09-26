from django.urls import path
from .views import *

app_name = 'excel'

urlpatterns = [
    path('contracts/', ExportContracts.as_view(), name='contracts'),
    path('reservations/', ExportApplicants.as_view(), name='reservations'),
    path('successions/', ExportSuccessions.as_view(), name='successions'),
    path('releases/', ExportReleases.as_view(), name='releases'),
    path('status/', ExportUnitStatus.as_view(), name='unit-status'),
    # path('payments/', export_payments_xls, name='payments'),
    path('payments/', ExportPayments.as_view(), name='payments'),
    path('paid-by-cont/', ExportPaymentsByCont.as_view(), name='paid-by-cont'),
    path('paid-status/', ExportPaymentStatus.as_view(), name='paid-status'),
    path('overall-sum/', ExportOverallSummary.as_view(), name='overall-summary'),
    path('p-balance/', ExportProjectBalance.as_view(), name='project-balance'),
    path('p-daily-cash/', ExportProjectDateCashbook.as_view(), name='project-daily-cash'),
    path('p-budget/', ExportBudgetExecutionStatus.as_view(), name='budget'),
    path('p-cashbook/', export_project_cash_xls, name='project-cash'),
    path('sites/', ExportSites.as_view(), name='sites'),
    path('sites-by-owner/', ExportSitesByOwner.as_view(), name='sites-by-owner'),
    path('sites-contracts/', ExportSitesContracts.as_view(), name='sites-contracts'),
    path('balance/', ExportBalanceByAcc.as_view(), name='balance'),
    path('daily-cash/', ExportDateCashbook.as_view(), name='daily-cash'),
    path('cashbook/', export_cashbook_xls, name='cashbook'),
    path('suitcases/', ExportSuitCases.as_view(), name='suitcases'),
    path('suitcase/', ExportSuitCase.as_view(), name='suitcase'),
    path('staffs/', ExportStaffs.as_view(), name='staffs'),
    path('departs/', ExportDeparts.as_view(), name='departs'),
    path('positions/', ExportPositions.as_view(), name='positions'),
    path('duties/', ExportDuties.as_view(), name='duties'),
    path('grades/', ExportGrades.as_view(), name='grades'),
]
