"""
PDF Export Common Mixins

공통 PDF 내보내기 기능을 제공하는 믹스인 클래스들
"""
from datetime import date, datetime

from django.core.files.storage import FileSystemStorage
from django.db.models import Sum
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import View
from weasyprint import HTML

from cash.models import ProjectCashBook
from contract.models import Contract
from payment.models import InstallmentPaymentOrder

TODAY = date.today()


class PdfExportMixin(View):
    """PDF 내보내기 공통 기능 믹스인"""

    @staticmethod
    def create_pdf_response(template_name, context, filename):
        """PDF 응답 생성"""
        html_string = render_to_string(template_name, context)
        html = HTML(string=html_string)
        html.write_pdf(target='/tmp/mypdf.pdf')

        fs = FileSystemStorage('/tmp')
        with fs.open('mypdf.pdf') as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            return response

    @staticmethod
    def get_base_context(**kwargs):
        """기본 컨텍스트 생성"""
        context = {
            'pub_date': kwargs.get('pub_date', TODAY),
        }
        context.update(kwargs)
        return context


class ContractPdfMixin:
    """계약 관련 PDF 공통 기능"""

    @staticmethod
    def get_contract(cont_id):
        """계약 가져오기"""

        return Contract.objects.get(pk=cont_id)

    @staticmethod
    def get_contract_unit(contract):
        """계약 동호수 정보 가져오기"""
        try:
            return contract.key_unit.houseunit
        except AttributeError:
            return None

    @staticmethod
    def get_contract_content(contract, unit):
        """계약 내용 정보 구성"""
        return {
            'contractor': contract.contractor.name,
            'cont_date': contract.contractor.contract_date,
            'cont_no': unit if unit else contract.serial_number,
            'cont_type': contract.unit_type,
        }


class PaymentPdfMixin:
    """납부 관련 PDF 공통 기능"""

    @staticmethod
    def get_payment_orders(project):
        """납부 회차 정보 가져오기"""

        return InstallmentPaymentOrder.objects.filter(project=project)

    @staticmethod
    def get_paid_list(contract, pub_date=None):
        """기 납부 목록 가져오기"""

        queryset = ProjectCashBook.objects.filter(
            income__isnull=False,
            project_account_d3__is_payment=True,
            contract=contract,
        )

        if pub_date:
            queryset = queryset.filter(deal_date__lte=pub_date)

        paid_list = queryset.order_by('deal_date', 'id')
        paid_sum_total = paid_list.aggregate(Sum('income'))['income__sum']
        paid_sum_total = paid_sum_total if paid_sum_total else 0

        return paid_list, paid_sum_total


class DateUtilMixin:
    """날짜 관련 유틸리티"""

    @staticmethod
    def parse_date(date_string, default=None):
        """날짜 문자열 파싱"""
        if not date_string:
            return default or TODAY

        try:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        except ValueError:
            return default or TODAY

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
