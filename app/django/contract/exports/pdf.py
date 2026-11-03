"""
Contract PDF Export Views

계약 관련 PDF 내보내기 뷰들 (고지서 등)
"""
from datetime import date

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import View
from weasyprint import HTML

from _pdf.mixins import PdfExportMixin
from _pdf.utils import get_contract
from apiV1.permissions._utils import get_project_ids_with_permission


class PdfExportCertOccupancy(PdfExportMixin, View):

    def get(self, request):
        user = getattr(request, 'user', None)
        if user is not None:
            if not user.is_authenticated:
                return HttpResponse("로그인이 필요합니다.", status=401, content_type='text/plain; charset=utf-8')

        contract_id = request.GET.get('contract')
        if not contract_id:
            return HttpResponse("계약 ID('contract') 파라미터가 필요합니다.", status=400, content_type='text/plain; charset=utf-8')

        try:
            contract = get_contract(contract_id)
        except (Exception,):
            return HttpResponse("존재하지 않거나 유효하지 않은 계약 ID입니다.", status=404, content_type='text/plain; charset=utf-8')

        if user is not None and user.is_authenticated and not (user.is_superuser or getattr(user, 'work_manager', False)):
            allowed_ids = get_project_ids_with_permission(user, 'contract.read')
            if contract.project_id not in allowed_ids:
                return HttpResponse("해당 계약의 증명서를 발급받을 권한이 없습니다.", status=403, content_type='text/plain; charset=utf-8')

        # context
        context = dict()
        context['contract'] = contract  # 계약 건 객체
        context['is_calc'] = True if request.GET.get('is_calc') else False  # 1 = 일반용(할인가산 포함) / '' = 확인용
        context['pub_date'] = date.today()  # 발행일자
        context['user'] = user.username if user and user.is_authenticated else 'Administrator'  # 사용자정보

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

        filename = request.GET.get('filename', 'cert-occupancy')
        return self.create_pdf_response_from_string(html_string, filename)

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
