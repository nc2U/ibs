from django.conf import settings
from django.db import models


class DocumentType(models.Model):
    """결재 문서 유형 (관리자가 사전 정의)"""
    name = models.CharField('문서 유형명', max_length=100, unique=True)
    code = models.CharField('유형 코드', max_length=30, unique=True,
                            help_text='영문 대문자/언더스코어 (예: BIZ_APPROVAL)')
    description = models.TextField('설명', blank=True)
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
