from django.db import models
from .company import Company
from .organization import Department, JobGrade, Position, DutyTitle


# 임직원 모델
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
    STATUS_CHOICES = (('1', '재직'), ('2', '휴직'), ('3', '퇴직신청'), ('4', '퇴직'))
    status = models.CharField('상태', max_length=1, choices=STATUS_CHOICES, default='1')
    date_leave = models.DateField('퇴사일', null=True, blank=True)
    EMPLOYMENT_CHOICES = (
        ('regular', '정규직'),
        ('contract', '계약직/기간제'),
        ('dispatched', '파견직'),
        ('commissioned', '위촉직/자문'),
        ('intern', '인턴/수습'),
        ('part_time', '파트타임/일용'),
    )
    employment_type = models.CharField('고용 형태', max_length=20, choices=EMPLOYMENT_CHOICES, default='regular')
    contract_end_date = models.DateField('계약 만료일', null=True, blank=True, help_text='계약직/파견직/위촉직의 계약 만료 예정일')
    probation_end_date = models.DateField('수습 만료일', null=True, blank=True)

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


# 보직 / 발령 모델
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
        verbose_name = '08. 직원 보직/겸직 정보'
        verbose_name_plural = '08. 직원 보직/겸직 목록'
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


# 인사 발령 및 신분 변동 이력
class PersonnelOrder(models.Model):
    """인사 발령 및 신분 변동 이력 (시계열 인사 히스토리)"""
    ORDER_TYPE_CHOICES = (
        ('10', '채용/신규입사'),
        ('20', '승진/승급'),
        ('30', '부서이동(전보)'),
        ('40', '보직임면/겸직'),
        ('50', '휴직'),
        ('51', '복직'),
        ('60', '파견/전적'),
        ('70', '포상/표창'),
        ('80', '징계/문책'),
        ('90', '퇴사/면직'),
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='personnel_orders', verbose_name='회사')
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='orders', verbose_name='대상 직원')
    order_type = models.CharField('발령 구분', max_length=2, choices=ORDER_TYPE_CHOICES)
    order_date = models.DateField('발령 일자(시행일)')
    effective_end_date = models.DateField('종료 일자', null=True, blank=True, help_text='휴직/파견/겸직 등의 종료 예정일')
    order_no = models.CharField('발령 호수/문서번호', max_length=50, blank=True)

    # 발령 전 스냅샷
    prev_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='prev_orders', verbose_name='이전 부서')
    prev_grade = models.ForeignKey(JobGrade, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='prev_orders', verbose_name='이전 직급')
    prev_position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='prev_orders', verbose_name='이전 직위')
    prev_duty = models.ForeignKey(DutyTitle, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='prev_orders', verbose_name='이전 직책')

    # 발령 후 상태
    new_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='new_orders', verbose_name='발령 부서')
    new_grade = models.ForeignKey(JobGrade, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='new_orders', verbose_name='발령 직급')
    new_position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='new_orders', verbose_name='발령 직위')
    new_duty = models.ForeignKey(DutyTitle, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='new_orders', verbose_name='발령 직책')

    description = models.CharField('발령 사유/세부 내용', max_length=255, blank=True)
    is_processed = models.BooleanField('현상태 자동반영 여부', default=True,
                                       help_text='발령 저장 시 Staff 및 StaffAssignment 현재 상태 자동 갱신 여부')

    class Meta:
        ordering = ['-order_date', '-id']
        verbose_name = '10. 인사 발령 이력'
        verbose_name_plural = '10. 인사 발령 이력'

    def __str__(self):
        return f'[{self.get_order_type_display()}] {self.staff.name} ({self.order_date})'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_processed and self.staff:
            # 발령에 따른 Staff/StaffAssignment 상태 자동 동기화
            staff = self.staff
            if self.new_grade:
                staff.grade = self.new_grade
            if self.new_position:
                staff.position = self.new_position
            if self.order_type == '50':  # 휴직
                staff.status = '2'
            elif self.order_type == '51':  # 복직
                staff.status = '1'
            elif self.order_type == '90':  # 퇴사
                staff.status = '4'
                if not staff.date_leave:
                    staff.date_leave = self.order_date
            elif self.order_type in ('10', '20', '30', '40'):  # 일반 상태
                if staff.status in ('2', '3'):
                    staff.status = '1'
            staff.save()

            if self.new_department or self.new_duty:
                primary_assign = staff.assignments.filter(is_primary=True).first()
                if primary_assign:
                    if self.new_department:
                        primary_assign.department = self.new_department
                    if self.new_duty:
                        primary_assign.duty = self.new_duty
                    primary_assign.save()
                elif self.new_department:
                    StaffAssignment.objects.create(
                        company=self.company,
                        staff=staff,
                        department=self.new_department,
                        duty=self.new_duty,
                        is_primary=True,
                        assigned_tasks=self.description or '발령 보직'
                    )


