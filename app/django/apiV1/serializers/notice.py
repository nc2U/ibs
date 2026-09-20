from rest_framework import serializers
from apiV1.serializers.accounts import SimpleUserSerializer
from notice.models import (
    SalesBillIssue, RegisteredSenderNumber, MessageTemplate, MessageSendHistory,
    EmailNotice, EmailSendLog
)


# Notice --------------------------------------------------------------------------
class SallesBillIssueSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = SalesBillIssue
        fields = ('pk', 'project', 'now_payment_order', 'host_name', 'host_tel',
                  'agency', 'agency_tel', 'bank_account1', 'bank_number1', 'bank_host1',
                  'bank_account2', 'bank_number2', 'bank_host2', 'zipcode', 'address1',
                  'address2', 'address3', 'title', 'content', 'creator', 'updated')


# Registered Sender Number --------------------------------------------------------
class RegisteredSenderNumberSerializer(serializers.ModelSerializer):
    """등록된 발신번호 시리얼라이저"""

    class Meta:
        model = RegisteredSenderNumber
        fields = ('id', 'phone_number', 'label', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

    @staticmethod
    def validate_phone_number(value):
        """전화번호 유효성 검사"""
        # 하이픈 제거 후 숫자만 추출
        clean_number = value.replace('-', '').replace(' ', '')

        # 숫자만 있는지 확인
        if not clean_number.isdigit():
            raise serializers.ValidationError("전화번호는 숫자와 하이픈(-)만 포함해야 합니다.")

        # 길이 검증 (지역번호 2-3자리 + 나머지 7-8자리)
        if len(clean_number) < 9 or len(clean_number) > 11:
            raise serializers.ValidationError("올바른 전화번호 형식이 아닙니다.")

        return value


# Message Template ----------------------------------------------------------------
class MessageTemplateSerializer(serializers.ModelSerializer):
    """메시지 템플릿 시리얼라이저"""

    class Meta:
        model = MessageTemplate
        fields = ('id', 'title', 'message_type', 'content', 'variables', 'is_active',
                  'created_by', 'created_at', 'updated_at')
        read_only_fields = ('created_by', 'created_at', 'updated_at')

    @staticmethod
    def validate_message_type(value):
        """메시지 타입 유효성 검사"""
        valid_types = ['SMS', 'LMS', 'MMS']
        if value not in valid_types:
            raise serializers.ValidationError(f"메시지 타입은 {', '.join(valid_types)} 중 하나여야 합니다.")
        return value


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
    company_id = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="조직 구분 ID (히스토리 저장용)"
    )
    project = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="프로젝트 ID (히스토리 저장용)"
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


# Message Send History ------------------------------------------------------------
class MessageSendHistorySerializer(serializers.ModelSerializer):
    """메시지 발송 기록 시리얼라이저"""
    sent_by = SimpleUserSerializer(read_only=True)

    class Meta:
        model = MessageSendHistory
        fields = (
            'id', 'message_type', 'sender_number', 'message_content', 'title',
            'recipients', 'recipient_count', 'sent_at', 'request_no', 'company_id',
            'project', 'scheduled_send', 'schedule_datetime', 'sent_by', 'created'
        )
        read_only_fields = ('id', 'sent_by', 'created')


class MessageSendHistoryListSerializer(serializers.ModelSerializer):
    """메시지 발송 기록 목록 시리얼라이저 (경량화)"""
    sent_by = SimpleUserSerializer(read_only=True)

    # recipients는 목록에서 제외 (상세보기에서만 표시)

    class Meta:
        model = MessageSendHistory
        fields = ('id', 'message_type', 'sender_number', 'title', 'message_content', 'recipient_count',
                  'sent_at', 'request_no', 'scheduled_send', 'sent_by', 'created')
        read_only_fields = ('id', 'sent_by', 'created')


