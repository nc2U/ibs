from django.core.exceptions import ValidationError
from django.db import models
from .company import Company


# 부서 모델 - 기능별 조직 단위
class Department(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments', verbose_name='회사')
    upper_depart = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='sub_departs',
                                     verbose_name='상위 부서')
    level = models.PositiveSmallIntegerField('레벨', default=1,
                                             help_text='부서 간 상하 소속 관계에 의한 단계, 최상위 부서인 경우 1단계 이후 각 뎁스 마다 1씩 증가')
    name = models.CharField('부서', max_length=30, db_index=True)
    task = models.CharField('주요 업무', max_length=255, null=True, blank=True)
    manager = models.ForeignKey('company.Staff', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='managed_departs', verbose_name='책임자')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = '03. 부서 정보'
        verbose_name_plural = '03. 부서 정보'

    def clean(self):
        super().clean()
        if self.upper_depart_id:
            if self.pk and self.upper_depart_id == self.pk:
                raise ValidationError({'upper_depart': '자기 자신을 상위 부서로 지정할 수 없습니다.'})
            parent = self.upper_depart
            visited = {self.pk} if self.pk else set()
            while parent:
                if parent.pk in visited:
                    raise ValidationError({'upper_depart': '상위 부서 지정 시 순환 참조가 발생합니다.'})
                visited.add(parent.pk)
                parent = parent.upper_depart

    def save(self, *args, **kwargs):
        visited = kwargs.pop('_visited_departs', None)
        if visited is None:
            visited = set()
        if self.pk:
            visited.add(self.pk)

        # 1. 상위 부서 유무에 따른 level 자동 계산
        if not self.upper_depart:
            self.level = 1
        else:
            self.level = self.upper_depart.level + 1

        super().save(*args, **kwargs)

        # 2. 부서의 레벨이 변경된 경우 하위 부서들도 연쇄 재계산 (순환 방어 포함)
        for sub in self.sub_departs.all():
            if sub.pk not in visited and sub.level != self.level + 1:
                sub.save(_visited_departs=visited)


# 직급 모델 - 조직에서의 성장 단계(조직 내에서 사람의 역할·책임·성장단계·보상 수준을 일관된 기준으로 관리하기 위한 체계)
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
        verbose_name = "04. 직급 정보"
        verbose_name_plural = "04. 직급 정보"
        unique_together = ('company', 'code')  # 회사 내 직급 코드 중복 방지


# 직위 모델 - 전문성·역할의 수준
class Position(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='positions', verbose_name='회사')
    name = models.CharField('직위', max_length=30, db_index=True)
    grades = models.ManyToManyField(JobGrade, related_name='positions', verbose_name='직책')
    desc = models.CharField('설명', max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = "05. 직위 정보"
        verbose_name_plural = "05. 직위 정보"


# 직책 모델 - 현재 맡고 있는 관리 책임
class DutyTitle(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='titles', verbose_name='회사')
    code = models.CharField('직책 코드', max_length=20, blank=True, help_text='예: CEO, DIV_HEAD, HQ_HEAD, TEAM_LEADER 등')
    name = models.CharField('직책', max_length=30, db_index=True)
    desc = models.CharField('설명', max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = "07. 직책 정보"
        verbose_name_plural = "07. 직책 정보"
