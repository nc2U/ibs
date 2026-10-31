"""
Excel Export Common Mixins

공통 Excel 내보내기 기능을 제공하는 믹스인 클래스들
"""
import datetime
import io
import re
from decimal import Decimal
from urllib.parse import quote

import xlsxwriter
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import View

from project.models import Project


class _TodayProxy(str):
    """서버 가동 중 날짜가 바뀌어도 항상 현재 날짜를 동적으로 반환하는 프록시 문자열"""

    @property
    def _val(self):
        return datetime.date.today().strftime('%Y-%m-%d')

    def __str__(self):
        return self._val

    def __repr__(self):
        return repr(self._val)

    def __len__(self):
        return len(self._val)

    def __bool__(self):
        return bool(self._val)

    def __add__(self, other):
        return self._val + str(other)

    def __radd__(self, other):
        return str(other) + self._val

    def __eq__(self, other):
        return self._val == other

    def __ne__(self, other):
        return self._val != other

    def __lt__(self, other):
        return self._val < other

    def __le__(self, other):
        return self._val <= other

    def __gt__(self, other):
        return self._val > other

    def __ge__(self, other):
        return self._val >= other

    def __hash__(self):
        return hash(self._val)

    def startswith(self, prefix, *args):
        return self._val.startswith(prefix, *args)

    def endswith(self, suffix, *args):
        return self._val.endswith(suffix, *args)

    def split(self, sep=None, maxsplit=-1):
        return self._val.split(sep, maxsplit)

    def replace(self, old, new, count=-1):
        return self._val.replace(old, new, count)


# 하위 호환성을 위해 TODAY 심볼 유지 (동적 프록시 적용)
TODAY = _TodayProxy()


