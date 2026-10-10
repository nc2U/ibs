"""
PDF Export Common Mixins

공통 PDF 내보내기 기능을 제공하는 믹스인 클래스들
"""
from datetime import date, datetime

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import View
from weasyprint import HTML

from contract.models import Contract
from payment.models import InstallmentPaymentOrder

from urllib.parse import quote

class PdfExportMixin(View):
    """PDF 내보내기 공통 기능 믹스인"""

    @staticmethod
    def create_pdf_response(template_name, context, filename):
        """PDF 응답 생성 (메모리 버퍼 기반 생성으로 디스크 I/O 및 동시성 충돌 방지)"""
        html_string = render_to_string(template_name, context)
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf()

        encoded_filename = quote(f"{filename}.pdf" if not filename.lower().endswith('.pdf') else filename)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
        return response

    @staticmethod
    def get_base_context(**kwargs):
        """기본 컨텍스트 생성 (호출 시점의 현재 날짜 적용)"""
        context = {
            'pub_date': kwargs.get('pub_date', date.today()),
        }
        context.update(kwargs)
        return context


class ContractPdfMixin:
    """계약 관련 PDF 공통 기능"""

    @staticmethod
    def get_contract(cont_id):
        """계약 가져오기"""
        try:
            return Contract.objects.filter(pk=cont_id).first()
        except (ValueError, TypeError):
            return None

    @staticmethod
    def get_contract_unit(contract):
        """계약 동호수 정보 가져오기"""
        if not contract:
            return None
        try:
            return contract.key_unit.houseunit
        except AttributeError:
            return None

    @staticmethod
    def get_contract_content(contract, unit):
        """계약 내용 정보 구성"""
        if not contract:
            return {}

        contractor = getattr(contract, 'contractor', None)
        return {
            'contractor': contractor.name if contractor else '',
            'cont_date': contractor.contract_date if contractor else None,
            'cont_no': unit if unit else getattr(contract, 'serial_number', ''),
            'cont_type': getattr(contract, 'unit_type', None),
        }


class PaymentPdfMixin:
    """납부 관련 PDF 공통 기능"""

    @staticmethod
    def get_payment_orders(project):
        """납부 회차 정보 가져오기"""
        if not project:
            return InstallmentPaymentOrder.objects.none()
        return InstallmentPaymentOrder.objects.filter(project=project)

    @staticmethod
    def get_paid_list(contract, pub_date=None):
        """기 납부 목록 가져오기"""

        return [], 0


class DateUtilMixin:
    """날짜 관련 유틸리티"""

    @staticmethod
    def parse_date(date_string, default=None):
        """날짜 문자열 파싱 (기본값 미지정 시 호출 시점의 현재 날짜 적용)"""
        fallback_date = default if default is not None else date.today()
        if not date_string:
            return fallback_date

        try:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return fallback_date

    @staticmethod
    def format_date(date_obj, format_str='%Y-%m-%d'):
        """날짜 포맷팅"""
        if not date_obj:
            return ''
        return date_obj.strftime(format_str)

    @staticmethod
    def get_date_range_filter(start_date, end_date):
        """날짜 범위 필터 생성"""
        filters = {}
        if start_date:
            filters['deal_date__gte'] = start_date
        if end_date:
            filters['deal_date__lte'] = end_date
        return filters


class FormattingMixin:
    """데이터 포맷팅 관련 기능"""

    @staticmethod
    def format_currency(amount):
        """통화 형식으로 포맷"""
        if amount is None:
            return 0
        return f"{amount:,}"

    @staticmethod
    def format_percentage(value, decimal_places=2):
        """퍼센티지 형식으로 포맷"""
        if value is None:
            return "0%"
        return f"{value:.{decimal_places}f}%"

    @staticmethod
    def safe_division(dividend, divisor, default=0):
        """안전한 나눗셈"""
        try:
            return dividend / divisor if divisor != 0 else default
        except (TypeError, ZeroDivisionError):
            return default


class PdfUtilsMixin:
    """PDF 관련 유틸리티 기능"""

    @staticmethod
    def get_blank_line_count(content_count, max_lines=14):
        """공백 라인 수 계산"""
        blank_count = max_lines - content_count
        return max(0, blank_count)

    @staticmethod
    def create_filename(base_name, identifier=None, extension='pdf'):
        """파일명 생성"""
        filename_parts = [base_name]

        if identifier:
            filename_parts.append(str(identifier))

        filename = '_'.join(filename_parts)
        return f"{filename}.{extension}"

    @staticmethod
    def paginate_data(data_list, items_per_page=20):
        """데이터 페이지네이션"""
        paginated_data = []
        for i in range(0, len(data_list), items_per_page):
            paginated_data.append(data_list[i:i + items_per_page])
        return paginated_data
