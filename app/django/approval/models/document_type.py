from django.conf import settings
from django.db import models


class DocumentType(models.Model):
    """결재 문서 유형 (관리자가 사전 정의)"""

    ROUTE_ORGANIZATION = 'organization'
    ROUTE_TEMPLATE = 'template'
    ROUTE_TYPE_CHOICES = (
        (ROUTE_ORGANIZATION, '조직도 기반 자동 결재선 (직속 부서장 → 상위 부서장 → 전결/대표이사)'),
        (ROUTE_TEMPLATE, '수동 고정 템플릿 결재선'),
    )

    name = models.CharField('문서 유형명', max_length=100, unique=True)
    code = models.CharField('유형 코드', max_length=30, unique=True,
                            help_text='영문 대문자/언더스코어 (예: BIZ_APPROVAL)')
    description = models.TextField('설명', blank=True)
    route_type = models.CharField(
        '결재선 생성 방식', max_length=15,
        choices=ROUTE_TYPE_CHOICES, default=ROUTE_ORGANIZATION,
        help_text='조직도 기반: 기안자의 부서 조직도를 탐색하여 자동 결재선 구성 / 템플릿: 지정된 결재선 템플릿 사용'
    )
    final_approval_duty = models.ForeignKey(
        'company.DutyTitle', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='전결 직책',
        help_text='해당 직책자 승인 시 최종 완료 처리 (예: 팀장 전결, 본부장 전결). 미지정 시 대표이사까지 상신.'
    )
    final_dept_level = models.PositiveSmallIntegerField(
        '전결 부서 레벨', null=True, blank=True,
        help_text='예: 1로 설정 시 본부(1레벨) 부서장까지만 승인 후 완료 (대표이사 생략)'
    )
    form_schema = models.JSONField(
        '양식 스키마',
        default=list,
        blank=True,
        help_text='동적 양식 필드 정의 (JSON Schema). 예: [{"key":"purpose","label":"목적","type":"text","required":true}]'
    )
    is_active = models.BooleanField('사용 여부', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'[{self.code}] {self.name}'

    class Meta:
        ordering = ['id']
        verbose_name = '01. 결재 문서 유형'
        verbose_name_plural = '01. 결재 문서 유형 목록'


class RouteTemplate(models.Model):
    """결재선 단계 템플릿 (문서 유형에 종속)"""

    CONDITION_AND = 'AND'
    CONDITION_OR = 'OR'
    CONDITION_CHOICES = (
        (CONDITION_AND, '전원 승인 (AND)'),
        (CONDITION_OR, '1인 승인 (OR)'),
    )

    doc_type = models.ForeignKey(
        DocumentType, on_delete=models.CASCADE,
        related_name='route_templates', verbose_name='문서 유형'
    )
    step_order = models.PositiveSmallIntegerField('결재 순서', default=1)
    role_label = models.CharField('결재 단계명', max_length=50,
                                  help_text='예: 팀장 검토, 부서장 승인, 대표이사 최종')
    approvers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='approval_route_templates',
        verbose_name='결재자 목록',
        help_text='병렬 결재(공동대표 등)의 경우 복수 지정 가능'
    )
    condition = models.CharField(
        '결재 조건', max_length=3,
        choices=CONDITION_CHOICES, default=CONDITION_AND,
        help_text='AND: 전원 승인 필요 / OR: 1인 승인으로 진행'
    )

    def __str__(self):
        return f'{self.doc_type.name} - Step {self.step_order}: {self.role_label}'

    class Meta:
        ordering = ['doc_type', 'step_order']
        unique_together = ('doc_type', 'step_order')
        verbose_name = '02. 결재선 단계 템플릿'
        verbose_name_plural = '02. 결재선 단계 템플릿 목록'
