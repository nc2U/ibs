from django.urls import path

# 앱별 내보내기 모듈에서 가져오기
from notice.exports.pdf import PdfExportBill
from payment.exports.pdf import (
    PdfExportPayments, PdfExportDailyLateFee, PdfExportCalculation,
    PdfExportLedgerPayment, PdfExportLedgerDailyLateFee, PdfExportLedgerCalculation
)
from contract.exports.pdf import PdfExportCertOccupancy

app_name = 'pdf'

urlpatterns = [
    # Notice 관련
    path('bill/', PdfExportBill.as_view(), name='bill'),

    # Payment 관련
    path('payments/', PdfExportPayments.as_view(), name='payments'),
    path('daily-late-fee/', PdfExportDailyLateFee.as_view(), name='daily-late-fee'),
    path('calculation/', PdfExportCalculation.as_view(), name='calculation'),

    path('ledger/payment/', PdfExportLedgerPayment.as_view(), name='ledger-payment'),
    path('ledger/daily-late-fee/', PdfExportLedgerDailyLateFee.as_view(), name='ledger-daily-late-fee'),
    path('ledger/calculation/', PdfExportLedgerCalculation.as_view(), name='ledger-calculation'),

    # Contract 관련
    path('cert-occupancy/', PdfExportCertOccupancy.as_view(), name='cert-occupancy'),
]
