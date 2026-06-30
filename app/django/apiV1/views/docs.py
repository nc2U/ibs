from django.db.models import F, Q
from django.http import FileResponse
from django.utils import timezone
from django_filters import BooleanFilter, ModelChoiceFilter, CharFilter, DateFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from company.models import Company
from docs.models import LetterSequence, DocType, Category, LawsuitCase, Document, Link, File, Image, OfficialLetter
from docs.utils import generate_official_letter_pdf
from ..pagination import PageNumberPaginationOneHundred, PageNumberPaginationThreeThousand
from apiV1.permissions.auth_perms import permissions, IsProjectStaffOrReadOnly
from apiV1.permissions.work_perms import ProjectPermission
from ..serializers.docs import DocTypeSerializer, CategorySerializer, LawSuitCaseSerializer, \
    SimpleLawSuitCaseSerializer, DocumentSerializer, LinkSerializer, FileSerializer, ImageSerializer, \
    DocumentInTrashSerializer, OfficialLetterSerializer


# DocsItem --------------------------------------------------------------------------

class DocTypeViewSet(viewsets.ModelViewSet):
    queryset = DocType.objects.all()
    serializer_class = DocTypeSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
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
        if value:  # True 일 경우 값이 '2' 인 데이터만 반환
            return queryset.filter(issue_project__sort='2')
        return queryset.exclude(issue_project__sort='2')  # False 일 경우 '2'가 아닌 데이터만 반환

    @staticmethod
    def filter_related_case(queryset, name, value):
        # 수정: 타입 안전성 — int 변환 실패 시 빈 결과 반환, related_case_id 사용
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
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationOneHundred
    filterset_class = LawSuitCaseFilterSet
    search_fields = ('other_agency', 'case_number', 'case_name', 'plaintiff',
                     'plaintiff_attorney', 'defendant', 'defendant_attorney',
                     'case_start_date', 'case_end_date', 'summary')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)