class ExcelExportMixin(LoginRequiredMixin, View):
    """Excel 내보내기 공통 기능 믹스인 (세션 및 JWT 로그인 인증 지원)"""
    raise_exception = False

    def dispatch(self, request, *args, **kwargs):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not request.user.is_authenticated and auth_header:
            from rest_framework_simplejwt.authentication import JWTAuthentication
            try:
                auth_result = JWTAuthentication().authenticate(request)
                if auth_result is not None:
                    request.user, request.auth = auth_result
            except Exception:
                pass
            if not request.user.is_authenticated:
                return HttpResponse(
                    '유효하지 않거나 만료된 인증 토큰입니다.',
                    status=401,
                    content_type='text/plain; charset=utf-8',
                )
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def get_today_str():
        """동적으로 현재 날짜 반환 (프로세스 캐싱 방지)"""
        return datetime.date.today().strftime('%Y-%m-%d')

    @classmethod
    def sanitize_sheet_name(cls, name, default='데이터'):
        """시트 이름 유효성 검증 및 31자/금지문자 정제"""
        if not name:
            return default
        # 엑셀 시트명 금지 문자 \ / ? * : [ ] 제거
        cleaned = re.sub(r'[\\/?*:[\]]', '', str(name)).strip()
        return cleaned[:31] if cleaned else default

    @classmethod
    def create_workbook(cls, sheet_name=None, in_memory=False, default_row=20):
        """워크북과 워크시트 생성"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': in_memory})
        worksheet = workbook.add_worksheet(cls.sanitize_sheet_name(sheet_name))
        worksheet.set_default_row(default_row)
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

    @staticmethod
    def create_number_format(workbook):
        number_format = workbook.add_format({
            'valign': 'vcenter',
            'border': True,
            'num_format': 41,
            'align': 'right'
        })
        return number_format

    @staticmethod
    def create_center_format(workbook):
        center_format = workbook.add_format({
            'valign': 'vcenter',
            'border': True,
            'align': 'center'
        })
        return center_format

    @staticmethod
    def create_left_format(workbook):
        left_format = workbook.add_format({
            'valign': 'vcenter',
            'border': True,
            'align': 'left'
        })
        return left_format

    @staticmethod
    def create_sum_format(workbook):
        sum_format = workbook.add_format()
        sum_format.set_bold()
        sum_format.set_valign('vcenter')
        sum_format.set_border()
        sum_format.set_num_format(41)
        sum_format.set_align('center')
        sum_format.set_bg_color('#eeeeee')
        return sum_format

    def write_title(self, worksheet, workbook, row_num, col_count, title):
        """제목 작성"""
        title_format = self.create_title_format(workbook)
        worksheet.set_row(row_num, 50)
        if col_count > 0:
            worksheet.merge_range(row_num, 0, row_num, col_count, title, title_format)
        else:
            worksheet.write(row_num, 0, title, title_format)
        return row_num + 1

    @classmethod
    def write_date_info(cls, worksheet, workbook, row_num, col_count, date_str=None, right_format=None):
        """날짜 정보 작성 (동적 현재 일자 적용)"""
        date_info = (date_str or cls.get_today_str()) + ' 현재'
        worksheet.set_row(row_num, 18)

        # Use the provided format or create once
        if right_format is None:
            right_format = workbook.add_format({'align': 'right'})

        worksheet.write(row_num, col_count, date_info, right_format)
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
        """데이터 행 작성 (성능 최적화 및 정확한 타입별 서식 적용)"""
        # Pre-create format objects for reuse
        default_format = workbook.add_format({
            'border': True,
            'align': 'center',
            'valign': 'vcenter'
        })

        left_format = workbook.add_format({
            'border': True,
            'align': 'left',
            'valign': 'vcenter'
        })

        date_format = workbook.add_format({
            'border': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': 'yyyy-mm-dd'
        })

        number_format = workbook.add_format({
            'border': True,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '#,##0'
        })

        decimal_format = workbook.add_format({
            'border': True,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '#,##0.##'
        })

        for item in data_list:
            for col_num, (header_name, field_name, width) in enumerate(headers):
                if header_name and field_name:  # 빈 헤더와 필드 제외
                    value = self.get_field_value(item, field_name)

                    # 값의 타입 및 컬럼 헤더명에 따른 적절한 서식 매칭
                    if isinstance(value, float) and (value % 1):
                        cell_format = decimal_format
                    elif isinstance(value, (int, float)):
                        cell_format = number_format
                    elif isinstance(value, str) and ('일자' in header_name or '날짜' in header_name):
                        cell_format = date_format
                    elif isinstance(value, str) and any(kw in header_name for kw in ('비고', '주소', '내용', '상호', '적요')):
                        cell_format = left_format
                    else:
                        cell_format = default_format

                    worksheet.write(row_num, col_num, value, cell_format)
            row_num += 1

        return row_num

    @staticmethod
    def get_field_value(obj, field_name):
        """객체에서 필드 값 추출 (중첩 필드 지원 및 숫자/날짜 타입 보존)"""
        if not field_name:
            return ''

        try:
            # 중첩 필드 처리 (예: contractor__name)
            fields = field_name.split('__')
            value = obj
            for field in fields:
                if hasattr(value, field):
                    value = getattr(value, field)
                elif isinstance(value, dict):
                    value = value.get(field, '')
                elif hasattr(value, 'get') and callable(getattr(value, 'get')):
                    value = value.get(field, '')
                else:
                    return ''

                # choice 필드의 get_status_display 등 인자 없는 callable 속성 자동 평가
                if callable(value):
                    try:
                        value = value()
                    except TypeError:
                        pass

            if value is None:
                return ''

            # 1. 숫자 타입 보존 (Decimal, int, float) -> 엑셀에서 수식/합계 정상 작동
            if isinstance(value, Decimal):
                return float(value) if value % 1 else int(value)
            if isinstance(value, (int, float)):
                return value

            # 2. 날짜/시간 포맷팅
            if isinstance(value, datetime.date):
                return value.strftime('%Y-%m-%d')
            elif isinstance(value, datetime.datetime):
                return value.strftime('%Y-%m-%d %H:%M')

            # 3. 기타 값은 문자열 반환
            return str(value)
        except (AttributeError, KeyError, TypeError):
            return ''

    @staticmethod
    def create_response(output, workbook, filename):
        """HTTP 응답 생성 (중복 close 방지 및 파일명 인젝션 방어)"""
        # 중복 close 방어 (하위 뷰에서 이미 close()를 호출한 경우 발생할 수 있는 UserWarning 차단)
        if not getattr(workbook, 'fileclosed', 0):
            try:
                workbook.close()
            except Exception:
                pass

        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        # HTTP Response Splitting 및 특수문자 정제
        clean_name = re.sub(r'["\r\n]', '', str(filename)).strip() or 'export'
        encoded_filename = quote(f'{clean_name}.xlsx')
        response['Content-Disposition'] = (
            f'attachment; filename="{clean_name}.xlsx"; filename*=UTF-8\'\'{encoded_filename}'
        )
        return response


class ProjectFilterMixin:
    """프로젝트 필터링 공통 기능"""

    @staticmethod
    def get_project(request):
        """요청에서 프로젝트 추출"""
        project_id = request.GET.get('project')
        if project_id:
            try:
                return Project.objects.filter(pk=project_id).first()
            except (ValueError, TypeError):
                return None
        return None

    @staticmethod
    def get_selected_columns(request):
        """선택된 컬럼 목록 추출"""
        col_param = request.GET.get('col', '')
        if col_param:
            try:
                return sorted([int(c) for c in col_param.split('-') if c.isdigit()])
            except (ValueError, TypeError):
                return []
        return []


class ExcelUtilsMixin:
    """Excel 관련 유틸리티 기능"""

    @staticmethod
    def format_currency(amount):
        """통화 형식으로 포맷 (문자열, Decimal, float, int 완벽 방어)"""
        if amount is None or amount == '':
            return ''
        try:
            if isinstance(amount, str):
                clean_str = amount.replace(',', '').strip()
                amount = float(clean_str) if '.' in clean_str else int(clean_str)
            elif isinstance(amount, Decimal):
                amount = float(amount) if amount % 1 else int(amount)
            return f"{amount:,}"
        except (ValueError, TypeError):
            return str(amount)

    @staticmethod
    def format_phone(phone):
        """전화번호 형식으로 포맷 (서울 02 국번 9/10자리 및 일반 10/11자리 대응, 숫자형 안전 변환)"""
        if not phone:
            return ''
        # 하이픈 및 공백 제거 후 재포맷 (정수형 입력 방어)
        clean_phone = str(phone).replace('-', '').replace(' ', '')
        if len(clean_phone) == 11:
            return f"{clean_phone[:3]}-{clean_phone[3:7]}-{clean_phone[7:]}"
        elif len(clean_phone) == 10:
            if clean_phone.startswith('02'):
                return f"{clean_phone[:2]}-{clean_phone[2:6]}-{clean_phone[6:]}"
            return f"{clean_phone[:3]}-{clean_phone[3:6]}-{clean_phone[6:]}"
        elif len(clean_phone) == 9 and clean_phone.startswith('02'):
            return f"{clean_phone[:2]}-{clean_phone[2:5]}-{clean_phone[5:]}"
        return str(phone)

    @staticmethod
    def safe_get_attr(obj, attr_path, default=''):
        """안전한 속성/키 접근 (객체 및 딕셔너리 동시 지원, callable 평가)"""
        try:
            attrs = attr_path.split('__')
            result = obj
            for attr in attrs:
                if hasattr(result, attr):
                    result = getattr(result, attr)
                elif isinstance(result, dict):
                    result = result.get(attr, default)
                elif hasattr(result, 'get') and callable(getattr(result, 'get')):
                    result = result.get(attr, default)
                else:
                    return default

                if callable(result):
                    try:
                        result = result()
                    except TypeError:
                        pass

            return result if result is not None else default
        except (AttributeError, TypeError):
            return default


class AdvancedExcelMixin:
    """고급 Excel 포맷팅 기능 믹스인"""

    @staticmethod
    def create_format_objects(workbook):
        """재사용 가능한 포맷 객체들을 미리 생성"""
        return {
            'default': workbook.add_format({
                'border': True,
                'align': 'center',
                'valign': 'vcenter'
            }),
            'date': workbook.add_format({
                'border': True,
                'align': 'center',
                'valign': 'vcenter',
                'num_format': 'yyyy-mm-dd'
            }),
            'number': workbook.add_format({
                'border': True,
                'align': 'center',
                'valign': 'vcenter',
                'num_format': '#,##0'
            }),
            'currency': workbook.add_format({
                'border': True,
                'align': 'right',
                'valign': 'vcenter',
                'num_format': '_-* #,##0_-;-* #,##0_-;_-* "-"_-;_-@_-'
            }),
            'percent': workbook.add_format({
                'border': True,
                'align': 'center',
                'valign': 'vcenter',
                'num_format': '_-* 0.00%_-;-* 0.00%_-;_-* "-"??%_-;_-@_-'
            }),
            'header': workbook.add_format({
                'bold': True,
                'border': True,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#eeeeee'
            }),
            'title': workbook.add_format({
                'bold': True,
                'font_size': 18,
                'align': 'vcenter'
            }),
            'right_align': workbook.add_format({
                'align': 'right'
            })
        }

    @staticmethod
    def write_multi_level_headers(worksheet, workbook, row_num, header_structure, formats):
        """다단계 헤더 작성"""
        for level, headers in enumerate(header_structure):
            current_row = row_num + level
            worksheet.set_row(current_row, 23)

            for header_info in headers:
                if len(header_info) == 5:  # [start_col, end_col, start_row, end_row, text]
                    start_col, end_col, start_row, end_row, text = header_info
                    if start_col == end_col and start_row == end_row:
                        worksheet.write(current_row + start_row, start_col, text, formats['header'])
                    else:
                        worksheet.merge_range(
                            current_row + start_row, start_col,
                            current_row + end_row, end_col,
                            text, formats['header']
                        )

        return row_num + len(header_structure)

    @staticmethod
    def write_summary_row(worksheet, workbook, row_num, data, formats, summary_format=None):
        """합계 행 작성"""
        if summary_format is None:
            summary_format = formats['header']

        for col_num, value in enumerate(data):
            worksheet.write(row_num, col_num, value, summary_format)

        return row_num + 1

    @staticmethod
    def apply_conditional_formatting(worksheet, range_str, condition_type, criteria, format_obj):
        """조건부 서식 적용"""
        worksheet.conditional_format(range_str, {
            'type': condition_type,
            'criteria': criteria,
            'format': format_obj
        })

    @staticmethod
    def set_column_widths(worksheet, widths):
        """컬럼 너비 일괄 설정"""
        for col_num, width in enumerate(widths):
            worksheet.set_column(col_num, col_num, width)


class XlwtStyleMixin:
    """xlwt 라이브러리용 스타일 생성 믹스인"""

    @staticmethod
    def create_xlwt_styles():
        """
        xlwt용 재사용 가능한 스타일 세트 생성
        xlwt는 최대 4094개의 스타일만 지원하므로 미리 생성하여 재사용

        Returns:
            dict: 스타일 이름을 키로 하는 xlwt.XFStyle 객체 딕셔너리
        """
        import xlwt

        # 기본 스타일 (왼쪽 정렬)
        style_default = xlwt.XFStyle()
        style_default.borders.left = 1
        style_default.borders.right = 1
        style_default.borders.top = 1
        style_default.borders.bottom = 1
        style_default.alignment.vert = style_default.alignment.VERT_CENTER

        # 가운데 정렬 스타일
        style_center = xlwt.XFStyle()
        style_center.borders.left = 1
        style_center.borders.right = 1
        style_center.borders.top = 1
        style_center.borders.bottom = 1
        style_center.alignment.vert = style_center.alignment.VERT_CENTER
        style_center.alignment.horz = style_center.alignment.HORZ_CENTER

        # 오른쪽 정렬 스타일
        style_right = xlwt.XFStyle()
        style_right.borders.left = 1
        style_right.borders.right = 1
        style_right.borders.top = 1
        style_right.borders.bottom = 1
        style_right.alignment.vert = style_right.alignment.VERT_CENTER
        style_right.alignment.horz = style_right.alignment.HORZ_RIGHT

        # 날짜 스타일 (가운데 정렬 + 날짜 포맷)
        style_date = xlwt.XFStyle()
        style_date.borders.left = 1
        style_date.borders.right = 1
        style_date.borders.top = 1
        style_date.borders.bottom = 1
        style_date.alignment.vert = style_date.alignment.VERT_CENTER
        style_date.alignment.horz = style_date.alignment.HORZ_CENTER
        style_date.num_format_str = 'yyyy-mm-dd'

        # 금액 스타일 (숫자 포맷)
        style_amount = xlwt.XFStyle()
        style_amount.borders.left = 1
        style_amount.borders.right = 1
        style_amount.borders.top = 1
        style_amount.borders.bottom = 1
        style_amount.alignment.vert = style_amount.alignment.VERT_CENTER
        style_amount.num_format_str = '#,##0'

        # 헤더 스타일 (굵게 + 회색 배경 + 가운데 정렬)
        style_header = xlwt.XFStyle()
        style_header.font.bold = True
        style_header.borders.left = 1
        style_header.borders.right = 1
        style_header.borders.top = 1
        style_header.borders.bottom = 1
        style_header.alignment.vert = style_header.alignment.VERT_CENTER
        style_header.alignment.horz = style_header.alignment.HORZ_CENTER
        style_header.pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        style_header.pattern.pattern_fore_colour = 22  # 회색

        return {
            'default': style_default,
            'center': style_center,
            'right': style_right,
            'date': style_date,
            'amount': style_amount,
            'header': style_header,
        }
