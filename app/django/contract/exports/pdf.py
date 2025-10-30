"""
Contract PDF Export Views

계약 관련 PDF 내보내기 뷰들 (고지서 등)
"""
from datetime import date

from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import View
from weasyprint import HTML

from _pdf.utils import get_contract


class PdfExportCertOccupancy(View):

    def get(self, request):

        # context
        context = dict()
        context['contract'] = get_contract(request.GET.get('contract'))  # 계약 건 객체
        context['is_calc'] = True if request.GET.get('is_calc') else False  # 1 = 일반용(할인가산 포함) / '' = 확인용
        context['pub_date'] = date.today()  # 발행일자
        context['user'] = request.user.username  # 사용자정보

        # ----------------------------------------------------------------
        template_name = 'pdf/certification-occupancy.html'
        html_string = render_to_string(template_name, context)

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
        /* PDF2htmlEX 로고 및 UI 요소 숨기기 */
        .loading-indicator,
        .loading-indicator.active,
        #sidebar,
        #outline,
        .checked,
        .bi[style*="background"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
        }
        </style>
        """

        # HTML 문서의 head 섹션에 CSS 추가
        if '<head>' in html_string:
            html_string = html_string.replace('<head>', f'<head>{landscape_css}', 1)
        else:
            html_string = f'<html><head>{landscape_css}</head><body>{html_string}</body></html>'

        # 동적 텍스트 오버레이 추가
        overlay_text = self.generate_text_overlay(context)

        # HTML 문서의 body 끝에 오버레이 텍스트 추가
        if '</body>' in html_string:
            html_string = html_string.replace('</body>', f'{overlay_text}</body>')
        else:
            html_string = html_string + overlay_text

        html = HTML(string=html_string)
        html.write_pdf(target='/tmp/mypdf.pdf')

        filename = request.GET.get('filename', 'cert-occupancy')

        fs = FileSystemStorage('/tmp')
        with fs.open('mypdf.pdf') as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            return response

    @staticmethod
    def generate_text_overlay(context):
        """이미지 위에 텍스트 오버레이 생성"""
        contract = context.get('contract')
        pub_date_obj = context.get('pub_date')
        pub_date = pub_date_obj.strftime(f'%Y{"&nbsp;" * 8}%m{"&nbsp;" * 8}%d') if pub_date_obj else ""
        user = context.get('user')

        if not contract:
            return ""

        # 프로젝트 정보
        project = contract.project
        project_name = project.name if project else ""
        project_location = project.location if project else ""

        # 동호수 정보
        unit_info = ""
        try:
            if hasattr(contract, 'key_unit') and contract.key_unit:
                unit_info = str(contract.key_unit.houseunit) if hasattr(contract.key_unit, 'houseunit') else ""
        except:
            unit_info = ""

        # 텍스트 오버레이 HTML 생성 (예시 좌표 - 실제 좌표는 조정 필요)
        overlay_html = f"""
        <!-- 동적 텍스트 오버레이 -->
        <div style="position: absolute; top: 187px; left: 150px; font-size: 12px; z-index: 10;">
            {project_name}
        </div>
        <div style="position: absolute; top: 187px; left: 476px; font-size: 12px; z-index: 10;">
            {project_name}
        </div>
        <div style="position: absolute; top: 187px; left: 804px; font-size: 12px; z-index: 10;">
            {project_name}
        </div>
        
        <div style="position: absolute; top: 217px; left: 150px; font-size: 9px; z-index: 10;">
            {project_location}
        </div>
        <div style="position: absolute; top: 217px; left: 476px; font-size: 9px; z-index: 10;">
            {project_location}
        </div>
        <div style="position: absolute; top: 217px; left: 804px; font-size: 9px; z-index: 10;">
            {project_location}
        </div>
        
        <div style="position: absolute; top: 247px; left: 150px; font-size: 12px; z-index: 10;">
            {unit_info}
        </div>
        <div style="position: absolute; top: 247px; left: 476px; font-size: 12px; z-index: 10;">
            {unit_info}
        </div>
        <div style="position: absolute; top: 247px; left: 804px; font-size: 12px; z-index: 10;">
            {unit_info}
        </div>
        
        <div style="position: absolute; top: 518px; left: 180px; font-size: 12px; z-index: 10;">
            {pub_date}
        </div>
        <div style="position: absolute; top: 518px; left: 506px; font-size: 12px; z-index: 10;">
            {pub_date}
        </div>
        <div style="position: absolute; top: 518px; left: 834px; font-size: 12px; z-index: 10;">
            {pub_date}
        </div>
        
        <div style="position: absolute; top: 600px; left: 530px; font-size: 12px; z-index: 10;">
            {project_name}
        </div>
        <div style="position: absolute; top: 604px; left: 855px; font-size: 12px; z-index: 10;">
            {project_name}
        </div>
        
        <div style="position: absolute; top: 642px; left: 530px; font-size: 12px; z-index: 10;">
            {user}
        </div>
        <div style="position: absolute; top: 642px; left: 855px; font-size: 12px; z-index: 10;">
            {user}
        </div>
        """

        return overlay_html
