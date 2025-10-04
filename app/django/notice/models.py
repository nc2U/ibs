from django.db import models
from django.conf import settings


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
