from django.core.exceptions import ValidationError
from django.db import models

from .company import Company


# 임원 직위 모델
class ExecutiveRank(models.Model):
    """임원 직위 정보 (이사, 상무, 전무, 부사장, 사장, 부회장, 회장 등)"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='executive_ranks', verbose_name='회사')
    code = models.CharField('직위 코드', max_length=10, help_text='예: E1, E2, E3.., A01, V01')
    name = models.CharField('임원 직위명', max_length=20, db_index=True, help_text='예: 회장, 부회장, 사장, 상무, 이사, 감사, 고문')
    sort_order = models.PositiveSmallIntegerField('정렬 순서', default=1)
    role_desc = models.CharField('역할/관장 설명', max_length=255, blank=True, help_text='주요 역할 및 관장 부문 요약')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = "06. 임원 직위 정보"
        verbose_name_plural = "06. 임원 직위 정보"
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'name'],
                name='unique_executive_rank_name'
            ),
            models.UniqueConstraint(
                fields=['company', 'code'],
                name='unique_executive_rank_code'
            ),
        ]


# 임원 모델
class Executive(models.Model):
    """임원 법적/등기/임기 상세 정보"""
    EXECUTIVE_TYPE_CHOICES = (
        ('inside', '사내이사'),
        ('outside', '사외이사'),
        ('non_standing', '기타비상무이사'),
        ('auditor', '감사'),
        ('advisor', '고문'),
    )
    REPRESENT_CHOICES = (
        ('none', '대표권 없음'),
        ('sole', '단독대표'),
        ('joint', '공동대표'),
        ('each', '각자대표'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='executives', verbose_name='회사')
    staff = models.OneToOneField('company.Staff', on_delete=models.CASCADE, null=True, blank=True, related_name='executive', verbose_name='임원')
    name = models.CharField('이름(직접입력)', max_length=100, null=True, blank=True, help_text='시스템 계정(Staff)이 없는 경우 필수')
    contact = models.CharField('연락처(직접입력)', max_length=100, null=True, blank=True)
    rank = models.ForeignKey(ExecutiveRank, on_delete=models.PROTECT, related_name='executives', verbose_name='임원 직위')
    executive_type = models.CharField('임원 구분', max_length=25, choices=EXECUTIVE_TYPE_CHOICES, default='inside',
                                      help_text='임원의 법적·조직적 구분')
    is_registered = models.BooleanField('등기 여부', default=False, help_text='법인 등기부등본 등기 여부')
    is_standing = models.BooleanField('상근 여부', default=True, help_text='상근 또는 비상근')
    represent_type = models.CharField('대표권 구분', max_length=10, choices=REPRESENT_CHOICES, default='none',
                                      help_text='대표권 보유 형태')
    term_start = models.DateField('현재 임기 시작일(취임일)', null=True, blank=True)
    term_end = models.DateField('현재 임기 만료일', null=True, blank=True)
    appointed_date = models.DateField('최초 임원 선임일', null=True, blank=True)
    note = models.CharField('비고', max_length=255, blank=True)

    @property
    def full_name(self):
        return self.staff.name if self.staff else self.name

    def __str__(self):
        rank_str = f" {self.rank.name}" if self.rank else ""
        return f"{self.full_name}{rank_str} ({self.get_executive_type_display()})"

    def clean(self):
        super().clean()

        errors = {}

        if not self.staff and not self.name:
            errors['name'] = '시스템 계정(Staff)이 없는 경우, 이름은 필수입니다.'

        if (
                self.company_id
                and self.staff_id
                and self.staff.company_id != self.company_id
        ):
            errors['staff'] = (
                '선택한 임원 직원의 회사와 임원 정보의 회사가 일치하지 않습니다.'
            )

        if (
                self.company_id
                and self.rank_id
                and self.rank.company_id != self.company_id
        ):
            errors['rank'] = (
                '선택한 임원 직위의 회사와 임원 정보의 회사가 일치하지 않습니다.'
            )

        if errors:
            raise ValidationError(errors)

    class Meta:
        ordering = ['rank__sort_order', 'staff__date_join', 'id']
        verbose_name = '09. 임원 등기/재임 정보'
        verbose_name_plural = '09. 임원 등기/재임 정보'
