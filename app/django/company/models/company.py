from django.db import models

from _utils.file_cleanup import file_cleanup_signals
from _utils.file_upload import get_company_image_path


# 회사 - 최상위 모델
class Company(models.Model):
    name = models.CharField('회사명', max_length=30, unique=True, db_index=True)
    en_name = models.CharField('영문명', max_length=50, blank=True, default='', help_text='영문 회사명')
    short_name = models.CharField('회사 약칭', max_length=20, blank=True, default='',
                                  help_text='공문서 번호 등에 표기될 약칭 (예: 대영IBS, 대영아이비에스, DYIBS)')
    tax_number = models.CharField('사업자등록번호', max_length=12)
    ceo = models.CharField('대표자명', max_length=20)
    org_number = models.CharField('법인등록번호', max_length=14)
    business_cond = models.CharField('업태', max_length=20, blank=True)
    business_even = models.CharField('종목', max_length=20, blank=True)
    es_date = models.DateField('설립일자', null=True, blank=True)
    op_date = models.DateField('개업일자', null=True, blank=True)
    zipcode = models.CharField('우편번호', max_length=5, blank=True)
    address1 = models.CharField('주소', max_length=35, blank=True)
    address2 = models.CharField('상세주소', max_length=50, blank=True)
    address3 = models.CharField('참고항목', max_length=30, blank=True)
    phone = models.CharField('대표전화', max_length=15, blank=True, default='')
    fax = models.CharField('대표팩스', max_length=15, blank=True, default='')
    email = models.EmailField('대표이메일', blank=True, default='')
    is_default = models.BooleanField('메인 회사 여부', default=False)

    class Meta:
        verbose_name = "01. 회사 정보"
        verbose_name_plural = "01. 회사 정보"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_default:
            Company.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Logo(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE)
    generic_logo = models.ImageField(upload_to=get_company_image_path, null=True, help_text='4.5:1 ~ 5:1 크기 추천',
                                     verbose_name='일반 로고')
    dark_logo = models.ImageField(upload_to=get_company_image_path, null=True, help_text='4.5:1 ~ 5:1 크기 추천',
                                  verbose_name='다크 로고')
    simple_logo = models.ImageField(upload_to=get_company_image_path, null=True, help_text='1:1 크기 추천',
                                    verbose_name='심플 로고')


class CompanySeal(models.Model):
    SEAL_TYPE_CHOICES = (
        ('CORP_SEAL', '법인인감 (대표이사 직인)'),
        ('USAGE_SEAL', '사용인감'),
        ('DEPT_SEAL', '부서인감/직인'),
        ('SIGN', '대표자/부서장 서명'),
        ('OMIT', '직인생략'),
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='seals', verbose_name='회사')
    seal_type = models.CharField('인장 종류', max_length=20, choices=SEAL_TYPE_CHOICES, default='USAGE_SEAL')
    name = models.CharField('인장 명칭', max_length=50, help_text='예: 대표이사 법인인감, 분양계약 전용 사용인감 1호')
    seal_image = models.ImageField('인장 이미지', upload_to=get_company_image_path, null=True, blank=True,
                                   help_text='배경이 투명한 PNG 권장 (정방형)')
    manager = models.CharField('관리 책임자/부서', max_length=50, blank=True, default='')
    final_approval_duty = models.ForeignKey(
        'company.DutyTitle', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='전결 직책 자격',
        help_text='이 인장을 날인하기 위한 최소 최종 전결 직책 (미지정 시 대표이사까지 상신)'
    )
    final_dept_level = models.PositiveSmallIntegerField(
        '전결 부서 레벨', null=True, blank=True,
        help_text='예: 1=본부장 전결, 2=팀장/소장 전결 가능 (미지정 시 대표이사까지 상신)'
    )
    is_active = models.BooleanField('사용 여부', default=True)
    created = models.DateTimeField('등록일시', auto_now_add=True)

    class Meta:
        verbose_name = "03. 회사 인장"
        verbose_name_plural = "03. 회사 인장"
        ordering = ['-is_active', 'seal_type', 'created']

    def __str__(self):
        return f"{self.name} ({self.get_seal_type_display()})"


file_cleanup_signals(Logo)
file_cleanup_signals(CompanySeal, file_field_names=['seal_image'])
