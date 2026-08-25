from django.db import models
from .company import Company


# 임원 직위 모델
class ExecutiveRank(models.Model):
    """임원 직위 정보 (이사, 상무, 전무, 부사장, 사장, 부회장, 회장 등)"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='executive_ranks', verbose_name='회사')
    code = models.CharField('직위 코드', max_length=10, blank=True, help_text='예: E1, E2, E3 등')
    name = models.CharField('임원 직위명', max_length=20, db_index=True, help_text='예: 이사, 상무, 전무, 부사장, 사장, 부회장, 회장')
    rank_order = models.PositiveSmallIntegerField('서열 순서', default=1, help_text='낮을수록 상위 서열 또는 정렬 순서')
    role_desc = models.CharField('역할/관장 설명', max_length=255, blank=True, help_text='주요 역할 및 관장 부문 요약')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['rank_order', 'id']
        verbose_name = "06. 임원 직위 정보"
        verbose_name_plural = "06. 임원 직위 정보"
        unique_together = ('company', 'name')


# 임원 모델
class Executive(models.Model):
    """임원 법적/등기/임기 상세 정보"""
    DIRECTOR_CHOICES = (
        ('inside', '사내이사'),
        ('outside', '사외이사'),
        ('non_standing_director', '기타비상무이사'),
        ('auditor', '감사'),
        ('advisor', '고문/자문'),
    )
    REPRESENT_CHOICES = (
        ('none', '해당없음'),
        ('sole', '단독대표'),
        ('joint', '공동대표'),
        ('each', '각자대표'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='executives', verbose_name='회사')
    staff = models.OneToOneField('company.Staff', on_delete=models.CASCADE, related_name='executive', verbose_name='임원')
    rank = models.ForeignKey(ExecutiveRank, on_delete=models.SET_NULL, null=True, blank=True, related_name='executives',
                             verbose_name='임원 직위')
    director_type = models.CharField('상법상 지위', max_length=25, choices=DIRECTOR_CHOICES, default='unregistered')
    is_registered = models.BooleanField('등기 여부', default=False, help_text='법인 등기부등본 등기 여부')
    is_standing = models.BooleanField('상근 여부', default=True, help_text='상근 또는 비상근')
    represent_type = models.CharField('대표권 구분', max_length=10, choices=REPRESENT_CHOICES, default='none',
                                      help_text='대표권 보유 형태')
    term_start = models.DateField('임기 시작일(취임일)', null=True, blank=True)
    term_end = models.DateField('임기 만료일', null=True, blank=True)
    appointed_date = models.DateField('최초 선임일', null=True, blank=True)
    note = models.CharField('비고', max_length=255, blank=True)

    def __str__(self):
        rank_str = f" {self.rank.name}" if self.rank else ""
        return f"{self.staff.name}{rank_str} ({self.get_director_type_display()})"

    class Meta:
        ordering = ['rank__rank_order', 'staff__date_join', 'id']
        verbose_name = '09. 임원 등기/재임 정보'
        verbose_name_plural = '09. 임원 등기/재임 정보'
