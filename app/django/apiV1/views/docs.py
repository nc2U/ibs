from datetime import datetime

from django.db.models import Q
from django.http import FileResponse
from django.utils import timezone
from django_filters import BooleanFilter, ModelChoiceFilter, NumberFilter, CharFilter, DateFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from company.models import Company
from project.models import Project
from docs.models import LetterSequence
from ..pagination import PageNumberPaginationOneHundred, PageNumberPaginationThreeThousand
from ..permission import *
from ..serializers.docs import *


# Docs --------------------------------------------------------------------------

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
        return queryset.filter(Q(pk=value) | Q(related_case=value))


class LawSuitCaseViewSet(viewsets.ModelViewSet):
    queryset = LawsuitCase.objects.all()
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
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationOneHundred
    filterset_class = DocumentFilterSet
    search_fields = (
        'lawsuit__case_number', 'lawsuit__case_name', 'title',
        'content', 'links__link', 'files__file', 'creator__username')

    def copy_and_create(self, request, *args, **kwargs):
        # 복사할 행의 ID를 저장한다.
        origin_pk = kwargs.get('pk')
        project = request.data.get('project')
        doc_type = request.data.get('doc_type')

        try:
            # 기존 행을 가져와서 복사한다.
            org_instance = Document.objects.get(pk=origin_pk)

            add_text = f'<br /><br /><p>[이 게시물은 {self.request.user.username} 님에 의해 {datetime.now()} {org_instance.board.name} 에서 복사됨]</p>'

            # 기존 행의 정보를 사용하여 새로운 행을 생성한다.
            new_instance_data = {
                'company': org_instance.company.pk,
                'project': project if project else None,
                'doc_type': doc_type,
                'category': org_instance.category.pk if org_instance.category else None,
                'lawsuit': org_instance.lawsuit.pk if org_instance.lawsuit else None,
                'title': org_instance.title,
                'execution_date': org_instance.execution_date if org_instance.execution_date else None,
                'content': org_instance.content + add_text,
            }

            # Serializer를 사용해 새로운 행을 생성하고 저장한다.
            serializer = DocumentSerializer(data=new_instance_data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Document.DoesNotExist:
            return Response({'detail': 'Original Document object does not exist'}, status=status.HTTP_404_NOT_FOUND)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        instance.soft_delete()
        return Response({'status': 'soft-deleted'}, status=status.HTTP_200_OK)


class LinkViewSet(viewsets.ModelViewSet):
    queryset = Link.objects.all()
    serializer_class = LinkSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)


class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('docs',)
    search_fields = ('file_name', 'description')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)


class DocsInTrashViewSet(DocumentViewSet):
    queryset = Document.all_objects.filter(deleted__isnull=False)
    serializer_class = DocumentInTrashSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

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
    queryset = OfficialLetter.objects.all()
    serializer_class = OfficialLetterSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationOneHundred
    filterset_class = OfficialLetterFilterSet
    search_fields = ('document_number', 'title', 'recipient_name',
                     'sender_name', 'content')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updator=self.request.user)

    @action(detail=True, methods=['post'])
    def generate_pdf(self, request, pk=None):
        """공문 PDF 생성"""
        from docs.utils import generate_official_letter_pdf

        letter = self.get_object()
        pdf_file = generate_official_letter_pdf(letter)
        letter.pdf_file = pdf_file
        letter.save()

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
        """다음 문서번호 미리보기"""
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
