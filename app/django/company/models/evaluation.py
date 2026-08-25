from django.db import models
from .company import Company
from .organization import JobGrade
from .staff import Staff


# 직급별 승급 기준 및 정책
class PromotionPolicy(models.Model):
    """직급별 승급 기준 및 정책
        # ├─ 최소 근속기간
        # ├─ 평가등급
        # ├─ 필수역량
        # ├─ 징계 여부
        # └─ 승급 제한 조건
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='promotion_policies', verbose_name='회사')
    current_grade = models.ForeignKey(JobGrade, on_delete=models.CASCADE, related_name='promotion_policies_from',
                                      verbose_name='현재 직급')
    target_grade = models.ForeignKey(JobGrade, on_delete=models.CASCADE, related_name='promotion_policies_to',
                                     verbose_name='승급 대상 직급')
    min_years = models.PositiveSmallIntegerField('최소 체류기간(년)', default=3, help_text='승급 심사 대상이 되기 위한 최소 근속 년수')
    min_avg_grade_point = models.DecimalField('최소 평가 평점', max_digits=4, decimal_places=2, null=True, blank=True,
                                              help_text='최근 평가 평균 점수 기준 (예: 80.00)')
    required_eval_grade = models.CharField('최소 평가 등급 요건', max_length=20, blank=True, help_text='예: 최근 2개년 평균 B+ 이상')
    required_credentials = models.CharField('필수 역량/자격 요건', max_length=255, blank=True,
                                            help_text='예: 필수 교육 이수, 어학 기준, 관련 자격증 등')
    disqualification_conditions = models.CharField('승급 결격 사유', max_length=255, blank=True,
                                                   help_text='예: 최근 1년 내 징계 처분 이력 등')
    description = models.TextField('세부 기준 설명', blank=True)
    is_active = models.BooleanField('사용 여부', default=True)

    def __str__(self):
        return f'{self.current_grade.code} → {self.target_grade.code} 승급 정책'

    class Meta:
        ordering = ['current_grade__id', 'target_grade__id']
        verbose_name = '14. 직급 승급 정책'
        verbose_name_plural = '14. 직급 승급 정책'
        unique_together = ('company', 'current_grade', 'target_grade')


# 임직원 인사/업적 평가 기록
class StaffEvaluation(models.Model):
    """직원 인사/업적 평가 기록"""
    PERIOD_CHOICES = (
        ('yearly', '연간'),
        ('1H', '상반기'),
        ('2H', '하반기'),
    )
    GRADE_CHOICES = (
        ('S', 'S (탁월)'),
        ('A', 'A (우수)'),
        ('B', 'B (보통)'),
        ('C', 'C (미흡)'),
        ('D', 'D (불량)'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='evaluations', verbose_name='회사')
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='evaluations', verbose_name='피평가자')
    eval_year = models.PositiveSmallIntegerField('평가 연도')
    eval_period = models.CharField('평가 주기', max_length=10, choices=PERIOD_CHOICES, default='yearly')
    grade = models.CharField('평가 등급', max_length=5, choices=GRADE_CHOICES)
    score = models.DecimalField('평가 점수', max_digits=5, decimal_places=2, null=True, blank=True,
                                help_text='100점 만점 환산 점수')
    achievement_summary = models.TextField('주요 업적 요약', blank=True)
    evaluator = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='evaluated_staffs', verbose_name='1차 평가자')
    reviewer = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='reviewed_staffs', verbose_name='2차 평가자/확인자')
    notes = models.CharField('종합 의견', max_length=255, blank=True)

    def __str__(self):
        return f'{self.staff.name} - {self.eval_year}년 {self.get_eval_period_display()} ({self.grade})'

    class Meta:
        ordering = ['-eval_year', 'eval_period', 'staff__name']
        verbose_name = '15. 직원 인사 평가'
        verbose_name_plural = '15. 직원 인사 평가'
        unique_together = ('staff', 'eval_year', 'eval_period')


# 승급 심사 대상 및 발령 이력
class PromotionCandidate(models.Model):
    """승급 심사 대상 및 발령 이력"""
    STATUS_CHOICES = (
        ('candidate', '심사 대상'),
        ('recommended', '부서 추천'),
        ('approved', '승진 확정'),
        ('rejected', '심사 탈락'),
        ('hold', '심사 보류'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='promotion_candidates',
                                verbose_name='회사')
    policy = models.ForeignKey(PromotionPolicy, on_delete=models.CASCADE, related_name='candidates',
                               verbose_name='적용 승급 정책')
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='promotion_records', verbose_name='승급 대상자')
    eval_year = models.PositiveSmallIntegerField('심사 연도')
    tenure_years = models.DecimalField('현 직급 체류 년수', max_digits=4, decimal_places=1, default=0.0)
    avg_eval_score = models.DecimalField('평가 평균 점수', max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField('심사 상태', max_length=15, choices=STATUS_CHOICES, default='candidate')
    committee_review = models.TextField('인사위원회 심의 의견', blank=True)
    promoted_date = models.DateField('승진 발령일', null=True, blank=True)

    def __str__(self):
        return f'[{self.eval_year}] {self.staff.name} ({self.policy.current_grade.code} → {self.policy.target_grade.code}) - {self.get_status_display()}'

    class Meta:
        ordering = ['-eval_year', 'policy__current_grade__id', 'staff__name']
        verbose_name = '16. 승급 심사 및 발령'
        verbose_name_plural = '16. 승급 심사 및 발령'
