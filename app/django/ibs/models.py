from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class AccountSort(models.Model):
    name = models.CharField(max_length=2, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = "01. (공통) - 입출금 구분"
        verbose_name_plural = "01. (공통) - 입출금 구분"


class AccountSubD1(models.Model):
    sorts = models.ManyToManyField('ibs.AccountSort')
    code = models.CharField(max_length=3)
    name = models.CharField(max_length=10, db_index=True)
    description = models.CharField(max_length=20)

    def __str__(self):
        return f'[{self.code}] {self.name} 계정'

    class Meta:
        ordering = ['id']
        verbose_name = "02. (공통) - 회계계정 과목"
        verbose_name_plural = "02. (공통) - 회계계정 과목"


class AccountSubD2(models.Model):
    d1 = models.ForeignKey(AccountSubD1, on_delete=models.CASCADE, related_name='acc_d2s')
    code = models.CharField(max_length=3)
    name = models.CharField(max_length=20, db_index=True)
    description = models.CharField(max_length=50)

    def __str__(self):
        return f'[{self.code}] {self.name}'

    class Meta:
        ordering = ['id']
        verbose_name = "03. 본사 계정"
        verbose_name_plural = "03. 본사 계정"


class AccountSubD3(models.Model):
    sort = models.ForeignKey(AccountSort, on_delete=models.CASCADE)
    d2 = models.ForeignKey(AccountSubD2, on_delete=models.CASCADE, related_name='acc_d3s')
    code = models.CharField(max_length=3)
    name = models.CharField(max_length=20, db_index=True)
    is_hide = models.BooleanField(default=False)
    is_special = models.BooleanField(default=False)
    description = models.CharField(max_length=50)

    def __str__(self):
        return f'[{self.code}] {self.name}'

    class Meta:
        ordering = ['id']
        verbose_name = "04. 본사 세부계정"
        verbose_name_plural = "04. 본사 세부계정"


class ProjectAccountD2(models.Model):
    d1 = models.ForeignKey(AccountSubD1, on_delete=models.CASCADE, related_name='pro_d2s')
    code = models.CharField(max_length=3)
    name = models.CharField(max_length=20, db_index=True)
    description = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)
        verbose_name = "05. 프로젝트 계정"
        verbose_name_plural = "05. 프로젝트 계정"


class ProjectAccountD3(models.Model):
    sort = models.ForeignKey(AccountSort, on_delete=models.CASCADE)
    d2 = models.ForeignKey(ProjectAccountD2, on_delete=models.CASCADE, related_name='pro_d3s')
    code = models.CharField(max_length=3)
    is_payment = models.BooleanField(default=False)
    is_related_contract = models.BooleanField(default=False)
    name = models.CharField(max_length=20, db_index=True)
    description = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)
        verbose_name = "06. 프로젝트 세부계정"
        verbose_name_plural = "06. 프로젝트 세부계정"


class UserWidgetConfig(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard_config')
    layouts = models.JSONField('레이아웃 설정', default=dict, help_text='브레이크포인트별(lg, md, sm 등) 위젯 배치 및 크기 정보')
    visible_widgets = models.JSONField('표시 위젯 목록', default=list, help_text='현재 활성화되어 화면에 노출되는 위젯 ID 리스트')
    version = models.PositiveIntegerField('데이터 버전', default=1, help_text='포맷 변경 시 하위 호환성 관리를 위한 버전 번호')
    created = models.DateTimeField('생성일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)

    def __str__(self):
        return f'{self.user.username}의 대시보드 설정'

    class Meta:
        ordering = ['-id']
        verbose_name = '07. 대시보드 위젯 설정'
        verbose_name_plural = '07. 대시보드 위젯 설정'


class CalendarSchedule(models.Model):
    title = models.CharField('일정 제목', max_length=100, db_index=True)
    all_day = models.BooleanField(default=True)
    start_date = models.DateField('시작 일자', null=True, blank=True)
    end_date = models.DateField('종료 일자', null=True, blank=True)
    start_time = models.DateTimeField('시작 시간', null=True, blank=True)
    end_time = models.DateTimeField('종료 시간', null=True, blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='등록자')
    created = models.DateTimeField('등록일시', auto_now_add=True)
    updated = models.DateTimeField('편집일시', auto_now=True)

    def __str__(self):
        return self.title

    @staticmethod
    def _extract_local_date(dt_or_str):
        from django.utils.dateparse import parse_datetime, parse_date
        if hasattr(dt_or_str, 'date'):
            if timezone.is_aware(dt_or_str):
                return timezone.localtime(dt_or_str).date()
            return dt_or_str.date()
        if isinstance(dt_or_str, str):
            parsed = parse_datetime(dt_or_str)
            if parsed:
                if timezone.is_aware(parsed):
                    return timezone.localtime(parsed).date()
                return parsed.date()
            return parse_date(dt_or_str[:10])
        return None

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({'end_date': '종료 일자는 시작 일자 이후여야 합니다.'})
        if not self.all_day and self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValidationError({'end_time': '종료 시간은 시작 시간 이후여야 합니다.'})

    def save(self, *args, **kwargs):
        if not self.start_date and self.start_time:
            self.start_date = self._extract_local_date(self.start_time)

        if not self.end_date and self.end_time:
            self.end_date = self._extract_local_date(self.end_time)

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-id']
        verbose_name = '08. 캘린더 일정'
        verbose_name_plural = '08. 캘린더 일정'


class WiseSaying(models.Model):
    saying_ko = models.CharField(max_length=300)
    saying_en = models.CharField(max_length=300)
    spoked_by = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f'{self.saying_ko} - {self.spoked_by}'

    class Meta:
        ordering = ['id']
        verbose_name = "오늘의 한마디"
        verbose_name_plural = "오늘의 한마디"
