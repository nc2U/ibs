"""
Excel Export Utility Functions

Excel 내보내기에 사용되는 공통 유틸리티 함수들
"""
import datetime


def get_today_string():
    """오늘 날짜를 문자열로 반환"""
    return datetime.date.today().strftime('%Y-%m-%d')


def create_filename(base_name, project_name=None, additional_info=None):
    """파일명 생성"""
    filename_parts = [base_name]

    if project_name:
        filename_parts.append(project_name)

    if additional_info:
        filename_parts.append(additional_info)

    filename_parts.append(get_today_string())

    return '_'.join(filename_parts)


def filter_headers_by_columns(headers, selected_columns):
    """선택된 컬럼에 따라 헤더 필터링"""
    if not selected_columns:
        return headers

    # 빈 헤더를 제외하고 인덱스 매핑
    filtered_headers = []
    valid_index = 0

    for i, header in enumerate(headers):
        # 헤더가 비어있지 않고 첫 번째 요소가 있는 경우만 체크
        if header and header[0]:  # 헤더 이름이 있는 경우만
            if valid_index in selected_columns:
                filtered_headers.append(header)
            valid_index += 1
        else:
            filtered_headers.append(header)  # 빈 헤더는 그대로 유지

    return filtered_headers


def get_queryset_with_select_related(base_queryset, related_fields):
    """성능 최적화를 위한 select_related 적용"""
    if related_fields:
        return base_queryset.select_related(*related_fields)
    return base_queryset


def get_queryset_with_prefetch_related(base_queryset, prefetch_fields):
    """성능 최적화를 위한 prefetch_related 적용"""
    if prefetch_fields:
        return base_queryset.prefetch_related(*prefetch_fields)
    return base_queryset


def apply_status_filter(queryset, status_param, status_field='status'):
    """상태 필터 적용"""
    if status_param:
        filter_kwargs = {status_field: status_param}
        return queryset.filter(**filter_kwargs)
    return queryset


def apply_date_range_filter(queryset, start_date, end_date, date_field='created_at'):
    """날짜 범위 필터 적용"""
    if start_date:
        filter_kwargs = {f'{date_field}__gte': start_date}
        queryset = queryset.filter(**filter_kwargs)

    if end_date:
        filter_kwargs = {f'{date_field}__lte': end_date}
        queryset = queryset.filter(**filter_kwargs)

    return queryset


class HeaderBuilder:
    """헤더 구성을 위한 빌더 클래스"""

    def __init__(self):
        self.headers = [[]]  # 빈 헤더로 시작

    def add_header(self, name, field_name, width=10):
        """헤더 추가"""
        self.headers.append([name, field_name, width])
        return self

    def add_empty_header(self):
        """빈 헤더 추가"""
        self.headers.append([])
        return self

    def build(self):
        """헤더 리스트 반환"""
        return self.headers


def create_contract_headers():
    """계약 관련 공통 헤더 생성"""
    return HeaderBuilder() \
        .add_header('일련번호', 'serial_number', 10) \
        .add_header('등록상태', 'contractor__qualification', 8) \
        .add_header('차수', 'order_group__name', 10) \
        .add_header('타입', 'key_unit__unit_type__name', 7) \
        .add_header('계약자', 'contractor__name', 10) \
        .add_header('동', 'key_unit__houseunit__building_unit__name', 7) \
        .add_header('호수', 'key_unit__houseunit__name', 7) \
        .build()


def create_payment_headers():
    """납부 관련 공통 헤더 생성"""
    return HeaderBuilder() \
        .add_header('일련번호', 'serial_number', 10) \
        .add_header('계약자', 'contractor__name', 10) \
        .add_header('납부회차', 'installment_order__pay_name', 12) \
        .add_header('납부금액', 'income', 12) \
        .add_header('납부일자', 'deal_date', 12) \
        .build()


def create_company_headers():
    """회사 관련 공통 헤더 생성"""
    return HeaderBuilder() \
        .add_header('번호', 'id', 8) \
        .add_header('이름', 'name', 15) \
        .add_header('등록일', 'created_at', 12) \
        .build()