# Post Label ----------------------------------------------------------------------
class PostLabelSerializer(serializers.Serializer):
    """우편 라벨 출력용 시리얼라이저"""
    id = serializers.IntegerField(read_only=True)
    contractor_id = serializers.IntegerField(source='contractor.id', read_only=True)
    contractor_name = serializers.CharField(source='contractor.name', read_only=True)
    contract_id = serializers.IntegerField(source='contractor.contract.id', read_only=True, allow_null=True)
    contract_serial = serializers.CharField(source='contractor.contract.serial_number', read_only=True, allow_null=True)
    order_group_id = serializers.IntegerField(source='contractor.contract.order_group.id', read_only=True, allow_null=True)
    order_group_name = serializers.CharField(source='contractor.contract.order_group.name', read_only=True, allow_null=True)
    unit_type_name = serializers.CharField(source='contractor.contract.unit_type.name', read_only=True, allow_null=True)

    # 동호수
    building_name = serializers.SerializerMethodField()
    unit_name = serializers.SerializerMethodField()
    unit_info = serializers.SerializerMethodField()

    # 주민등록 주소
    id_zipcode = serializers.CharField(read_only=True)
    id_address1 = serializers.CharField(read_only=True)
    id_address2 = serializers.CharField(read_only=True)
    id_address3 = serializers.CharField(read_only=True)

    # 우편송부 주소
    dm_zipcode = serializers.CharField(read_only=True)
    dm_address1 = serializers.CharField(read_only=True)
    dm_address2 = serializers.CharField(read_only=True)
    dm_address3 = serializers.CharField(read_only=True)

    # 조합 주소 (수령지 우선)
    effective_zipcode = serializers.SerializerMethodField()
    effective_address1 = serializers.SerializerMethodField()
    effective_address2 = serializers.SerializerMethodField()
    effective_address3 = serializers.SerializerMethodField()
    has_dm_address = serializers.SerializerMethodField()

    def _get_house_unit(self, obj):
        contract = getattr(obj.contractor, 'contract', None)
        if contract and contract.key_unit and hasattr(contract.key_unit, 'houseunit'):
            return contract.key_unit.houseunit
        return None

    def get_building_name(self, obj):
        hu = self._get_house_unit(obj)
        return hu.building_unit.name if hu and hu.building_unit else ''

    def get_unit_name(self, obj):
        hu = self._get_house_unit(obj)
        return hu.name if hu else ''

    def get_unit_info(self, obj):
        hu = self._get_house_unit(obj)
        if hu:
            bldg = hu.building_unit.name if hu.building_unit else ''
            return f'{bldg} {hu.name}'
        return ''

    def get_has_dm_address(self, obj):
        return bool(obj.dm_address1 and obj.dm_address1.strip())

    def get_effective_zipcode(self, obj):
        return obj.dm_zipcode if self.get_has_dm_address(obj) else obj.id_zipcode

    def get_effective_address1(self, obj):
        return obj.dm_address1 if self.get_has_dm_address(obj) else obj.id_address1

    def get_effective_address2(self, obj):
        return obj.dm_address2 if self.get_has_dm_address(obj) else obj.id_address2

    def get_effective_address3(self, obj):
        return obj.dm_address3 if self.get_has_dm_address(obj) else obj.id_address3


# Email Notice --------------------------------------------------------------------
class EmailSendLogSerializer(serializers.ModelSerializer):
    """이메일 발송 로그 시리얼라이저"""
    contractor_name = serializers.CharField(source='contractor.name', read_only=True)

    class Meta:
        model = EmailSendLog
        fields = (
            'id', 'email_notice', 'contractor', 'contractor_name',
            'recipient_name', 'recipient_email', 'unit_info',
            'status', 'error_message', 'sent_at'
        )
        read_only_fields = ('id', 'sent_at')


class EmailNoticeSerializer(serializers.ModelSerializer):
    """이메일 공지 상세 및 생성 시리얼라이저"""
    sent_by = SimpleUserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    send_logs = EmailSendLogSerializer(many=True, read_only=True)

    class Meta:
        model = EmailNotice
        fields = (
            'id', 'project', 'title', 'content', 'sender_name', 'sender_email',
            'total_recipients', 'success_count', 'fail_count',
            'status', 'status_display', 'sent_by', 'created', 'completed_at', 'send_logs'
        )
        read_only_fields = (
            'id', 'total_recipients', 'success_count', 'fail_count',
            'status', 'sent_by', 'created', 'completed_at'
        )


class EmailNoticeListSerializer(serializers.ModelSerializer):
    """이메일 공지 목록 시리얼라이저 (경량화)"""
    sent_by = SimpleUserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = EmailNotice
        fields = (
            'id', 'project', 'title', 'sender_name', 'sender_email',
            'total_recipients', 'success_count', 'fail_count',
            'status', 'status_display', 'sent_by', 'created', 'completed_at'
        )
        read_only_fields = ('id', 'sent_by', 'created')


class EmailSendRequestSerializer(serializers.Serializer):
    """이메일 발송 요청 바디 검증용"""
    project = serializers.IntegerField(required=True)
    title = serializers.CharField(max_length=150, required=True)
    content = serializers.CharField(required=True)
    sender_name = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')
    sender_email = serializers.EmailField(required=False, allow_blank=True, default='')
    order_group = serializers.IntegerField(required=False, allow_null=True)
    building = serializers.IntegerField(required=False, allow_null=True)
    # 특정 계약자 지정 발송 옵션
    contractor_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_empty=True, default=list
    )
