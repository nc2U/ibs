from django.urls import path

from contract.exports.pdf import PdfExportCertOccupancy
# 앱별 내보내기 모듈에서 가져오기
from notice.exports.pdf import PdfExportBill
from payment.exports.pdf import (
    PdfExportLedgerPayment, PdfExportLedgerDailyLateFee, PdfExportLedgerCalculation
)

app_name = 'pdf'

urlpatterns = [
    # Notice 관련
    path('bill/', PdfExportBill.as_view(), name='bill'),

    # Payment 관련
    path('ledger/payment/', PdfExportLedgerPayment.as_view(), name='ledger-payment'),
    path('ledger/daily-late-fee/', PdfExportLedgerDailyLateFee.as_view(), name='ledger-daily-late-fee'),
    path('ledger/calculation/', PdfExportLedgerCalculation.as_view(), name='ledger-calculation'),

    # Contract 관련
    path('cert-occupancy/', PdfExportCertOccupancy.as_view(), name='cert-occupancy'),
]