class AllLawSuitCaseViewSet(LawSuitCaseViewSet):
    serializer_class = SimpleLawSuitCaseSerializer
    pagination_class = PageNumberPaginationThreeThousand


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
        if value:  # True 일 경우 값이 '2' 인 데이터만 반환
            return queryset.filter(issue_project__sort='2')
        return queryset.exclude(issue_project__sort='2')  # False 일 경우 '2'가 아닌 데이터만 반환


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related(
        'issue_project', 'doc_type', 'category', 'lawsuit', 'creator', 'updator'
    ).prefetch_related('links', 'files', 'docscrape_set')
    serializer_class = DocumentSerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
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
        queryset = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset
        # 읽기 권한이 있으면 비밀글 및 블라인드글도 목록에 노출되도록 함 (제목/내용 등 상세 노출은 Serializer에서 제한)
        return queryset

    @staticmethod
    def _is_owner_or_admin(user, instance) -> bool:
        """비밀글 접근 가드: 작성자 본인 또는 관리자인지 확인"""
        return (
                user.is_superuser or
                getattr(user, 'work_manager', False) or
                instance.creator == user
        )

    @action(detail=True, methods=['post'], url_path='hit')
    def hit(self, request, *args, **kwargs):
        """조회수 증가 전용 액션 - docs.read 권한만 필요"""
        instance = self.get_object()
        # 수정: F() 표현식으로 Race Condition 방지
        Document.objects.filter(pk=instance.pk).update(hit=F('hit') + 1)
        instance.refresh_from_db(fields=['hit'])
        return Response({'hit': instance.hit}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='copy')
    def copy_and_create(self, request, *args, **kwargs):
        """문서 복사 액션"""
        origin_pk = kwargs.get('pk')
        # 프론트엔드에서 전달받는 issue_project pk (project 키 하위 호환)
        issue_project = request.data.get('issue_project') or request.data.get('project')
        doc_type = request.data.get('doc_type')

        try:
            org_instance = Document.objects.select_related(
                'issue_project', 'category', 'lawsuit'
            ).get(pk=origin_pk)

            # 비밀글 복사 보안 가드: 작성자이거나 관리자일 때만 복사 허용
            if org_instance.is_secret and not self._is_owner_or_admin(request.user, org_instance):
                return Response(
                    {'detail': 'You do not have permission to copy this secret document.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # 수정: timezone-aware 현재 시간 사용 (datetime.now() 제거)
            copied_at = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M')
            add_text = (
                f'<br /><br /><p>'
                f'[이 게시물은 {request.user.username} 님에 의해 {copied_at} '
                f'{org_instance.issue_project.name} 에서 복사됨]'
                f'</p>'
            )

            new_instance_data = {
                # 수정: company 필드 제거(Document에 없음), issue_project 필드 사용
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
        # 수정: get_object() 이중 호출 제거 → serializer.instance 사용
        instance = serializer.instance
        # 비밀글 수정 보안 가드: 비밀글인 경우 작성자 본인이거나 관리자만 수정 가능
        if instance.is_secret and not self._is_owner_or_admin(self.request.user, instance):
            raise PermissionDenied("You do not have permission to update this secret document.")
        serializer.save(updator=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # 비밀글 삭제 보안 가드: 비밀글인 경우 작성자 본인이거나 관리자만 삭제 가능
        if instance.is_secret and not self._is_owner_or_admin(request.user, instance):
            return Response(
                {'detail': 'You do not have permission to delete this secret document.'},
                status=status.HTTP_403_FORBIDDEN
            )

        instance.soft_delete()
        return Response({'status': 'soft-deleted'}, status=status.HTTP_200_OK)


class LinkViewSet(viewsets.ModelViewSet):
    queryset = Link.objects.all()
    serializer_class = LinkSerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)

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
        # 수정: self.queryset 직접 참조 → super().get_queryset()
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset
        # is_secret: 작성자 본인 열람 가능 / is_blind: 관리자만 열람 가능
        return queryset.filter(
            Q(docs__is_secret=False) | Q(docs__creator=user)
        ).filter(docs__is_blind=False)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)


class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
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
        # 수정: self.queryset 직접 참조 → super().get_queryset()
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset
        # is_secret: 작성자 본인 열람 가능 / is_blind: 관리자만 열람 가능
        return queryset.filter(
            Q(docs__is_secret=False) | Q(docs__creator=user)
        ).filter(docs__is_blind=False)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)

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
        # 수정: self.queryset 직접 참조 → super().get_queryset()
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset
        # is_secret: 작성자 본인 열람 가능 / is_blind: 관리자만 열람 가능
        return queryset.filter(
            Q(docs__is_secret=False) | Q(docs__creator=user)
        ).filter(docs__is_blind=False)


class DocsInTrashViewSet(DocumentViewSet):
    queryset = Document.all_objects.filter(deleted__isnull=False).select_related('doc_type', 'category')
    serializer_class = DocumentInTrashSerializer

    def get_queryset(self):
        # 수정: self.queryset 직접 참조 → super().get_queryset() (클래스 queryset 기반 필터 적용)
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return queryset
        # is_secret: 작성자 본인 열람 가능
        return queryset.filter(
            Q(is_secret=False) | Q(creator=user)
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # 비밀글 완전 삭제 보안 가드: 비밀글인 경우 작성자 본인이거나 관리자만 완전 삭제 가능
        if instance.is_secret and not self._is_owner_or_admin(request.user, instance):
            return Response(
                {'detail': 'You do not have permission to delete this secret document.'},
                status=status.HTTP_403_FORBIDDEN
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
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
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
        if hasattr(user, 'staff_auth') and user.staff_auth.company:
            return queryset.filter(company=user.staff_auth.company)
        return queryset.none()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)

    @action(detail=True, methods=['post'])
    def generate_pdf(self, request, pk=None):
        """공문 PDF 생성"""
        letter = self.get_object()
        # 수정: 예외 처리 추가로 500 에러 노출 방지
        try:
            pdf_file = generate_official_letter_pdf(letter)
        except Exception as e:
            return Response(
                {'error': f'PDF 생성 실패: {e}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        letter.pdf_file = pdf_file
        # 수정: update_fields 지정으로 불필요한 전체 필드 갱신 방지
        letter.save(update_fields=['pdf_file'])
        return Response({
            'status': 'success',
            'pdf_url': letter.pdf_file.url if letter.pdf_file else None
        })

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """PDF 파일 다운로드"""
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
        """다음 문서번호 미리보기 (시퀀스를 증가시키지 않음)"""
        company_id = request.query_params.get('company')
        if not company_id:
            return Response({'error': '회사 ID가 필요합니다.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            company = Company.objects.get(pk=company_id)
            current_year = timezone.now().year

            sequence = LetterSequence.objects.filter(
                company=company,
                year=current_year
            ).first()

            next_seq = (sequence.last_sequence + 1) if sequence else 1
            next_number = f'{current_year}-{next_seq:03d}'

            return Response({'next_document_number': next_number})
        except Company.DoesNotExist:
            return Response({'error': '회사를 찾을 수 없습니다.'},
                            status=status.HTTP_404_NOT_FOUND)
