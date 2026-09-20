from django.conf import settings
from django.db import models


class SalesBillIssue(models.Model):
    project = models.OneToOneField('project.Project', on_delete=models.CASCADE, unique=True, verbose_name='프로젝트')
    now_payment_order = models.ForeignKey('payment.InstallmentPaymentOrder', on_delete=models.SET_NULL,
                                          null=True, blank=True, verbose_name='현재 발행회차')
    host_name = models.CharField('시행자명', max_length=20)
    host_tel = models.CharField('시행사 전화', max_length=13)
    agency = models.CharField('대행사명', max_length=20, blank=True)
    agency_tel = models.CharField('대행사 전화', max_length=13, blank=True)
    bank_account1 = models.CharField('수납은행[1]', max_length=20)
    bank_number1 = models.CharField('계좌번호[1]', max_length=25)
    bank_host1 = models.CharField('예금주[1]', max_length=20)
    bank_account2 = models.CharField('수납은행[2]', max_length=20, blank=True)
    bank_number2 = models.CharField('계좌번호[2]', max_length=25, blank=True)
    bank_host2 = models.CharField('예금주[2]', max_length=20, blank=True)
    zipcode = models.CharField('우편번호', max_length=5)
    address1 = models.CharField('주소', max_length=35)
    address2 = models.CharField('상세주소', max_length=50, blank=True)
    address3 = models.CharField('참고항목', max_length=30, blank=True)
    title = models.CharField('고지서 제목', max_length=80, db_index=True)
    content = models.TextField('고지서 내용')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자')
    updated = models.DateTimeField('최종 변경일', auto_now=True)

    class Meta:
        ordering = ['id']
        verbose_name = "01. 프로젝트 고지서 정보"
        verbose_name_plural = "01. 프로젝트 고지서 정보"

    def __str__(self):
        return f'{self.project}-고지서 정보'


class RegisteredSenderNumber(models.Model):
    """등록된 발신번호 (iwinv API에서 사전 등록 필요)"""
    phone_number = models.CharField('발신번호', max_length=20, unique=True, db_index=True,
                                    help_text='iwinv 관리자 페이지에서 사전 등록된 발신번호')
    label = models.CharField('설명', max_length=50, blank=True,
                             help_text='발신번호에 대한 설명 (예: 본사, 고객센터)')
    is_active = models.BooleanField('활성화', default=True, db_index=True)
    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "02. 등록된 발신번호"
        verbose_name_plural = "02. 등록된 발신번호"

    def __str__(self):
        if self.label:
            return f'{self.phone_number} ({self.label})'
        return self.phone_number


class MessageTemplate(models.Model):
    """메시지 템플릿"""
    MESSAGE_TYPE_CHOICES = [
        ('SMS', 'SMS'),
        ('LMS', 'LMS'),
        ('MMS', 'MMS'),
    ]

    title = models.CharField('템플릿 제목', max_length=100,
                             help_text='템플릿 이름 (LMS 전송 시 제목으로도 사용 가능)')
    message_type = models.CharField('메시지 타입', max_length=10,
                                    choices=MESSAGE_TYPE_CHOICES, default='SMS', db_index=True)
    content = models.TextField('메시지 내용')
    variables = models.JSONField('변수 목록', default=list, blank=True,
                                 help_text='템플릿에서 사용하는 변수 예: ["이름", "금액"]')
    is_active = models.BooleanField('활성화', default=True, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, verbose_name='등록자')
    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "03. 메시지 템플릿"
        verbose_name_plural = "03. 메시지 템플릿"

    def __str__(self):
        return f'{self.title} ({self.message_type})'


