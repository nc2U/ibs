"""
Excel Export Common Mixins

공통 Excel 내보내기 기능을 제공하는 믹스인 클래스들
"""
import datetime
import io
from django.http import HttpResponse
from django.views.generic import View
import xlsxwriter

from project.models import Project

TODAY = datetime.date.today().strftime('%Y-%m-%d')


class ExcelExportMixin(View):
    """Excel 내보내기 공통 기능 믹스인"""

    @staticmethod
    def create_workbook(sheet_name=None):
        """워크북과 워크시트 생성"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(sheet_name or '데이터')
        worksheet.set_default_row(20)
        return output, workbook, worksheet

    @staticmethod
    def create_title_format(workbook, font_size=18):
        """제목 형식 생성"""
        title_format = workbook.add_format()
        title_format.set_font_size(font_size)
        title_format.set_align('vcenter')
        title_format.set_bold()
        return title_format

    @staticmethod
    def create_header_format(workbook):
        """헤더 형식 생성"""
        h_format = workbook.add_format()
        h_format.set_bold()
        h_format.set_border()
        h_format.set_align('center')
        h_format.set_align('vcenter')
        h_format.set_bg_color('#eeeeee')
        return h_format

    def write_title(self, worksheet, workbook, row_num, col_count, title):
        """제목 작성"""
        title_format = self.create_title_format(workbook)
        worksheet.set_row(row_num, 50)
        worksheet.merge_range(row_num, 0, row_num, col_count, title, title_format)
        return row_num + 1

    @staticmethod
    def write_date_info(worksheet, workbook, row_num, col_count, date_str=None):
        """날짜 정보 작성"""
        date_info = (date_str or TODAY) + ' 현재'
        worksheet.set_row(row_num, 18)
        worksheet.write(row_num, col_count, date_info, workbook.add_format({'align': 'right'}))
        return row_num + 1

    def write_headers(self, worksheet, workbook, row_num, headers):
        """헤더 작성"""
        h_format = self.create_header_format(workbook)
        worksheet.set_row(row_num, 23, workbook.add_format({'bold': True}))

        for col_num, (header_name, field_name, width) in enumerate(headers):
            if header_name:  # 빈 헤더 제외
                worksheet.set_column(col_num, col_num, width)
                worksheet.write(row_num, col_num, header_name, h_format)

        return row_num + 1

    def write_data_rows(self, worksheet, workbook, row_num, headers, data_list):
        """데이터 행 작성"""
        c_format = workbook.add_format()
        c_format.set_border()
        c_format.set_align('center')
        c_format.set_align('vcenter')

        for item in data_list:
            for col_num, (header_name, field_name, width) in enumerate(headers):
                if header_name and field_name:  # 빈 헤더와 필드 제외
                    value = self.get_field_value(item, field_name)
                    worksheet.write(row_num, col_num, value, c_format)
            row_num += 1

        return row_num

    @staticmethod
    def get_field_value(obj, field_name):
        """객체에서 필드 값 추출 (중첩 필드 지원)"""
        if not field_name:
            return ''

        try:
            # 중첩 필드 처리 (예: contractor__name)
            fields = field_name.split('__')
            value = obj
            for field in fields:
                if hasattr(value, field):
                    value = getattr(value, field)
                elif hasattr(value, 'get') and callable(getattr(value, 'get')):
                    value = value.get(field, '')
                else:
                    return ''

            # 날짜 포맷팅
            if isinstance(value, datetime.date):
                return value.strftime('%Y-%m-%d')
            elif isinstance(value, datetime.datetime):
                return value.strftime('%Y-%m-%d %H:%M')

            return str(value) if value is not None else ''
        except (AttributeError, KeyError, TypeError):
            return ''

    @staticmethod
    def create_response(output, workbook, filename):
        """HTTP 응답 생성"""
        workbook.close()
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        return response


class ProjectFilterMixin:
    """프로젝트 필터링 공통 기능"""

    @staticmethod
    def get_project(request):
        """요청에서 프로젝트 추출"""
        project_id = request.GET.get('project')
        if project_id:
            return Project.objects.get(pk=project_id)
        return None

    @staticmethod
    def get_selected_columns(request):
        """선택된 컬럼 목록 추출"""
        col_param = request.GET.get('col', '')
        if col_param:
            return sorted(list(map(int, col_param.split('-'))))
        return []


class ExcelUtilsMixin:
    """Excel 관련 유틸리티 기능"""

    @staticmethod
    def format_currency(amount):
        """통화 형식으로 포맷"""
        if amount is None:
            return ''
        return f"{amount:,}"

    @staticmethod
    def format_phone(phone):
        """전화번호 형식으로 포맷"""
        if not phone:
            return ''
        # 하이픈 제거 후 재포맷
        clean_phone = phone.replace('-', '').replace(' ', '')
        if len(clean_phone) == 11:
            return f"{clean_phone[:3]}-{clean_phone[3:7]}-{clean_phone[7:]}"
        elif len(clean_phone) == 10:
            return f"{clean_phone[:3]}-{clean_phone[3:6]}-{clean_phone[6:]}"
        return phone

    @staticmethod
    def safe_get_attr(obj, attr_path, default=''):
        """안전한 속성 접근"""
        try:
            attrs = attr_path.split('__')
            result = obj
            for attr in attrs:
                if hasattr(result, attr):
                    result = getattr(result, attr)
                else:
                    return default
            return result if result is not None else default
        except (AttributeError, TypeError):
            return default
