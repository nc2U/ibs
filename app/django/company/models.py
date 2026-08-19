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
    name = models.CharField('직급', max_length=10, db_index=True)
    promotion_period = models.PositiveSmallIntegerField('승급표준년수', null=True, blank=True)
    criteria_new = models.CharField('신입부여 기준', max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = "03. 직급 정보"
        verbose_name_plural = "03. 직급 정보"


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
    name = models.CharField('직책', max_length=5, db_index=True)
    desc = models.CharField('설명', max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = "05. 직책 정보"
        verbose_name_plural = "05. 직책 정보"


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
    def position(self):
        """주보직의 직위"""
        return self.primary_assignment.position if self.primary_assignment else None

    @property
    def duty(self):
        """주보직의 직책"""
        return self.primary_assignment.duty if self.primary_assignment else None

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-date_join']
        verbose_name = '06. 직원 정보'
        verbose_name_plural = '06. 직원 정보'


class StaffAssignment(models.Model):
    """직원 보직/발령 정보 (주 보직 및 겸직 지원)"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='assignments', verbose_name='회사')
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='assignments', verbose_name='직원')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='assignments', verbose_name='소속 부서')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='직위')
    duty = models.ForeignKey(DutyTitle, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='직책')
    is_primary = models.BooleanField('주 부서/보직 여부', default=True, help_text='기본 소속 여부 (직원당 1개만 True)')
    assigned_tasks = models.CharField('담당 업무 요약', max_length=255, blank=True, help_text='예: 재무회계/인사/총무 총괄, 개발사업성 검토 등')

    REPRESENT_CHOICES = (
        ('sole', '단독대표'),
        ('joint', '공동대표'),
        ('each', '각자대표'),
    )
    represent_type = models.CharField('대표권 구분', max_length=10, choices=REPRESENT_CHOICES, null=True, blank=True,
                                      help_text='대표이사 직책인 경우 대표권 형태')

    class Meta:
        ordering = ['-is_primary', 'id']
        verbose_name = '07. 직원 보직/겸직 정보'
        verbose_name_plural = '07. 직원 보직/겸직 목록'
        unique_together = ('staff', 'department', 'duty')

    def __str__(self):
        role = self.duty.name if self.duty else (self.position.name if self.position else '팀원')
        primary_str = '[주]' if self.is_primary else '[겸]'
        return f'{primary_str} {self.staff.name} - {self.department.name} ({role})'

    def save(self, *args, **kwargs):
        # 주 보직(is_primary=True)으로 저장 시 동일 직원의 다른 보직은 is_primary=False로 변경
        if self.is_primary and self.staff_id:
            StaffAssignment.objects.filter(staff_id=self.staff_id, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
