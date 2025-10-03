from rest_framework import serializers

from notice.models import SalesBillIssue
from apiV1.serializers.accounts import SimpleUserSerializer


# Notice --------------------------------------------------------------------------
class SallesBillIssueSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = SalesBillIssue
        fields = ('pk', 'project', 'now_payment_order', 'host_name', 'host_tel',
                  'agency', 'agency_tel', 'bank_account1', 'bank_number1', 'bank_host1',
                  'bank_account2', 'bank_number2', 'bank_host2', 'zipcode', 'address1',
                  'address2', 'address3', 'title', 'content', 'creator', 'updated')


# SMS/MMS Message Serializers -------------------------------------------------------
class SMSMessageSerializer(serializers.Serializer):
    """SMS 메시지 발송 시리얼라이저"""
    message_type = serializers.ChoiceField(
        choices=[('SMS', 'SMS (90자 이내)'), ('LMS', 'LMS (장문메시지)'), ('AUTO', '자동 판별')],
        default='AUTO',
        help_text="메시지 타입"
    )
    message = serializers.CharField(
        max_length=2000,
        help_text="메시지 내용 (SMS: 90byte, LMS: 2000byte)"
    )
    title = serializers.CharField(
        max_length=40,
        required=False,
        allow_blank=True,
        help_text="제목 (LMS용, 최대 40byte)"
    )
    sender_number = serializers.CharField(
        max_length=20,
        help_text="발신번호"
    )
    recipients = serializers.ListField(
        child=serializers.CharField(max_length=20),
        min_length=1,
        max_length=1000,
        help_text="수신자 번호 리스트 (최대 1000명)"
    )
    scheduled_send = serializers.BooleanField(
        default=False,
        help_text="예약 발송 여부"
    )
    schedule_date = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="예약 발송 날짜 (YYYY-MM-DD)"
    )
    schedule_time = serializers.TimeField(
        required=False,
        allow_null=True,
        help_text="예약 발송 시간 (HH:mm)"
    )
    use_v2_api = serializers.BooleanField(
        default=True,
        help_text="v2 API 사용 여부"
    )

    def validate(self, data):
        """전체 유효성 검사"""
        # 예약 발송 시 날짜/시간 필수 검사
        if data.get('scheduled_send', False):
            if not data.get('schedule_date') or not data.get('schedule_time'):
                raise serializers.ValidationError(
                    "예약 발송 시 발송 날짜와 시간을 모두 입력해야 합니다."
                )

        # LMS 타입일 때 제목 필수 검사
        if data.get('message_type') == 'LMS' and not data.get('title'):
            raise serializers.ValidationError(
                "LMS 발송 시 제목이 필요합니다."
            )

        return data

    @staticmethod
    def validate_message(value):
        """메시지 내용 유효성 검사"""
        if len(value.encode('utf-8')) > 2000:
            raise serializers.ValidationError(
                "메시지는 2000 bytes까지만 입력 가능합니다."
            )
        return value

    @staticmethod
    def validate_title(value):
        """제목 유효성 검사"""
        if value and len(value.encode('utf-8')) > 40:
            raise serializers.ValidationError(
                "제목은 40 bytes까지만 입력 가능합니다."
            )
        return value

    @staticmethod
    def validate_recipients(value):
        """수신자 번호 유효성 검사"""
        if len(value) > 1000:
            raise serializers.ValidationError(
                "수신자는 최대 1000명까지 가능합니다."
            )

        # 전화번호 형식 검사
        for phone in value:
            clean_phone = phone.replace('-', '').replace(' ', '')
            if not clean_phone.isdigit() or len(clean_phone) < 10 or len(clean_phone) > 11:
                raise serializers.ValidationError(
                    f"잘못된 전화번호 형식: {phone}"
                )

        return value


class MMSMessageSerializer(SMSMessageSerializer):
    """MMS 메시지 발송 시리얼라이저"""
    image = serializers.ImageField(
        help_text="이미지 파일 (100KB 미만 JPG)"
    )

    @staticmethod
    def validate_image(value):
        """이미지 파일 유효성 검사"""
        # 파일 크기 검사 (100KB)
        if value.size > 100 * 1024:
            raise serializers.ValidationError(
                "이미지는 100KB 미만이어야 합니다."
            )

        # 파일 확장자 검사
        if not value.name.lower().endswith('.jpg'):
            raise serializers.ValidationError(
                "JPG 파일만 업로드 가능합니다."
            )

        return value