class MessageSendHistory(models.Model):
    # 기본 정보
    company_id = models.CharField('조직 구분 ID', max_length=100, blank=True)
    project = models.ForeignKey('project.Project', on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='프로젝트')
    request_no = models.CharField('요청번호', max_length=100, blank=True, db_index=True,
                                  help_text='iwinv API 요청번호')

    # 발송 정보
    """메시지 발송 기록 (성공한 발송만 저장)"""
    MESSAGE_TYPE_CHOICES = [
        ('SMS', 'SMS'),
        ('LMS', 'LMS'),
        ('MMS', 'MMS'),
        ('KAKAO', '카카오 알림톡'),
    ]
    message_type = models.CharField('메시지 타입', max_length=10, choices=MESSAGE_TYPE_CHOICES, db_index=True)
    sender_number = models.CharField('발신번호', max_length=20, db_index=True)
    title = models.CharField('제목', max_length=100, blank=True, help_text='LMS 발송 시 제목')
    message_content = models.TextField('메시지 내용')

    # 수신자 정보 (JSONField로 전체 배열 저장)
    recipients = models.JSONField('수신번호 목록', help_text='발송된 전체 수신번호 배열')
    recipient_count = models.IntegerField('수신자 수', default=0, db_index=True)

    # 예약 발송 정보
    scheduled_send = models.BooleanField('예약 발송', default=False)
    schedule_datetime = models.DateTimeField('예약 일시', null=True, blank=True)

    # 발송 시간 및 발송자
    sent_at = models.DateTimeField('발송 일시', db_index=True)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, verbose_name='발송자')

    # 메타 정보
    created = models.DateTimeField('등록일', auto_now_add=True)

    class Meta:
        ordering = ['-created']
        verbose_name = "04. 메시지 발송 기록"
        verbose_name_plural = "04. 메시지 발송 기록"

    def __str__(self):
        return f'{self.message_type} - {self.sender_number} ({self.recipient_count}명) - {self.sent_at.strftime("%Y-%m-%d %H:%M")}'


class EmailNotice(models.Model):
    """계약자 대상 대량 이메일 발송"""
    STATUS_CHOICES = (
        ('pending', '발송 대기'),
        ('sending', '발송 중'),
        ('completed', '발송 완료'),
        ('failed', '발송 실패'),
    )

    project = models.ForeignKey('project.Project', on_delete=models.CASCADE,
                                related_name='email_notices', verbose_name='프로젝트')
    title = models.CharField('이메일 제목', max_length=150)
    content = models.TextField('이메일 본문 (HTML)')
    sender_name = models.CharField('발신자명', max_length=50, blank=True, default='')
    sender_email = models.EmailField('발신 이메일', blank=True, default='')
    total_recipients = models.PositiveIntegerField('총 수신자 수', default=0)
    success_count = models.PositiveIntegerField('발송 성공 건수', default=0)
    fail_count = models.PositiveIntegerField('발송 실패 건수', default=0)
    status = models.CharField('발송 상태', max_length=15, choices=STATUS_CHOICES, default='pending', db_index=True)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='발송자')
    created = models.DateTimeField('등록일시', auto_now_add=True)
    completed_at = models.DateTimeField('완료일시', null=True, blank=True)

    class Meta:
        ordering = ['-created']
        verbose_name = "05. 이메일 발송 관리"
        verbose_name_plural = "05. 이메일 발송 관리"

    def __str__(self):
        return f'[{self.get_status_display()}] {self.title} ({self.success_count}/{self.total_recipients}건)'


class EmailSendLog(models.Model):
    """개별 계약자 이메일 발송 로그"""
    STATUS_CHOICES = (
        ('pending', '대기'),
        ('success', '성공'),
        ('fail', '실패'),
    )

    email_notice = models.ForeignKey(EmailNotice, on_delete=models.CASCADE,
                                     related_name='send_logs', verbose_name='이메일 공지')
    contractor = models.ForeignKey('contract.Contractor', on_delete=models.SET_NULL,
                                   null=True, blank=True, verbose_name='계약자')
    recipient_name = models.CharField('수신자명', max_length=50)
    recipient_email = models.EmailField('수신 이메일')
    unit_info = models.CharField('동호수 정보', max_length=50, blank=True, default='')
    status = models.CharField('발송 상태', max_length=10, choices=STATUS_CHOICES, default='pending', db_index=True)
    error_message = models.TextField('오류/실패 사유', blank=True, default='')
    sent_at = models.DateTimeField('발송일시', null=True, blank=True)

    class Meta:
        ordering = ['id']
        verbose_name = "06. 이메일 발송 로그"
        verbose_name_plural = "06. 이메일 발송 로그"

    def __str__(self):
        return f'{self.recipient_name}({self.recipient_email}) - {self.get_status_display()}'

