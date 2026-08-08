import logging

from django.db.models import F, Q
from django.http import FileResponse
from django.utils import timezone
from django_filters import BooleanFilter, ModelChoiceFilter, CharFilter, DateFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

logger = logging.getLogger(__name__)

from apiV1.permissions.auth_perms import permissions, IsProjectStaffOrReadOnly, IsWorkManagerReadOnly, IsStaffOrReadOnly
from apiV1.permissions.work_perms import ProjectPermission, DocumentPermission
from company.models import Company
from work.models import IssueProject
from docs.models import LetterSequence, Category, LawsuitCase, Document, Link, File, Image, OfficialLetter
from docs.utils import generate_official_letter_pdf
from ..pagination import PageNumberPaginationOneHundred, PageNumberPaginationThreeThousand
from ..serializers.docs import CategorySerializer, LawSuitCaseSerializer, \
    SimpleLawSuitCaseSerializer, DocumentSerializer, LinkSerializer, FileSerializer, ImageSerializer, \
    DocumentInTrashSerializer, OfficialLetterSerializer


# DocsItem --------------------------------------------------------------------------
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (permissions.IsAuthenticated, IsWorkManagerReadOnly)
    filterset_fields = ('doc_type', 'active')


class LawSuitCaseFilterSet(FilterSet):
    company = ModelChoiceFilter(field_name='issue_project__company',
                                queryset=Company.objects.all(), label='회사')
    is_real_dev = BooleanFilter(method='is_real_dev_proj', label='부동산개발 프로젝트')
    related_case = CharFilter(method='filter_related_case')
    in_progress = BooleanFilter(field_name='case_end_date', lookup_expr='isnull', label='진행중')

    class Meta:
        model = LawsuitCase
        fields = ('company', 'issue_project__project', 'is_real_dev', 'issue_project',
                  'related_case', 'sort', 'level', 'court', 'in_progress')

    @staticmethod
    def is_real_dev_proj(queryset, name, value):
        if value:
            return queryset.filter(issue_project__type='2')
        return queryset.exclude(issue_project__type='2')

    @staticmethod
    def filter_related_case(queryset, name, value):
        try:
            pk = int(value)
        except (ValueError, TypeError):
            return queryset.none()
        return queryset.filter(Q(pk=pk) | Q(related_case_id=pk))


class LawSuitCaseViewSet(viewsets.ModelViewSet):
    queryset = LawsuitCase.objects.select_related(
        'issue_project', 'related_case', 'creator', 'updator'
    ).prefetch_related(
        'document_set__category',
        'document_set__links',
        'document_set__files'
    )
    serializer_class = LawSuitCaseSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, ProjectPermission)
    pagination_class = PageNumberPaginationOneHundred
    filterset_class = LawSuitCaseFilterSet
    search_fields = ('other_agency', 'case_number', 'case_name', 'plaintiff',
                     'plaintiff_attorney', 'defendant', 'defendant_attorney',
                     'case_start_date', 'case_end_date', 'summary')

    @property
    def required_permission(self):
        # 소송 사건 등록/수정/삭제 권한은 일반 문서 권한(docs.create 등)과 동일하게 매핑
        mapping = {
            'list': 'docs.read',
            'retrieve': 'docs.read',
            'create': 'docs.create',
            'update': 'docs.update',
            'partial_update': 'docs.update',
            'destroy': 'docs.delete'
        }
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset
        # 사용자가 멤버로 속한 프로젝트의 소송 데이터만 반환
        accessible_projects = IssueProject.objects.filter(members__user=user)
        return queryset.filter(issue_project__in=accessible_projects)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)


class AllLawSuitCaseViewSet(viewsets.ReadOnlyModelViewSet):
    """문서 등록/수정 시 소송 선택 드롭다운 전용 ReadOnly 뷰셋"""
    queryset = LawsuitCase.objects.all()
    serializer_class = SimpleLawSuitCaseSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, ProjectPermission)
    pagination_class = PageNumberPaginationThreeThousand
    filterset_class = LawSuitCaseFilterSet

    @property
    def required_permission(self):
        return 'docs.read'

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset
        accessible_projects = IssueProject.objects.filter(members__user=user)
        return queryset.filter(issue_project__in=accessible_projects)


