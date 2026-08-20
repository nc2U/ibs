from django.db import models

from _utils.file_cleanup import file_cleanup_signals
from _utils.file_upload import get_company_image_path


class Company(models.Model):
    name = models.CharField('회사명', max_length=30, unique=True, db_index=True)
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


file_cleanup_signals(Logo)


class Department(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments', verbose_name='회사')
    upper_depart = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='sub_departs',
                                     verbose_name='상위 부서')
    level = models.PositiveSmallIntegerField('레벨', default=1,
                                             help_text='부서 간 상하 소속 관계에 의한 단계, 최상위 부서인 경우 1단계 이후 각 뎁스 마다 1씩 증가')
    name = models.CharField('부서', max_length=30, db_index=True)
    task = models.CharField('주요 업무', max_length=255, null=True, blank=True)
    manager = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='managed_departs', verbose_name='책임자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = '02. 부서 정보'
        verbose_name_plural = '02. 부서 정보'

    def save(self, *args, **kwargs):
        # 1. 상위 부서 유무에 따른 level 자동 계산
        if not self.upper_depart:
            self.level = 1
        else:
            self.level = self.upper_depart.level + 1

        super().save(*args, **kwargs)

        # 2. 부서의 레벨이 변경된 경우 하위 부서들도 연쇄 재계산 (재귀 호출)
        for sub in self.sub_departs.all():
            if sub.level != self.level + 1:
                sub.save()


class JobGrade(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='ranks', verbose_name='회사')
    code = models.CharField('직급 코드', max_length=10)
    role = models.CharField('역할', max_length=100, blank=True)
    promotion_criteria = models.TextField('승급 기준', blank=True)  # 추후 PromotionPolicy 모델과 연결 고도화
    min_promotion_years = models.PositiveSmallIntegerField('최소 근속기간(년)', null=True, blank=True)

    def __str__(self):
        return self.code

    class Meta:
        ordering = ['id']
        verbose_name = "03. 직급 정보"
        verbose_name_plural = "03. 직급 정보"
        unique_together = ('company', 'code')  # 회사 내 직급 코드 중복 방지


# PromotionPolicy
# ├─ 최소 근속기간
# ├─ 평가등급
# ├─ 필수역량
# ├─ 징계 여부
# └─ 승급 제한 조건


class Position(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='positions', verbose_name='회사')
    name = models.CharField('직위', max_length=30, db_index=True)
    grades = models.ManyToManyField(JobGrade, related_name='positions', verbose_name='직책')
    desc = models.CharField('설명', max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = "04. 직위 정보"
        verbose_name_plural = "04. 직위 정보"


class DutyTitle(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='titles', verbose_name='회사')
    code = models.CharField('직책 코드', max_length=20, blank=True, help_text='예: CEO, DIV_HEAD, HQ_HEAD, TEAM_LEADER 등')
    name = models.CharField('직책', max_length=30, db_index=True)
    desc = models.CharField('설명', max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = "05. 직책 정보"
        verbose_name_plural = "05. 직책 정보"


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


class Staff(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='staffs', verbose_name='회사')
    SORT_CHOICES = (('1', '임원'), ('2', '직원'))
    sort = models.CharField('구분', max_length=1, choices=SORT_CHOICES, default='1')
    user = models.OneToOneField('accounts.User', on_delete=models.DO_NOTHING, null=True,
                                blank=True, verbose_name='유저 정보')
    name = models.CharField('직원 성명', max_length=10, db_index=True)
    id_number = models.CharField('주민등록번호', max_length=14)
    personal_phone = models.CharField('휴대전화', max_length=13)
    email = models.EmailField('이메일', null=True, blank=True)
    grade = models.ForeignKey(JobGrade, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='직급 정보')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='직위 정보')
    date_join = models.DateField('입사일')
    STATUS_CHOICES = (('1', '근무 중'), ('2', '휴직 중'), ('3', '퇴직신청'), ('4', '퇴사처리'))
    status = models.CharField('상태', max_length=1, choices=STATUS_CHOICES, default='1')
    date_leave = models.DateField('퇴사일', null=True, blank=True)
    is_hq_financial_officer = models.BooleanField('본사 금융 관리 권한', default=False,
                                                  help_text='본사 프로젝트의 상세 자금 흐름을 열람할 수 있는 권한입니다. Django Admin 에서만 제어 합니다.')
    is_hq_hr_officer = models.BooleanField('본사 인사 관리 권한', default=False,
                                           help_text='본사 프로젝트의 인사 관리 흐름을 열람할 수 있는 권한입니다. Django Admin 에서만 제어 합니다.')

    @property
    def primary_assignment(self):
        """주보직 (없으면 첫 번째 보직)"""
        return self.assignments.filter(is_primary=True).first() or self.assignments.first()

    @property
    def department(self):
        """주보직의 소속 부서"""
        return self.primary_assignment.department if self.primary_assignment else None

    @property
    def duty(self):
        """주보직의 직책"""
        return self.primary_assignment.duty if self.primary_assignment else None

    @property
    def executive_rank(self):
        """임원 직위 (임원인 경우)"""
        return self.executive.rank.name if hasattr(self,
                                                   'executive') and self.executive and self.executive.rank else None

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-date_join']
        verbose_name = '07. 직원 정보'
        verbose_name_plural = '07. 직원 정보'


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
    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, related_name='executive', verbose_name='임원')
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
        verbose_name = '08. 임원 등기/재임 정보'
        verbose_name_plural = '08. 임원 등기/재임 정보'


class StaffAssignment(models.Model):
    """직원 보직/발령 정보 (주 보직 및 겸직 지원)"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='assignments', verbose_name='회사')
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='assignments', verbose_name='직원')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='assignments',
                                   verbose_name='소속 부서')
    duty = models.ForeignKey(DutyTitle, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='직책')
    is_primary = models.BooleanField('주 부서/보직 여부', default=True, help_text='기본 소속 여부 (직원당 1개만 True)')
    assigned_tasks = models.CharField('담당 업무 요약', max_length=255, blank=True, help_text='예: 재무회계/인사/총무 총괄, 개발사업성 검토 등')

    class Meta:
        ordering = ['-is_primary', 'id']
        verbose_name = '09. 직원 보직/겸직 정보'
        verbose_name_plural = '09. 직원 보직/겸직 목록'
        unique_together = ('staff', 'department', 'duty')

    def __str__(self):
        role = self.duty.name if self.duty else '팀원'
        primary_str = '[주]' if self.is_primary else '[겸]'
        return f'{primary_str} {self.staff.name} - {self.department.name} ({role})'

    def save(self, *args, **kwargs):
        # 주 보직(is_primary=True)으로 저장 시 동일 직원의 다른 보직은 is_primary=False로 변경
        if self.is_primary and self.staff_id:
            StaffAssignment.objects.filter(staff_id=self.staff_id, is_primary=True).exclude(pk=self.pk).update(
                is_primary=False)
        super().save(*args, **kwargs)


class PromotionPolicy(models.Model):
    """직급별 승급 기준 및 정책"""
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
        verbose_name = '10. 직급 승급 정책'
        verbose_name_plural = '10. 직급 승급 정책'
        unique_together = ('company', 'current_grade', 'target_grade')


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
        verbose_name = '11. 직원 인사 평가'
        verbose_name_plural = '11. 직원 인사 평가'
        unique_together = ('staff', 'eval_year', 'eval_period')


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
        verbose_name = '12. 승급 심사 및 발령'
        verbose_name_plural = '12. 승급 심사 및 발령'
