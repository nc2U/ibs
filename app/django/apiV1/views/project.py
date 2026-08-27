import logging
from datetime import datetime

from django.db.models import Sum, F, Case, When
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apiV1.permissions.auth_perms import permissions, IsProjectStaffOrReadOnly
from apiV1.permissions.ibs_perms import IbsModulePermission
from ledger.models import ProjectAccountingEntry, ProjectBankTransaction
from project.models import Project, ProjectIncBudget, ProjectOutBudget, Site, SiteOwner, \
    SiteOwnshipRelationship, SiteContract, SiteOwnerConsultationLogs
from work.models import IssueProject
from ..pagination import PageNumberPaginationFifty, PageNumberPaginationOneHundred, \
    PageNumberPaginationOneThousand
from ..serializers.project import ProjectSerializer, ProjectIncBudgetSerializer, ProjectOutBudgetSerializer, \
    StatusOutBudgetSerializer, LedgerExecAmountToBudgetSerializer, TotalSiteAreaSerializer, SiteSerializer, \
    AllSiteSerializer, TotalOwnerAreaSerializer, SiteOwnerSerializer, AllOwnerSerializer, \
    SiteOwnshipRelationshipSerializer, TotalContractedAreaSerializer, SiteContractSerializer, \
    SiteOwnerConsultationLogsSerializer

logger = logging.getLogger(__name__)


def get_accessible_project_ids(user):
    return IssueProject.objects.filter(members__user=user).values_list('project__id', flat=True)


# 사이트 액션별 권한 매핑 (SiteOwnerViewSet, SiteContractViewSet 공통)
_SITE_ACTION_PERMISSION_MAP = {
    'list': 'site.read',
    'retrieve': 'site.read',
    'find_page': 'site.read',
    'create': 'site.create',
    'update': 'site.update',
    'partial_update': 'site.update',
    'destroy': 'site.delete',
}


# Project --------------------------------------------------------------------------
class ProjectFilterSet(FilterSet):
    class Meta:
        model = Project
        fields = ('kind', 'start_year', 'is_direct_manage', 'is_returned_area',
                  'is_unit_set', 'issue_project__status')


class ProjectViewSet(viewsets.ModelViewSet):
    # N+1 방지: 관계 필드 eager loading
    queryset = Project.objects.select_related(
        'issue_project__company', 'salesbillissue'
    ).all()
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_class = ProjectFilterSet

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(pk__in=get_accessible_project_ids(user))


class ProjectIncBudgetViewSet(viewsets.ModelViewSet):
    queryset = ProjectIncBudget.objects.all()
    serializer_class = ProjectIncBudgetSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project', 'unit_type__sort')

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(project_id__in=get_accessible_project_ids(user))


class ProjectOutBudgetViewSet(viewsets.ModelViewSet):
    queryset = ProjectOutBudget.objects.all()
    serializer_class = ProjectOutBudgetSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project',)

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(project_id__in=get_accessible_project_ids(user))


class StatusOutBudgetViewSet(ProjectOutBudgetViewSet):
    serializer_class = StatusOutBudgetSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        use_ledger = self.request.query_params.get('use_ledger', 'false').lower() == 'true'

        if use_ledger:
            # ledger 기반: account가 있고, depth=2, is_category_only=False인 예산만
            queryset = queryset.select_related(
                'account', 'account__parent', 'account_d2', 'account_d3'
            ).filter(
                account__isnull=False,
                account__depth=2,
                account__category='expense',
                account__is_category_only=False
            )
        return queryset


class ExecAmountToBudgetViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LedgerExecAmountToBudgetSerializer
    pagination_class = PageNumberPaginationFifty
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project',)

    def get_queryset(self):
        project = self.request.query_params.get('project')
        request_date = self.request.query_params.get('date')

        # date 파라미터 유효성 검증 및 단일 파싱 (기존: 이중 strptime 호출, 모듈 상수 TODAY 사용)
        try:
            parsed_date = datetime.strptime(request_date, '%Y-%m-%d') if request_date else datetime.today()
        except ValueError:
            raise ValidationError({'date': '날짜 형식이 잘못되었습니다. YYYY-MM-DD 형식으로 입력하세요.'})

        date = parsed_date.strftime('%Y-%m-%d')
        month_first = parsed_date.replace(day=1).strftime('%Y-%m-%d')

        queryset = ProjectAccountingEntry.objects.filter(
            account__depth=2,
            account__is_category_only=False,
            account__category='expense',
        ).select_related('account')

        if project:
            queryset = queryset.filter(project_id=project)

        # 출금 거래만 (sort_id=2)
        valid_transactions = ProjectBankTransaction.objects.filter(
            sort_id=2,
            deal_date__lte=date
        )
        if project:
            valid_transactions = valid_transactions.filter(project_id=project)
        valid_transaction_ids = valid_transactions.values_list('transaction_id', flat=True)

        queryset = queryset.filter(transaction_id__in=valid_transaction_ids)

        # 당월 거래 ID
        month_transactions = ProjectBankTransaction.objects.filter(
            sort_id=2,
            deal_date__gte=month_first,
            deal_date__lte=date
        )
        if project:
            month_transactions = month_transactions.filter(project_id=project)
        month_transaction_ids = month_transactions.values_list('transaction_id', flat=True)

        return queryset.values('account').annotate(
            all_sum=Sum('amount'),
            month_sum=Sum(Case(
                When(transaction_id__in=month_transaction_ids, then=F('amount')),
                default=0
            ))
        )


class TotalSiteAreaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TotalSiteAreaSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project',)

    def get_queryset(self):
        return Site.objects.values('project') \
            .annotate(official=Sum('official_area'),
                      returned=Sum('returned_area'))


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationOneHundred
    filterset_fields = ('project',)
    search_fields = ('district', 'lot_number', 'site_purpose', 'owners__owner')

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            queryset = queryset.filter(project_id__in=get_accessible_project_ids(user))
        # M2M(owners) 역방향 검색 시 중복 결과 방지
        if self.request.query_params.get('search'):
            return queryset.distinct()
        return queryset

    @property
    def required_permission(self):
        return _SITE_ACTION_PERMISSION_MAP.get(self.action, 'site.read')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)


class AllSiteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Site.objects.all().select_related('project')
    serializer_class = AllSiteSerializer
    pagination_class = PageNumberPaginationOneThousand
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project',)

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        return qs.filter(project_id__in=get_accessible_project_ids(user))


class TotalOwnerAreaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TotalOwnerAreaSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project',)

    def get_queryset(self):
        return Site.objects.values('project') \
            .annotate(owned_area=Sum('siteownshiprelationship__owned_area'))


class FindPageMixin:
    """특정 ID의 항목이 몇 번째 페이지에 있는지 찾는 공통 액션 Mixin
    (SiteOwnerViewSet, SiteContractViewSet에서 공유)
    """

    @action(detail=False, methods=['get'])
    def find_page(self, request):
        """특정 ID의 항목이 몇 번째 페이지에 있는지 찾기"""
        highlight_id = request.query_params.get('highlight_id')
        if not highlight_id:
            return Response({'error': 'highlight_id parameter required'}, status=400)

        try:
            highlight_id = int(highlight_id)
        except ValueError:
            return Response({'error': 'highlight_id must be integer'}, status=400)

        # 현재 필터 조건을 적용한 queryset 가져오기
        queryset = self.filter_queryset(self.get_queryset())

        # 해당 ID가 존재하는지 확인 (model-agnostic, DoesNotExist 개별 처리 불필요)
        if not queryset.filter(pk=highlight_id).exists():
            return Response({'error': 'Item not found'}, status=404)

        # 기본 정렬이 -id 순(최신순)이므로 해당 항목보다 id가 큰 항목 개수 계산
        items_before = queryset.filter(id__gt=highlight_id).count()

        # 페이지 크기 파라미터 읽기 (기본값: 10)
        page_size = request.query_params.get('limit', '10')
        try:
            page_size = int(page_size) if page_size else 10
        except ValueError:
            page_size = 10

        return Response({'page': (items_before // page_size) + 1})


class SiteOwnerViewSet(FindPageMixin, viewsets.ModelViewSet):
    queryset = SiteOwner.objects.all()
    serializer_class = SiteOwnerSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneHundred

    @property
    def required_permission(self):
        return _SITE_ACTION_PERMISSION_MAP.get(self.action, 'site.read')

    filterset_fields = ('project', 'own_sort', 'use_consent')
    search_fields = ('owner', 'phone1', 'phone2', 'sites__lot_number', 'note')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)


class AllOwnerViewSet(viewsets.ReadOnlyModelViewSet):
    """조회 전용 ViewSet: 드롭다운 등 단순 목록 조회 용도로 쓰기 엔드포인트 미노출"""
    queryset = SiteOwner.objects.all().order_by('id')
    serializer_class = AllOwnerSerializer
    pagination_class = PageNumberPaginationOneThousand
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project',)


class SiteRelationViewSet(viewsets.ModelViewSet):
    queryset = SiteOwnshipRelationship.objects.all()
    serializer_class = SiteOwnshipRelationshipSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)


class TotalContractedAreaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TotalContractedAreaSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('project',)

    def get_queryset(self):
        return SiteContract.objects.values('project') \
            .annotate(contracted_area=Sum('contract_area'))


class SiteContractViewSet(FindPageMixin, viewsets.ModelViewSet):
    queryset = SiteContract.objects.all()
    serializer_class = SiteContractSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneHundred

    @property
    def required_permission(self):
        return _SITE_ACTION_PERMISSION_MAP.get(self.action, 'site.read')

    filterset_fields = ('project', 'owner__own_sort')
    search_fields = ('owner__owner', 'owner__phone1', 'acc_bank', 'acc_owner', 'note')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)


class SiteOwnerConsultationLogsViewSet(viewsets.ModelViewSet):
    """토지 소유자 상담 내역 관리 ViewSet"""
    queryset = SiteOwnerConsultationLogs.objects.select_related('consultant').all()
    serializer_class = SiteOwnerConsultationLogsSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('site_owner', 'channel')
    ordering = ['-consultation_date', '-created']

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user, consultant=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)