class DocumentFilterSet(FilterSet):
    company = ModelChoiceFilter(field_name='issue_project__company',
                                queryset=Company.objects.all(), label='회사')
    is_real_dev = BooleanFilter(method='is_real_dev_proj', label='부동산개발 프로젝트')

    class Meta:
        model = Document
        fields = ('company', 'is_real_dev', 'issue_project__project',
                  'issue_project', 'doc_type', 'category', 'lawsuit', 'creator')

    @staticmethod
    def is_real_dev_proj(queryset, name, value):
        if value:
            return queryset.filter(issue_project__type='2')
        return queryset.exclude(issue_project__type='2')


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related(
        'issue_project', 'category', 'lawsuit', 'creator', 'updator'
    ).prefetch_related('links', 'files', 'docscrape_set')
    serializer_class = DocumentSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, DocumentPermission)
    pagination_class = PageNumberPaginationOneHundred
    filterset_class = DocumentFilterSet
    search_fields = (
        'lawsuit__case_number', 'lawsuit__case_name', 'title',
        'description', 'links__link', 'files__file', 'creator__username')

    @property
    def required_permission(self):
        mapping = {
            'list': 'docs.read',
            'retrieve': 'docs.read',
            'hit': 'docs.read',
            'copy_and_create': 'docs.create',
            'create': 'docs.create',
            'update': 'docs.update',
            'partial_update': 'docs.update',
            'destroy': 'docs.delete'
        }
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset().exclude(issue_project__status='9')
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset

        accessible_projects = IssueProject.objects.filter(members__user=user)

        return queryset.filter(
            issue_project__in=accessible_projects
        ).filter(
            Q(is_secret=False) | Q(creator=user)
        ).filter(is_blind=False)

    @action(detail=True, methods=['post'], url_path='hit')
    def hit(self, request, *args, **kwargs):
        instance = self.get_object()
        Document.objects.filter(pk=instance.pk).update(hit=F('hit') + 1)
        instance.refresh_from_db(fields=['hit'])
        return Response({'hit': instance.hit}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='copy')
    def copy_and_create(self, request, *args, **kwargs):
        origin_pk = kwargs.get('pk')
        issue_project = request.data.get('issue_project') or request.data.get('project')
        doc_type = request.data.get('doc_type')

        if not issue_project:
            return Response(
                {'detail': 'issue_project는 필수입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            org_instance = Document.objects.select_related(
                'issue_project', 'category', 'lawsuit'
            ).get(pk=origin_pk)

            # (A) 기밀 문서 검증은 DocumentPermission 클래스에서 자동 통제됨
            copied_at = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M')
            add_text = (
                f'<br /><br /><p>'
                f'[이 게시물은 {request.user.username} 님에 의해 {copied_at} '
                f'{org_instance.issue_project.name} 에서 복사됨]'
                f'</p>'
            )

            new_instance_data = {
                'issue_project': issue_project,
                'doc_type': doc_type,
                'category': org_instance.category.pk if org_instance.category else None,
                'lawsuit': org_instance.lawsuit.pk if org_instance.lawsuit else None,
                'title': org_instance.title,
                'execution_date': org_instance.execution_date if org_instance.execution_date else None,
                'description': org_instance.description + add_text,
            }

            serializer = DocumentSerializer(data=new_instance_data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save(creator=request.user)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Document.DoesNotExist:
            return Response(
                {'detail': 'Original Document object does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        # (B) 기밀 문서 수정 검증은 DocumentPermission 클래스에서 자동 통제됨
        serializer.save(updator=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # (C) 기밀 문서 삭제 검증은 DocumentPermission 클래스에서 자동 통제됨
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LinkViewSet(viewsets.ModelViewSet):
    queryset = Link.objects.all()
    serializer_class = LinkSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, DocumentPermission)

    @property
    def required_permission(self):
        mapping = {
            'list': 'docs.read',
            'retrieve': 'docs.read',
            'create': 'docs.create',
            'update': 'docs.update',
            'partial_update': 'docs.update',
            'destroy': 'docs.delete'
        }
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset

        from work.models import IssueProject
        accessible_projects = IssueProject.objects.filter(members__user=user)

        return queryset.filter(
            docs__issue_project__in=accessible_projects
        ).filter(
            Q(docs__is_secret=False) | Q(docs__creator=user)
        ).filter(docs__is_blind=False)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)


class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, DocumentPermission)
    filterset_fields = ('docs',)
    search_fields = ('file_name', 'description')

    @property
    def required_permission(self):
        mapping = {
            'list': 'docs.read',
            'retrieve': 'docs.read',
            'create': 'docs.create',
            'update': 'docs.update',
            'partial_update': 'docs.update',
            'destroy': 'docs.delete'
        }
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset

        from work.models import IssueProject
        accessible_projects = IssueProject.objects.filter(members__user=user)

        return queryset.filter(
            docs__issue_project__in=accessible_projects
        ).filter(
            Q(docs__is_secret=False) | Q(docs__creator=user)
        ).filter(docs__is_blind=False)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly, DocumentPermission)

    @property
    def required_permission(self):
        mapping = {
            'list': 'docs.read',
            'retrieve': 'docs.read',
            'create': 'docs.create',
            'update': 'docs.update',
            'partial_update': 'docs.update',
            'destroy': 'docs.delete'
        }
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset

        from work.models import IssueProject
        accessible_projects = IssueProject.objects.filter(members__user=user)

        return queryset.filter(
            docs__issue_project__in=accessible_projects
        ).filter(
            Q(docs__is_secret=False) | Q(docs__creator=user)
        ).filter(docs__is_blind=False)


class DocsInTrashViewSet(DocumentViewSet):
    queryset = Document.all_objects.filter(deleted__isnull=False).select_related('category')
    serializer_class = DocumentInTrashSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset

        from work.models import IssueProject
        accessible_projects = IssueProject.objects.filter(members__user=user)

        return queryset.filter(
            issue_project__in=accessible_projects
        ).filter(
            Q(is_secret=False) | Q(creator=user)
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        is_admin = user.is_superuser or getattr(user, 'work_manager', False)

        if instance.is_secret and not is_admin and instance.creator != user:
            return Response(
                {'detail': 'You do not have permission to delete this secret document.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Official Letter --------------------------------------------------------------------------

class OfficialLetterFilterSet(FilterSet):
    company = ModelChoiceFilter(field_name='company',
                                queryset=Company.objects.all(), label='회사')
    issue_date_from = DateFilter(field_name='issue_date', lookup_expr='gte', label='발신일(시작)')
    issue_date_to = DateFilter(field_name='issue_date', lookup_expr='lte', label='발신일(종료)')

    class Meta:
        model = OfficialLetter
        fields = ('company', 'issue_date_from', 'issue_date_to', 'creator')


class OfficialLetterViewSet(viewsets.ModelViewSet):
    queryset = OfficialLetter.objects.select_related('company', 'creator', 'updator')
    serializer_class = OfficialLetterSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationOneHundred
    filterset_class = OfficialLetterFilterSet
    search_fields = ('document_number', 'title', 'recipient_name',
                     'sender_name', 'content')

    @property
    def required_permission(self):
        mapping = {
            'list': 'docs.read',
            'retrieve': 'docs.read',
            'create': 'docs.create',
            'update': 'docs.update',
            'partial_update': 'docs.update',
            'destroy': 'docs.delete',
            'generate_pdf': 'docs.create',
            'download_pdf': 'docs.read',
            'next_document_number': 'docs.read'
        }
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset
        if hasattr(user, 'staff') and user.staff.company:
            return queryset.filter(company=user.staff.company)
        return queryset.none()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)

    @action(detail=True, methods=['post'])
    def generate_pdf(self, request, pk=None):
        letter = self.get_object()
        try:
            pdf_file = generate_official_letter_pdf(letter)
        except Exception as e:
            logger.exception('PDF 생성 실패 (letter pk=%s): %s', letter.pk, e)
            return Response(
                {'error': 'PDF 생성에 실패했습니다.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        letter.pdf_file = pdf_file
        letter.save(update_fields=['pdf_file'])
        return Response({
            'status': 'success',
            'pdf_url': letter.pdf_file.url if letter.pdf_file else None
        })

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        letter = self.get_object()

        if not letter.pdf_file:
            return Response({'error': 'PDF가 생성되지 않았습니다.'},
                            status=status.HTTP_404_NOT_FOUND)

        return FileResponse(
            letter.pdf_file.open('rb'),
            as_attachment=True,
            filename=letter.get_pdf_filename()
        )

    @action(detail=False, methods=['get'])
    def next_document_number(self, request):
        company_id = request.query_params.get('company')
        if not company_id:
            return Response({'error': '회사 ID가 필요합니다.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            company = Company.objects.get(pk=company_id)
            current_year = timezone.now().year

            # select_for_update()로 동시 요청 시 Race Condition(중복 채번) 방지
            from django.db import transaction
            with transaction.atomic():
                sequence = LetterSequence.objects.select_for_update().filter(
                    company=company,
                    year=current_year
                ).first()
                next_seq = (sequence.last_sequence + 1) if sequence else 1

            next_number = f'{current_year}-{next_seq:03d}'
            return Response({'next_document_number': next_number})
        except Company.DoesNotExist:
            return Response({'error': '회사를 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)
