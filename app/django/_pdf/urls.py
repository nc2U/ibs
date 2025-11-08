from django.urls import path

# 앱별 내보내기 모듈에서 가져오기
from notice.exports.pdf import PdfExportBill
from payment.exports.pdf import PdfExportPayments, PdfExportDailyLateFee, PdfExportCalculation
from contract.exports.pdf import PdfExportCertOccupancy

app_name = 'pdf'

urlpatterns = [
    # Notice 관련
    path('bill/', PdfExportBill.as_view(), name='bill'),

    # Payment 관련
    path('payments/', PdfExportPayments.as_view(), name='payments'),
    path('daily-late-fee/', PdfExportDailyLateFee.as_view(), name='daily-late-fee'),
    path('calculation/', PdfExportCalculation.as_view(), name='calculation'),
    path('cert-occupancy/', PdfExportCertOccupancy.as_view(), name='cert-occupancy'),
]