# 직원 경력 사항 (입사 전 및 사외 주요 경력)
class StaffCareer(models.Model):
    """직원 이전 경력 사항 (호봉/근속/자격 인정 기반)"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='staff_careers', verbose_name='회사')
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='careers', verbose_name='직원')
    company_name = models.CharField('근무처/기관명', max_length=50)
    department_name = models.CharField('부서/조직명', max_length=50, blank=True)
    position_title = models.CharField('직위/직급', max_length=30, blank=True)
    assigned_tasks = models.CharField('담당 업무', max_length=255, blank=True)
    start_date = models.DateField('시작일')
    end_date = models.DateField('종료일', null=True, blank=True)
    recognized_ratio = models.PositiveSmallIntegerField('경력 인정률(%)', default=100, help_text='호봉/승진 연수 인정 비율')
    note = models.CharField('비고/퇴사사유', max_length=255, blank=True)

    class Meta:
        ordering = ['-start_date', '-id']
        verbose_name = '11. 직원 경력 사항'
        verbose_name_plural = '11. 직원 경력 사항'

    def __str__(self):
        return f'{self.staff.name} - {self.company_name} ({self.position_title})'


# 직원 보유 자격 및 면허
class StaffCertificate(models.Model):
    """직원 보유 자격 및 면허 (건설 기술인 등급, 공인중개사, 기사 자격 등)"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='staff_certificates', verbose_name='회사')
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='certificates', verbose_name='직원')
    name = models.CharField('자격/면허명', max_length=50, db_index=True)
    grade = models.CharField('등급/급수', max_length=30, blank=True, help_text='예: 특급기술자, 1급, 공인중개사 등')
    cert_number = models.CharField('자격/등록 번호', max_length=50, blank=True)
    issuer = models.CharField('발급 기관', max_length=50, blank=True)
    acquired_date = models.DateField('취득일자')
    expire_date = models.DateField('만료/갱신일자', null=True, blank=True)
    has_allowance = models.BooleanField('자격 수당 지급 여부', default=False)
    note = models.CharField('비고', max_length=255, blank=True)

    class Meta:
        ordering = ['-acquired_date', '-id']
        verbose_name = '12. 직원 자격/면허'
        verbose_name_plural = '12. 직원 자격/면허'

    def __str__(self):
        grade_str = f' ({self.grade})' if self.grade else ''
        return f'{self.staff.name} - {self.name}{grade_str}'


# 직원 포상 및 징계 이력
class StaffRewardPunishment(models.Model):
    """직원 포상 및 징계 이력 (인사평가 및 승진 심사 결격사유 검증용)"""
    SORT_CHOICES = (
        ('reward', '포상/표창'),
        ('punish', '징계/문책'),
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='staff_rewards_punishments',
                                verbose_name='회사')
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='rewards_punishments', verbose_name='직원')
    sort = models.CharField('구분', max_length=10, choices=SORT_CHOICES, default='reward')
    type_name = models.CharField('포상/징계 항목명', max_length=50, help_text='예: 우수사원상, 견책, 감봉, 정직 등')
    action_date = models.DateField('처분/수여 일자')
    expire_date = models.DateField('징계 효력 만료일', null=True, blank=True, help_text='승진 결격 효력 기간 등')
    reason = models.TextField('사유/근거')
    organization = models.CharField('수여/처분 기관(부서)', max_length=50, blank=True)
    note = models.CharField('비고', max_length=255, blank=True)

    class Meta:
        ordering = ['-action_date', '-id']
        verbose_name = '13. 직원 상벌 이력'
        verbose_name_plural = '13. 직원 상벌 이력'

    def __str__(self):
        return f'[{self.get_sort_display()}] {self.staff.name} - {self.type_name} ({self.action_date})'


