"""
Contract PDF Export Views

계약 관련 PDF 내보내기 뷰들 (고지서 등)
"""
from datetime import date, datetime

from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import View
from weasyprint import HTML

from _pdf.utils import get_contract

TODAY = date.today()


class PdfExportCertOccupancy(View):

    @staticmethod
    def get(request):
        context = dict()

        project = request.GET.get('project')  # 프로젝트 ID
        # 계약 건 객체
        cont_id = request.GET.get('contract')
        context['contract'] = contract = get_contract(cont_id)
        context['is_calc'] = calc = True if request.GET.get('is_calc') else False  # 1 = 일반용(할인가산 포함) / '' = 확인용

        # 발행일자
        pub_date = request.GET.get('date', None)
        pub_date = datetime.strptime(pub_date, '%Y-%m-%d').date() if pub_date else TODAY
        context['pub_date'] = pub_date

        # ----------------------------------------------------------------

        html_string = render_to_string('pdf/certification-occupancy.html', context)

        # 가로 방향 페이지 설정을 위한 CSS 추가
        landscape_css = """
        <style>
        @page {
            size: A4 landscape;
            margin: 5mm;
        }
        body {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: hidden;
        }
        #page-container {
            transform: scale(0.77);
            transform-origin: 0 0;
            width: 100%;
            height: 100%;
        }
        .pf {
            margin: 0 !important;
            box-shadow: none !important;
        }
        </style>
        """

        # HTML 문서의 head 섹션에 CSS 추가
        if '<head>' in html_string:
            html_string = html_string.replace('<head>', f'<head>{landscape_css}', 1)
        else:
            html_string = f'<html><head>{landscape_css}</head><body>{html_string}</body></html>'

        html = HTML(string=html_string)
        html.write_pdf(target='/tmp/mypdf.pdf')

        fs = FileSystemStorage('/tmp')
        with fs.open('mypdf.pdf') as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="cert-occupancy.pdf"'
            return response