class KakaoMessageSerializer(serializers.Serializer):
    """카카오 알림톡 메시지 발송 시리얼라이저"""
    template_code = serializers.CharField(
        max_length=50,
        help_text="승인된 템플릿 코드"
    )
    recipients = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=10000,
        help_text="수신자 정보 리스트 [{'phone': '01012345678', 'template_param': ['값1', '값2']}]"
    )
    sender_number = serializers.CharField(
        max_length=20,
        help_text="발신번호 (사전 등록된 번호)"
    )
    scheduled_send = serializers.BooleanField(
        default=False,
        help_text="예약 발송 여부"
    )
    schedule_date = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="예약 발송 날짜 (YYYY-MM-DD)"
    )
    schedule_time = serializers.TimeField(
        required=False,
        allow_null=True,
        help_text="예약 발송 시간 (HH:mm)"
    )
    re_send = serializers.BooleanField(
        default=False,
        help_text="실패 시 대체 문자 발송 여부"
    )
    resend_type = serializers.ChoiceField(
        choices=[('Y', '알림톡 내용'), ('N', '직접 입력')],
        default='Y',
        help_text="대체 발송 내용 타입"
    )
    resend_title = serializers.CharField(
        max_length=40,
        required=False,
        allow_blank=True,
        help_text="대체 문자 제목 (LMS용)"
    )
    resend_content = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        help_text="대체 문자 내용"
    )

    @staticmethod
    def validate_recipients(value):
        """수신자 정보 유효성 검사"""
        if len(value) > 10000:
            raise serializers.ValidationError(
                "수신자는 최대 10,000명까지 가능합니다."
            )

        for i, recipient in enumerate(value):
            # 필수 필드 검사
            if 'phone' not in recipient:
                raise serializers.ValidationError(
                    f"수신자 {i + 1}번째: 전화번호(phone)가 필요합니다."
                )

            # 전화번호 형식 검사
            phone = str(recipient['phone']).replace('-', '').replace(' ', '')
            if not phone.isdigit() or len(phone) < 10 or len(phone) > 11:
                raise serializers.ValidationError(
                    f"수신자 {i + 1}번째: 잘못된 전화번호 형식 - {recipient['phone']}"
                )

            # 템플릿 변수는 선택사항이지만 있다면 리스트여야 함
            if 'template_param' in recipient and not isinstance(recipient['template_param'], list):
                raise serializers.ValidationError(
                    f"수신자 {i + 1}번째: template_param은 리스트여야 합니다."
                )

        return value

    def validate(self, data):
        """전체 유효성 검사"""
        # 예약 발송 시 날짜/시간 필수 검사
        if data.get('scheduled_send', False):
            if not data.get('schedule_date') or not data.get('schedule_time'):
                raise serializers.ValidationError(
                    "예약 발송 시 발송 날짜와 시간을 모두 입력해야 합니다."
                )

        # 대체 발송 설정 검사
        if data.get('re_send', False):
            if data.get('resend_type') == 'N' and not data.get('resend_content'):
                raise serializers.ValidationError(
                    "대체 발송 내용 타입이 '직접 입력'일 때 대체 문자 내용이 필요합니다."
                )

        return data


class SMSHistoryQuerySerializer(serializers.Serializer):
    """SMS 전송 내역 조회 시리얼라이저"""
    company_id = serializers.CharField(
        max_length=100,
        help_text="조직(업체) 발송 아이디"
    )
    start_date = serializers.DateField(
        help_text="발송 요청 시작일자 (YYYY-MM-DD)"
    )
    end_date = serializers.DateField(
        help_text="발송 요청 마감일자 (YYYY-MM-DD)"
    )
    request_no = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text="메시지 발송요청 고유번호"
    )
    page_num = serializers.IntegerField(
        default=1,
        min_value=1,
        help_text="페이지 번호 (기본:1)"
    )
    page_size = serializers.IntegerField(
        default=15,
        min_value=1,
        max_value=1000,
        help_text="조회 건수 (기본:15, 최대:1000) - 주의: iwinv API 버그로 인해 실제로는 사용되지 않음"
    )
    phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="수신번호"
    )

    def validate(self, data):
        """전체 유효성 검사"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date:
            # 시작일이 마감일보다 늦은지 체크
            if start_date > end_date:
                raise serializers.ValidationError(
                    "시작일이 마감일보다 늦을 수 없습니다."
                )

            # 90일 이내 체크
            date_diff = (end_date - start_date).days
            if date_diff > 90:
                raise serializers.ValidationError(
                    "조회 기간은 90일 이내만 가능합니다."
                )

        return data

    @staticmethod
    def validate_phone(value):
        """전화번호 유효성 검사"""
        if value:
            clean_phone = value.replace('-', '').replace(' ', '')
            if not clean_phone.isdigit() or len(clean_phone) < 10 or len(clean_phone) > 11:
                raise serializers.ValidationError(
                    f"잘못된 전화번호 형식: {value}"
                )
        return value
