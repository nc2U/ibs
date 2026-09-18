import logging

from django.db.models import F, Q
from django.http import FileResponse
from django.utils import timezone
from django_filters import BooleanFilter, ModelChoiceFilter, CharFilter, DateFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response

logger = logging.getLogger(__name__)

from apiV1.permissions.auth_perms import permissions, IsProjectStaffOrReadOnly, IsWorkManagerReadOnly, IsStaffOrReadOnly
from apiV1.permissions.work_perms import ProjectPermission, DocumentPermission
from company.models import Company
from work.models import IssueProject
from docs.models import (LetterSequence, Category, LawsuitCase, Document, Link,
                         File, Image, OfficialLetter, OfficialLetterAttachment,
                         InboundSequence, InboundLetter, InboundLetterAttachment)
from docs.utils import generate_official_letter_pdf
from ..pagination import PageNumberPaginationOneHundred, PageNumberPaginationThreeThousand
from ..serializers.docs import (CategorySerializer, LawSuitCaseSerializer,
                                SimpleLawSuitCaseSerializer, DocumentSerializer, LinkSerializer,
                                FileSerializer, ImageSerializer, DocumentInTrashSerializer,
                                OfficialLetterSerializer, OfficialLetterAttachmentSerializer,
                                InboundLetterSerializer, SimpleInboundLetterSerializer,
                                InboundLetterAttachmentSerializer)


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
        # 사용자가 멤버로 속한 워크스페이스의 소송 데이터만 반환
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
    ).prefetch_related(
        'links__creator', 'files__creator', 'allowed_users', 'docscrape_set',
        'creator__staff__assignments__department'
    )
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

        from company.models import StaffAssignment
        # 작성자의 부서 기반 팀공개(2등급) 판단을 위한 사용자 소속 부서 ID 목록
        user_dept_ids = StaffAssignment.objects.filter(
            staff__user=user, department__isnull=False
        ).values_list('department_id', flat=True)

        accessible_projects = IssueProject.objects.filter(members__user=user)

        return queryset.filter(
            issue_project__in=accessible_projects
        ).filter(
            # 4등급(전사공개): 모든 인증 사용자 허용
            Q(security_level=Document.SECURITY_COMPANY)
            # 3등급(프로젝트공개): 해당 워크스페이스 멤버
            | Q(security_level=Document.SECURITY_PROJECT)
            # 2등급(팀공개): 작성자 소속 부서와 일치하는 구성원
            | (Q(security_level=Document.SECURITY_TEAM)
               & Q(creator__staff__assignments__department_id__in=user_dept_ids))
            # 1등급(비공개): 작성자 본인
            | Q(creator=user)
            # 명시적 허가자
            | Q(allowed_users=user)
        ).filter(is_blind=False).distinct()


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
        from company.models import StaffAssignment
        accessible_projects = IssueProject.objects.filter(members__user=user)
        user_dept_ids = StaffAssignment.objects.filter(
            staff__user=user, department__isnull=False
        ).values_list('department_id', flat=True)

        return queryset.filter(
            docs__issue_project__in=accessible_projects
        ).filter(
            Q(docs__security_level=Document.SECURITY_COMPANY)
            | Q(docs__security_level=Document.SECURITY_PROJECT)
            # LinkViewSet
            | (Q(docs__security_level=Document.SECURITY_TEAM)
               & Q(docs__creator__staff__assignments__department_id__in=user_dept_ids))
            | Q(docs__creator=user)
            | Q(docs__allowed_users=user)
        ).filter(docs__is_blind=False).distinct()

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
        from company.models import StaffAssignment
        accessible_projects = IssueProject.objects.filter(members__user=user)
        user_dept_ids = StaffAssignment.objects.filter(
            staff__user=user, department__isnull=False
        ).values_list('department_id', flat=True)

        return queryset.filter(
            docs__issue_project__in=accessible_projects
        ).filter(
            Q(docs__security_level=Document.SECURITY_COMPANY)
            | Q(docs__security_level=Document.SECURITY_PROJECT)
            | (Q(docs__security_level=Document.SECURITY_TEAM)
               & Q(docs__creator__staff__assignments__department_id__in=user_dept_ids))
            | Q(docs__creator=user)
            | Q(docs__allowed_users=user)
        ).filter(docs__is_blind=False).distinct()

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
        from company.models import StaffAssignment
        accessible_projects = IssueProject.objects.filter(members__user=user)
        user_dept_ids = StaffAssignment.objects.filter(
            staff__user=user, department__isnull=False
        ).values_list('department_id', flat=True)

        return queryset.filter(
            docs__issue_project__in=accessible_projects
        ).filter(
            Q(docs__security_level=Document.SECURITY_COMPANY)
            | Q(docs__security_level=Document.SECURITY_PROJECT)
            | (Q(docs__security_level=Document.SECURITY_TEAM)
               & Q(docs__creator__staff__assignments__department_id__in=user_dept_ids))
            | Q(docs__creator=user)
            | Q(docs__allowed_users=user)
        ).filter(docs__is_blind=False).distinct()


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
            Q(security_level=Document.SECURITY_COMPANY)
            | Q(security_level=Document.SECURITY_PROJECT)
            | Q(creator=user)
            | Q(allowed_users=user)
        ).distinct()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        is_admin = user.is_superuser or getattr(user, 'work_manager', False)

        if not is_admin and not instance.is_visible_to(user):
            return Response(
                {'detail': '이 문서를 삭제할 권한이 없습니다.'},
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
    approval_status = CharFilter(method='filter_approval_status', label='결재/발송 상태')

    def filter_approval_status(self, queryset, name, value):
        if not value:
            return queryset
        if value == 'dispatched':
            return queryset.filter(dispatched_at__isnull=False)
        return queryset.filter(approval_status=value)

    class Meta:
        model = OfficialLetter
        fields = ('company', 'issue_date_from', 'issue_date_to', 'creator',
                  'dispatch_method', 'approval_status')


class OfficialLetterViewSet(viewsets.ModelViewSet):
    queryset = OfficialLetter.objects.select_related(
        'company', 'seal', 'creator', 'updator', 'approval_document'
    ).prefetch_related('attachments')
    serializer_class = OfficialLetterSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationOneHundred
    filterset_class = OfficialLetterFilterSet
    search_fields = ('document_number', 'title', 'recipient_name',
                     'drafter_name', 'content', 'tracking_number')

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
            'upload_pdf': 'docs.create',
            'download_pdf': 'docs.read',
            'next_document_number': 'docs.read',
            'submit_approval': 'docs.create'
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
        letter = serializer.save(creator=self.request.user)
        if letter.dispatched_at and letter.parent_inbound_letter:
            parent = letter.parent_inbound_letter
            if parent.status != 'replied':
                parent.status = 'replied'
                parent.save(update_fields=['status'])

    def perform_update(self, serializer):
        letter = self.get_object()
        validated_data = serializer.validated_data

        # 발송 및 대장 관리 메타 필드 목록 (공문서 본문 내용이 아니며 사후 기록/수정 가능)
        dispatch_fields = {
            'dispatch_method', 'tracking_number', 'dispatched_at',
            'recipient_address', 'recipient_contact'
        }
        requested_fields = set(validated_data.keys())
        is_dispatch_meta_only = requested_fields and requested_fields.issubset(dispatch_fields)

        # 1. 발송 완료된 공문: 본문 서식 변경은 전면 금지, 관리 대장 정보(등기번호, 완료일시 등)만 수정 가능
        if letter.dispatched_at is not None and not is_dispatch_meta_only:
            raise ValidationError('이미 대외 발송이 완료된 공문서의 본문 내용은 수정할 수 없습니다.')

        # 2. 전자결재 진행 중인 공문은 결재 심의 중이므로 본문 수정 금지 (기안 회수 또는 반려 후 수정 가능)
        if letter.approval_status == 'pending' and not is_dispatch_meta_only:
            raise ValidationError('전자결재가 진행 중인 공문서는 수정할 수 없습니다. 기안을 회수하거나 반려된 후에 수정해 주세요.')

        # 3. 결재 최종 승인 완료된 공문: 본문 서식 수정은 관리자만 가능, 발송 대장 정보 수정은 일반 사용자(작성/관리자)도 허용
        is_manager = self.request.user.is_superuser or getattr(self.request.user, 'work_manager', False)
        if letter.approval_status == 'approved' and not is_manager and not is_dispatch_meta_only:
            raise PermissionDenied('최종 결재 승인된 공문서는 관리자만 수정할 수 있습니다.')

        # 4. 전자결재 이력이 있는 문서(approval_mode='approval' 또는 approval_document 연동)는 단독/직접 발송으로 변경 금지
        requested_mode = validated_data.get('approval_mode')
        if requested_mode == 'manual' and (letter.approval_document or letter.approval_mode == 'approval'):
            raise ValidationError('전자결재 문서로 등록된 공문은 단독/직접 발송 방식으로 변경할 수 없습니다.')

        updated_letter = serializer.save(updator=self.request.user)
        if updated_letter.dispatched_at and updated_letter.parent_inbound_letter:
            parent = updated_letter.parent_inbound_letter
            if parent.status != 'replied':
                parent.status = 'replied'
                parent.save(update_fields=['status'])

    def perform_destroy(self, instance):
        # 1. 발송 완료된 공문은 법적 증빙 문서로 삭제 전면 금지
        if instance.dispatched_at is not None:
            raise ValidationError('이미 대외 발송이 완료된 공문서는 법적 증빙 문서로 삭제할 수 없습니다.')

        # 2. 결재 승인 완료된 공문은 관리자만 삭제 가능
        is_manager = self.request.user.is_superuser or getattr(self.request.user, 'work_manager', False)
        if instance.approval_status == 'approved' and not is_manager:
            raise PermissionDenied('최종 결재 승인된 공문서는 관리자만 삭제할 수 있습니다.')

        instance.delete()

    @action(detail=True, methods=['post'])
    def generate_pdf(self, request, pk=None):
        letter = self.get_object()

        # 1. 발송 완료된 공문은 자료 유실/변조 방지를 위해 수퍼유저를 포함해 시스템 PDF 재생성을 무조건 전면 금지
        if letter.dispatched_at is not None:
            return Response(
                {'detail': '이미 대외 발송이 완료된 공문서는 자료 유실 및 변조 방지를 위해 PDF 재생성이 금지됩니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. 결재 승인 완료된 공문은 관리자(슈퍼유저/work_manager)만 재생성 가능
        is_manager = request.user.is_superuser or getattr(request.user, 'work_manager', False)
        if letter.approval_status == 'approved' and not is_manager:
            return Response(
                {'detail': '최종 결재 승인된 공문서는 관리자만 시스템 PDF를 재생성할 수 있습니다.'},
                status=status.HTTP_403_FORBIDDEN
            )

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

    @action(detail=True, methods=['post'])
    def upload_pdf(self, request, pk=None):
        """실물 날인 스캔본 등 완성된 PDF 파일을 직접 업로드하여 보관"""
        letter = self.get_object()

        # 발송 완료된 공문의 스캔 파일 교체는 관리자(슈퍼유저/work_manager)만 허용
        is_manager = request.user.is_superuser or getattr(request.user, 'work_manager', False)
        if letter.dispatched_at is not None and not is_manager:
            return Response(
                {'detail': '이미 발송 완료된 공문의 최종 스캔본 등록/교체는 관리자만 가능합니다.'},
                status=status.HTTP_403_FORBIDDEN
            )

        uploaded_file = request.FILES.get('pdf_file') or request.FILES.get('file')

        if not uploaded_file:
            return Response({'error': '업로드할 PDF 파일이 전달되지 않았습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        if not uploaded_file.name.lower().endswith('.pdf'):
            return Response({'error': 'PDF 파일 형식(.pdf)만 업로드할 수 있습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 기존 PDF 교체 저장
        letter.pdf_file = uploaded_file
        letter.save(update_fields=['pdf_file'])
        return Response({
            'status': 'success',
            'pdf_url': letter.pdf_file.url if letter.pdf_file else None
        })

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        letter = self.get_object()

        # PDF 파일이 없거나 스토리지에 실제 파일이 존재하지 않는 경우 자동 생성 시도
        need_generation = not letter.pdf_file
        if letter.pdf_file:
            try:
                if not letter.pdf_file.storage.exists(letter.pdf_file.name):
                    need_generation = True
            except Exception:
                need_generation = True

        if need_generation:
            try:
                pdf_file = generate_official_letter_pdf(letter)
                letter.pdf_file = pdf_file
                letter.save(update_fields=['pdf_file'])
            except Exception as e:
                logger.exception('공문 PDF 자동 생성 실패 (letter pk=%s): %s', letter.pk, e)
                return Response({'error': 'PDF 파일을 찾을 수 없으며 생성을 실패했습니다.'},
                                status=status.HTTP_404_NOT_FOUND)

        try:
            return FileResponse(
                letter.pdf_file.open('rb'),
                as_attachment=True,
                filename=letter.get_pdf_filename()
            )
        except Exception as e:
            logger.exception('공문 PDF 다운로드 실패 (letter pk=%s): %s', letter.pk, e)
            return Response({'error': 'PDF 파일을 읽을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def next_document_number(self, request):
        company_id = request.query_params.get('company')
        if not company_id:
            return Response({'error': '회사 ID가 필요합니다.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            if not hasattr(user, 'staff') or not user.staff.company_id or str(user.staff.company_id) != str(company_id):
                return Response({'error': '해당 회사의 공문 번호를 조회할 권한이 없습니다.'},
                                status=status.HTTP_403_FORBIDDEN)

        try:
            company = Company.objects.get(pk=company_id)
            next_number = LetterSequence.peek_next_document_number(company)
            return Response({'next_document_number': next_number})
        except Company.DoesNotExist:
            return Response({'error': '회사를 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def submit_approval(self, request, pk=None):
        """공문을 전자결재(ApprovalDocument)로 상신"""
        from approval.models import ApprovalDocument, DocumentType, ApprovalStep
        from company.models import StaffAssignment
        from approval.services.route_builder import build_dynamic_approval_route
        from approval.tasks import notify_approvers_task
        letter = self.get_object()

        if letter.dispatched_at:
            return Response({'detail': '이미 대외 발송이 완료된 공문은 전자결재를 상신할 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        if letter.approval_status == 'pending':
            return Response({'detail': '이미 결재가 진행 중인 공문입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        if letter.approval_status == 'approved':
            return Response({'detail': '이미 최종 승인된 공문입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # OFFICIAL_LETTER 양식의 DocumentType 조회 (없으면 첫번째 활성 유형)
        doc_type = DocumentType.objects.filter(form_template_key='OFFICIAL_LETTER', is_active=True).first()
        if not doc_type:
            doc_type = DocumentType.objects.filter(is_active=True).first()
        if not doc_type:
            return Response({'detail': '사용 가능한 전자결재 문서 유형이 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 기안자 보직 조회 (공문 발행 회사와 일치하는 보직 우선 탐색)
        assignment = StaffAssignment.objects.filter(
            staff__user=request.user, company=letter.company, is_primary=True
        ).first() or StaffAssignment.objects.filter(
            staff__user=request.user, company=letter.company
        ).first() or StaffAssignment.objects.filter(
            staff__user=request.user, is_primary=True
        ).first() or StaffAssignment.objects.filter(
            staff__user=request.user
        ).first()

        # ApprovalDocument 생성
        content_payload = {
            'receiver': letter.recipient_name,
            'refer_to': letter.recipient_reference,
            'drafter_name': letter.drafter_name,
            'send_due_date': str(letter.issue_date),
            'letter_subject': letter.title,
            'letter_body': letter.content,
            'official_letter_id': letter.pk,
            'body': f"[대외 공문 발송 품의]\n\n• 수신처: {letter.recipient_name}\n• 참조: {letter.recipient_reference or '-'}\n• 기안/담당: {letter.drafter_name}{f' ({letter.drafter_position})' if letter.drafter_position else ''}\n• 시행일자: {letter.issue_date}\n\n[공문 본문]\n{letter.content}",
        }

        doc = ApprovalDocument(
            title=f'[공문 발송 품의] {letter.title}',
            doc_type=doc_type,
            drafter=request.user,
            drafter_assignment=assignment,
            content=content_payload,
            status=ApprovalDocument.STATUS_PENDING,
            current_step=1,
            submitted_at=timezone.now(),
        )
        doc.content_hash = doc.compute_hash()
        doc.save()

        # 동적 결재선 빌드 및 저장 (공문 인장에 지정된 전결 기준 자동 연동)
        steps = build_dynamic_approval_route(
            doc_type=doc_type,
            drafter_user=request.user,
            drafter_assignment=assignment,
            content=content_payload,
            seal=letter.seal,
        )

        is_instant_approval = letter.is_solo_approval or not steps

        if is_instant_approval:
            # 승인(전결)권자 직접 기안인 경우: 1개의 승인된 Step 생성 후 즉시 최종 승인 처리
            role_label = '승인권자 승인'
            if letter.seal and letter.seal.final_approval_duty:
                role_label = f'{letter.seal.final_approval_duty.name} 승인'
            elif assignment and assignment.duty:
                role_label = f'{assignment.duty.name} 승인'

            step = ApprovalStep.objects.create(
                document=doc,
                step_order=1,
                role_label=role_label,
                condition='OR',
                status=ApprovalStep.STATUS_APPROVED,
            )
            step.approvers.set([request.user])

            doc.status = ApprovalDocument.STATUS_APPROVED
            doc.completed_at = timezone.now()
            doc.content_hash = doc.compute_hash()
            doc.doc_number = doc.generate_doc_number()
            doc.save(update_fields=['status', 'completed_at', 'content_hash', 'doc_number'])

            # 공문 상태 최종 승인 동기화
            letter.approval_document = doc
            letter.approval_status = 'approved'
            letter.save(update_fields=['approval_document', 'approval_status'])

            # 공문서 PDF 자동 생성
            try:
                pdf_file = generate_official_letter_pdf(letter)
                letter.pdf_file = pdf_file
                letter.save(update_fields=['pdf_file'])
            except Exception as e:
                logger.warning('공문 PDF 자동 생성 실패 (letter pk=%s): %s', letter.pk, e)

            # 전자결재 품의서 PDF 생성 비동기 태스크
            from approval.tasks import generate_approval_pdf_task
            generate_approval_pdf_task.delay(doc.pk)

            return Response({
                'detail': '승인(전결)권자 직접 기안으로 전자결재가 즉시 최종 승인 처리되었습니다.',
                'approval_document_id': doc.pk,
                'approval_status': letter.approval_status,
            })

        for step_data in steps:
            step = ApprovalStep.objects.create(
                document=doc,
                step_order=step_data['step_order'],
                role_label=step_data['role_label'],
                condition=step_data.get('condition', 'AND'),
                status='pending',
            )
            step.approvers.set(step_data['approvers'])

        # 공문과 결재문서 상호 연결
        letter.approval_document = doc
        letter.approval_status = 'pending'
        letter.save(update_fields=['approval_document', 'approval_status'])

        # 1차 결재자 알림 발송
        first_step = doc.steps.filter(step_order=1).first()
        if first_step:
            try:
                notify_approvers_task.delay(doc.pk, first_step.pk)
            except Exception:
                notify_approvers_task(doc.pk, first_step.pk)

        return Response({
            'detail': '전자결재가 성공적으로 상신되었습니다.',
            'approval_document_id': doc.pk,
            'approval_status': letter.approval_status,
        })


class OfficialLetterAttachmentViewSet(viewsets.ModelViewSet):
    queryset = OfficialLetterAttachment.objects.all()
    serializer_class = OfficialLetterAttachmentSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filterset_fields = ('letter',)

    @property
    def required_permission(self):
        mapping = {
            'list': 'docs.read',
            'retrieve': 'docs.read',
            'create': 'docs.create',
            'update': 'docs.update',
            'partial_update': 'docs.update',
            'destroy': 'docs.delete',
        }
        return mapping.get(self.action, None)


# Inbound Letter ViewSets ------------------------------------------------------------------

class InboundLetterFilterSet(FilterSet):
    company = ModelChoiceFilter(field_name='company',
                                queryset=Company.objects.all(), label='회사')
    received_date_from = DateFilter(field_name='received_date', lookup_expr='gte', label='접수일(시작)')
    received_date_to = DateFilter(field_name='received_date', lookup_expr='lte', label='접수일(종료)')
    reply_due_date_from = DateFilter(field_name='reply_due_date', lookup_expr='gte', label='회신기한(시작)')
    reply_due_date_to = DateFilter(field_name='reply_due_date', lookup_expr='lte', label='회신기한(종료)')
    status = CharFilter(field_name='status', label='처리 상태')
    recipient_dept = CharFilter(field_name='recipient_dept', label='배부 부서')
    recipient_manager = CharFilter(field_name='recipient_manager', label='담당자')

    class Meta:
        model = InboundLetter
        fields = ('company', 'received_date_from', 'received_date_to',
                  'reply_due_date_from', 'reply_due_date_to',
                  'status', 'recipient_dept', 'recipient_manager')


class InboundLetterViewSet(viewsets.ModelViewSet):
    queryset = InboundLetter.objects.select_related(
        'company', 'recipient_dept', 'recipient_manager', 'creator', 'updator', 'approval_document'
    ).prefetch_related('attachments', 'reply_letters')
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationOneHundred
    filterset_class = InboundLetterFilterSet
    search_fields = ('receipt_number', 'document_number', 'sender_name',
                     'sender_contact', 'title', 'content')

    def get_serializer_class(self):
        if self.action == 'list':
            return SimpleInboundLetterSerializer
        return InboundLetterSerializer

    @property
    def required_permission(self):
        mapping = {
            'list': 'docs.read',
            'retrieve': 'docs.read',
            'create': 'docs.create',
            'update': 'docs.update',
            'partial_update': 'docs.update',
            'destroy': 'docs.delete',
            'next_receipt_number': 'docs.read',
            'submit_approval': 'docs.update',
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

    @action(detail=False, methods=['get'])
    def next_receipt_number(self, request):
        company_id = request.query_params.get('company')
        if not company_id:
            return Response({'error': '회사 ID가 필요합니다.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            if not hasattr(user, 'staff') or not user.staff.company_id or str(user.staff.company_id) != str(company_id):
                return Response({'error': '해당 회사의 접수 번호를 조회할 권한이 없습니다.'},
                                status=status.HTTP_403_FORBIDDEN)

        try:
            company = Company.objects.get(pk=company_id)
            next_number = InboundSequence.peek_next_receipt_number(company)
            return Response({'next_receipt_number': next_number})
        except Company.DoesNotExist:
            return Response({'error': '회사를 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def submit_approval(self, request, pk=None):
        """수신 공문을 전자결재(ApprovalDocument)로 상신"""
        from approval.models import ApprovalDocument, DocumentType, ApprovalStep, ApprovalAttachment
        from company.models import StaffAssignment
        from approval.services.route_builder import build_dynamic_approval_route
        from approval.tasks import notify_approvers_task, generate_approval_pdf_task
        from approval.services.document_service import archive_to_docs
        from work.models import IssueProject

        letter = self.get_object()

        if letter.status == 'closed':
            return Response({'detail': '이미 종결 처리된 수신 공문은 전자결재를 상신할 수 없습니다.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if letter.approval_document and letter.approval_document.status in (
            ApprovalDocument.STATUS_PENDING, ApprovalDocument.STATUS_APPROVED
        ):
            return Response({'detail': '이미 전자결재가 진행 중이거나 최종 승인되었습니다.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # INBOUND_REPORT 양식의 DocumentType 조회 (없으면 첫번째 활성 유형)
        doc_type = DocumentType.objects.filter(form_template_key='INBOUND_REPORT', is_active=True).first()
        if not doc_type:
            doc_type = DocumentType.objects.filter(is_active=True).first()
        if not doc_type:
            return Response({'detail': '사용 가능한 전자결재 문서 유형이 없습니다.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # 기안자 보직 조회
        assignment = StaffAssignment.objects.filter(staff__user=request.user, is_primary=True).first()
        if not assignment:
            assignment = StaffAssignment.objects.filter(staff__user=request.user).first()

        content_payload = {
            'inbound_letter_id': letter.pk,
            'sender_name': letter.sender_name,
            'sender_contact': letter.sender_contact or '',
            'receipt_number': letter.receipt_number,
            'document_number': letter.document_number or '',
            'received_date': str(letter.received_date),
            'reply_due_date': str(letter.reply_due_date) if letter.reply_due_date else '',
            'letter_subject': letter.title,
            'letter_content': letter.content or '',
            'body': f"[수신 공문 처리 보고 및 대응 품의]\n\n• 발신처: {letter.sender_name}\n• 발신 문서번호: {letter.document_number or '-'}\n• 접수번호: {letter.receipt_number}\n• 접수일자: {letter.received_date}\n• 회신기한: {letter.reply_due_date or '기한 없음'}\n\n[수신 내용]\n{letter.content or '-'}",
        }

        workspace = None
        if letter.company:
            workspace = IssueProject.objects.filter(company=letter.company, type='1').first() or IssueProject.objects.filter(company=letter.company).first()

        doc = ApprovalDocument(
            title=f'[수신 공문 보고] {letter.title}',
            doc_type=doc_type,
            drafter=request.user,
            drafter_assignment=assignment,
            workspace=workspace,
            related_inbound_letter=letter,
            content=content_payload,
            status=ApprovalDocument.STATUS_PENDING,
            current_step=1,
            submitted_at=timezone.now(),
        )
        doc.content_hash = doc.compute_hash()
        doc.save()

        # 스캔본 및 첨부파일을 결재 문서 첨부파일로 복사
        if letter.scan_file:
            ApprovalAttachment.objects.create(
                document=doc,
                file=letter.scan_file,
                file_name=letter.scan_file.name.split('/')[-1],
                creator=request.user,
            )
        for att in letter.attachments.all():
            if att.file:
                ApprovalAttachment.objects.create(
                    document=doc,
                    file=att.file,
                    file_name=att.file_name or att.file.name.split('/')[-1],
                    file_size=att.file_size,
                    creator=request.user,
                )

        steps = build_dynamic_approval_route(
            doc_type=doc_type,
            drafter_user=request.user,
            drafter_assignment=assignment,
            content=content_payload,
        )

        is_ceo = False
        company = assignment.company if assignment else letter.company
        if company:
            from apiV1.views.approval import _get_company_ceos
            ceo_users = _get_company_ceos(company, set())
            is_ceo = request.user in ceo_users or any(u.id == request.user.id for u in ceo_users)
        if not is_ceo and assignment and assignment.duty and (assignment.duty.code == 'CEO' or '대표' in assignment.duty.name):
            is_ceo = True

        effective_final_duty = doc_type.final_approval_duty
        drafter_duty = assignment.duty if assignment and assignment.duty else None
        is_final_authority = False
        if effective_final_duty and drafter_duty and drafter_duty.id == effective_final_duty.id:
            is_final_authority = True

        is_instant_approval = (is_ceo or is_final_authority or not steps)

        if is_instant_approval:
            role_label = '대표이사 승인' if is_ceo else (f'{drafter_duty.name} 승인' if drafter_duty else '전결권자 승인')
            step = ApprovalStep.objects.create(
                document=doc,
                step_order=1,
                role_label=role_label,
                condition='OR',
                status=ApprovalStep.STATUS_APPROVED,
            )
            step.approvers.set([request.user])

            doc.status = ApprovalDocument.STATUS_APPROVED
            doc.completed_at = timezone.now()
            doc.content_hash = doc.compute_hash()
            doc.doc_number = doc.generate_doc_number()
            doc.save(update_fields=['status', 'completed_at', 'content_hash', 'doc_number'])

            letter.approval_document = doc
            letter.status = 'in_progress'
            letter.save(update_fields=['approval_document', 'status'])

            archive_to_docs(doc)
            generate_approval_pdf_task.delay(doc.pk)

            return Response({
                'detail': '승인(전결)권자 직접 기안으로 전자결재가 즉시 최종 승인 처리되었습니다.',
                'approval_document_id': doc.pk,
                'status': letter.status,
            })

        for step_data in steps:
            step = ApprovalStep.objects.create(
                document=doc,
                step_order=step_data['step_order'],
                role_label=step_data['role_label'],
                condition=step_data.get('condition', 'AND'),
                status='pending',
            )
            step.approvers.set(step_data['approvers'])

        letter.approval_document = doc
        letter.status = 'in_progress'
        letter.save(update_fields=['approval_document', 'status'])

        first_step = doc.steps.filter(step_order=1).first()
        if first_step:
            try:
                notify_approvers_task.delay(doc.pk, first_step.pk)
            except Exception:
                notify_approvers_task(doc.pk, first_step.pk)

        return Response({
            'detail': '수신 공문 처리 보고가 전자결재로 성공적으로 상신되었습니다.',
            'approval_document_id': doc.pk,
            'status': letter.status,
        })


class InboundLetterAttachmentViewSet(viewsets.ModelViewSet):
    queryset = InboundLetterAttachment.objects.all()
    serializer_class = InboundLetterAttachmentSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filterset_fields = ('letter',)

    @property
    def required_permission(self):
        mapping = {
            'list': 'docs.read',
            'retrieve': 'docs.read',
            'create': 'docs.create',
            'update': 'docs.update',
            'partial_update': 'docs.update',
            'destroy': 'docs.delete',
        }
        return mapping.get(self.action, None)