# 직원 연차 부여 및 잔여 관리 모델
class StaffLeaveQuota(models.Model):
    """직원 연도별 연차 발생/부여 및 잔여 관리 마스터"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='leave_quotas', verbose_name='회사')
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='leave_quotas', verbose_name='직원')
    year = models.PositiveSmallIntegerField('대상 연도', db_index=True)
    granted_days = models.DecimalField('기본 발생 연차', max_digits=4, decimal_places=2, default=15.00,
                                       help_text='근로기준법 기준 연차 발생 일수')
    carry_over_days = models.DecimalField('이월/조정 연차', max_digits=4, decimal_places=2, default=0.00,
                                          help_text='전년도 이월 또는 수동 조정 일수')
    reward_days = models.DecimalField('포상/가산 연차', max_digits=4, decimal_places=2, default=0.00,
                                      help_text='장기근속 가산 또는 포상 부여 일수')
    valid_start = models.DateField('사용 가능 시작일')
    valid_end = models.DateField('사용 가능 만료일')
    note = models.CharField('비고', max_length=255, blank=True)

    class Meta:
        ordering = ['-year', 'staff']
        verbose_name = '14. 직원 연차 부여/잔여'
        verbose_name_plural = '14. 직원 연차 부여/잔여'
        unique_together = ('staff', 'year')

    def __str__(self):
        return f'{self.staff.name} - {self.year}년 연차 ({self.remaining_days}/{self.total_granted_days}일 잔여)'

    @property
    def total_granted_days(self):
        """총 부여 일수 = 기본 + 이월 + 포상"""
        return (self.granted_days or 0) + (self.carry_over_days or 0) + (self.reward_days or 0)

    @property
    def used_days(self):
        """해당 유효 기간 내 실제 차감된 연차 사용 일수 합계"""
        usages = self.staff.leave_usages.filter(
            start_date__gte=self.valid_start,
            start_date__lte=self.valid_end,
            is_cancelled=False,
            deduction_days__gt=0,
        )
        return sum(u.deduction_days for u in usages)

    @property
    def remaining_days(self):
        """잔여 연차 일수"""
        return self.total_granted_days - self.used_days


# 직원 휴가/연차 사용 상세 이력 모델
class StaffLeaveUsage(models.Model):
    """직원 휴가/연차 사용 상세 기록 (전자결재 승인 시 자동 연동)"""
    LEAVE_TYPE_CHOICES = (
        ('annual', '연차 (1일)'),
        ('half_am', '오전 반차 (0.5일)'),
        ('half_pm', '오후 반차 (0.5일)'),
        ('quarter', '반반차 (0.25일)'),
        ('official', '공가/예비군 (차감 없음)'),
        ('sick', '병가'),
        ('condolence', '경조 휴가 (차감 없음)'),
        ('reward', '포상 휴가'),
        ('substitute', '대체 휴가'),
        ('other', '기타 휴가'),
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='leave_usages', verbose_name='회사')
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='leave_usages', verbose_name='직원')
    leave_type = models.CharField('휴가 구분', max_length=20, choices=LEAVE_TYPE_CHOICES, default='annual')
    start_date = models.DateField('시작일')
    end_date = models.DateField('종료일')
    deduction_days = models.DecimalField('차감 일수', max_digits=4, decimal_places=2, default=1.00,
                                         help_text='연차에서 실제 차감되는 일수 (예: 1.0, 0.5, 0.25, 0.0)')
    approval_doc = models.ForeignKey(
        'approval.ApprovalDocument', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='leave_usages',
        verbose_name='연관 전자결재 문서'
    )
    reason = models.CharField('휴가 사유', max_length=255, blank=True)
    is_cancelled = models.BooleanField('취소 여부', default=False, help_text='결재 취소/반려 시 차감 복구용')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date', '-id']
        verbose_name = '15. 직원 휴가/연차 사용 기록'
        verbose_name_plural = '15. 직원 휴가/연차 사용 기록'

    def __str__(self):
        cancel_str = ' [취소됨]' if self.is_cancelled else ''
        return f'{self.staff.name} - {self.get_leave_type_display()} ({self.start_date}~{self.end_date}, -{self.deduction_days}일){cancel_str}'
