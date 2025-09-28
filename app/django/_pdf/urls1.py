from django.urls import path

# 앱별 PDF 내보내기 모듈에서 가져오기
from contract.exports import PdfExportBill
from payment.exports import PdfExportPayments, PdfExportCalculation

app_name = 'pdf'

urlpatterns = [
    # Contract PDF (새 모듈)
    path('bill/', PdfExportBill.as_view(), name='bill'),

    # Payment PDF (새 모듈)
    path('payments/', PdfExportPayments.as_view(), name='payments'),
    path('calculation/', PdfExportCalculation.as_view(), name='calculation'),

    # 새로운 앱별 라우팅 (향후 확장)
    # path('contract/', include('contract.exports.pdf_urls')),
    # path('payment/', include('payment.exports.pdf_urls')),
]
