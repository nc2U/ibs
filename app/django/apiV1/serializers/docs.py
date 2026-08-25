import json
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from _utils.file_service import FileService
from apiV1.serializers.accounts import SimpleUserSerializer
from apiV1.serializers.work import SimpleIssueProjectSerializer
from docs.models import Category, LawsuitCase, Document, Link, File, Image, OfficialLetter

User = get_user_model()


# DocsItem --------------------------------------------------------------------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('pk', 'doc_type', 'color', 'name', 'parent', 'order', 'active', 'default')


class FilesInLawSuitCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('file',)


class LawSuitCaseSerializer(serializers.ModelSerializer):
    proj_name = serializers.SlugField(source='issue_project', read_only=True)
    proj_sort = serializers.SerializerMethodField(read_only=True)
    sort_desc = serializers.CharField(source='get_sort_display', read_only=True)
    level_desc = serializers.CharField(source='get_level_display', read_only=True)
    related_case_name = serializers.SlugField(source='related_case', read_only=True)
    court_desc = serializers.CharField(source='get_court_display', read_only=True)
    creator = SimpleUserSerializer(read_only=True)
    updator = SimpleUserSerializer(read_only=True)
    links = serializers.SerializerMethodField(read_only=True)
    files = serializers.SerializerMethodField(read_only=True)
    prev_pk = serializers.SerializerMethodField(read_only=True)
    next_pk = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LawsuitCase
        fields = ('pk', 'issue_project', 'proj_name', 'proj_sort', 'sort', 'sort_desc', 'level', 'level_desc',
                  'related_case', 'related_case_name', 'court', 'court_desc', 'other_agency', 'case_number',
                  'case_name', '__str__', 'plaintiff', 'plaintiff_attorney', 'plaintiff_case_price',
                  'defendant', 'defendant_attorney', 'defendant_case_price', 'related_debtor', 'case_start_date',
                  'case_end_date', 'summary', 'creator', 'updator', 'links', 'files', 'created', 'prev_pk', 'next_pk')
        read_only_fields = ('__str__',)

    @staticmethod
    def get_proj_sort(obj):
        return obj.issue_project.type if obj.issue_project else None

    @staticmethod
    def get_links(obj):
        """뷰셋의 prefetch_related 캐시를 재사용 (중복 쿼리 방지)"""
        links = []
        for doc in obj.document_set.all().order_by('id'):
            category_data = {
                'color': doc.category.color if doc.category else '',
                'name': doc.category.name if doc.category else ''
            }
            for link in doc.links.all():
                links.append({
                    'pk': link.id,
                    'category': {'name': category_data.get('name'),
                                 'color': category_data.get('color')},
                    'link': link.link})
        return links

    @staticmethod
    def get_files(obj):
        """뷰셋의 prefetch_related 캐시를 재사용 (중복 쿼리 방지)"""
        files = []
        for doc in obj.document_set.all().order_by('id'):
            category_data = {
                'color': doc.category.color if doc.category else '',
                'name': doc.category.name if doc.category else ''
            }
            for file in doc.files.all():
                files.append({
                    'pk': file.id,
                    'category': {'name': category_data.get('name'),
                                 'color': category_data.get('color')},
                    'file': file.file.url if file.file else ''})
        return files

    def get_prev_pk(self, obj):
        queryset = self.context['view'].filter_queryset(LawsuitCase.objects.all())
        prev_obj = queryset.filter(pk__lt=obj.pk).order_by('-case_start_date', '-pk').first()
        return prev_obj.pk if prev_obj else None

    def get_next_pk(self, obj):
        queryset = self.context['view'].filter_queryset(LawsuitCase.objects.all())
        next_obj = queryset.filter(pk__gt=obj.pk).order_by('case_start_date', 'pk').first()
        return next_obj.pk if next_obj else None


class SimpleLawSuitCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = LawsuitCase
        fields = ('pk', '__str__')


class LinksInDocumentSerializer(serializers.ModelSerializer):
    creator = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = Link
        fields = ('pk', 'docs', 'link', 'description', 'creator', 'hit', 'created')


class FilesInDocumentSerializer(serializers.ModelSerializer):
    creator = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = File
        fields = ('pk', 'docs', 'file_name', 'file', 'file_type',
                  'file_size', 'description', 'creator', 'hit', 'created')


def validate_link(value):
    parsed_url = urlparse(value)
    # 스키마(http, https)가 없으면 자동으로 'https://' 추가
    if not parsed_url.scheme:
        value = f"https://{value}"
    return value


class DocumentSerializer(serializers.ModelSerializer):
    project = SimpleIssueProjectSerializer(source='issue_project', read_only=True)
    proj_type = serializers.SerializerMethodField(read_only=True)
    type_name = serializers.SerializerMethodField()
    cate_name = serializers.SlugField(source='category', read_only=True)
    cate_color = serializers.SerializerMethodField(read_only=True)
    lawsuit_name = serializers.SlugField(source='lawsuit', read_only=True)
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True, default='')
    links = serializers.SerializerMethodField(read_only=True)
    files = serializers.SerializerMethodField(read_only=True)
    creator = SimpleUserSerializer(read_only=True)
    updator = SimpleUserSerializer(read_only=True)
    scrape = serializers.SerializerMethodField(read_only=True)
    my_scrape = serializers.SerializerMethodField(read_only=True)
    security_level_desc = serializers.CharField(source='get_security_level_display', read_only=True)
    creator_dept_name = serializers.SerializerMethodField(read_only=True)
    allowed_users = serializers.PrimaryKeyRelatedField(
        many=True, read_only=False,
        queryset=User.objects.all(),
        required=False,
    )
    prev_pk = serializers.SerializerMethodField(read_only=True)
    next_pk = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Document
        fields = ('pk', 'project', 'proj_type', 'doc_type', 'type_name',
                  'category', 'cate_name', 'cate_color', 'lawsuit', 'lawsuit_name', 'title',
                  'execution_date', 'description', 'hit', 'scrape', 'my_scrape', 'ip', 'device',
                  'is_pinned', 'security_level', 'security_level_desc', 'creator_dept_name', 'allowed_users',
                  'is_blind', 'deleted', 'links', 'files',
                  'creator', 'updator', 'created', 'updated', 'is_new', 'prev_pk', 'next_pk')
        read_only_fields = ('ip',)

    def _is_visible_to_user(self, obj) -> bool:
        """
        문서 열람 권한 판정 (메모리 캐싱 및 list 액션 최적화)
        """
        if hasattr(obj, '_is_visible_cached'):
            return obj._is_visible_cached

        request = self.context.get('request')
        if not request:
            obj._is_visible_cached = False
            return False

        user = request.user
        if not user or not user.is_authenticated:
            obj._is_visible_cached = False
            return False

        # 슈퍼유저 또는 work_manager는 항상 열람 가능
        if user.is_superuser or getattr(user, 'work_manager', False):
            obj._is_visible_cached = True
            return True

        if obj.is_blind:
            obj._is_visible_cached = False
            return False

        view = self.context.get('view')
        # list 액션은 get_queryset()에서 이미 접근 권한(security_level/allowed_users 등) 필터링을 거쳤으므로 True
        if view and view.action == 'list':
            obj._is_visible_cached = True
            return True

        obj._is_visible_cached = obj.is_visible_to(user)
        return obj._is_visible_cached

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # 블라인드/비공개 문서의 경우 제목과 본문을 마스킹
        if not self._is_visible_to_user(instance):
            if instance.is_blind:
                data['title'] = '[HIDDEN DOCUMENT]'
                data['description'] = '이 문서는 관리자에 의해 숨김처리 되었습니다.'
            else:
                data['description'] = '열람 권한이 없는 문서입니다.'
        return data

    @staticmethod
    def get_proj_type(obj):
        return obj.issue_project.type if obj.issue_project else None

    @staticmethod
    def get_type_name(obj):
        return obj.get_doc_type_display()

    @staticmethod
    def get_cate_color(obj):
        return obj.category.color if obj.category else None

    @staticmethod
    def get_creator_dept_name(obj):
        """작성자의 소속 부서명(주 부서 우선) 추출"""
        if not obj.creator_id:
            return None
        try:
            staff = getattr(obj.creator, 'staff', None)
            if staff:
                assignments = staff.assignments.all()
                primary = next((a for a in assignments if a.is_primary), None) or (assignments[0] if assignments else None)
                if primary and primary.department:
                    return primary.department.name
        except Exception:
            pass
        return None

    @staticmethod
    def get_scrape(obj):
        """prefetch_related 캐시를 사용하여 DB 쿼리 없이 개수 산출"""
        if hasattr(obj, '_prefetched_objects_cache') and 'docscrape_set' in obj._prefetched_objects_cache:
            return len(obj.docscrape_set.all())
        return obj.docscrape_set.count()

    def get_my_scrape(self, obj):
        """prefetch_related 캐시를 사용하여 DB 쿼리 없이 내 스크랩 여부 산출"""
        user = self.context.get('request') and self.context['request'].user
        if not user or not user.is_authenticated:
            return False
        if hasattr(obj, '_prefetched_objects_cache') and 'docscrape_set' in obj._prefetched_objects_cache:
            return any(s.user_id == user.pk for s in obj.docscrape_set.all())
        return obj.docscrape_set.filter(user=user).exists()

    def get_links(self, obj):
        if not self._is_visible_to_user(obj):
            return []
        return LinksInDocumentSerializer(obj.links.all(), many=True).data

    def get_files(self, obj):
        if not self._is_visible_to_user(obj):
            return []
        return FilesInDocumentSerializer(obj.files.all(), many=True).data

    def get_prev_pk(self, obj):
        view = self.context.get('view')
        if view and view.action != 'retrieve':
            return None
        queryset = view.filter_queryset(Document.objects.all())
        prev_obj = queryset.filter(pk__lt=obj.pk).order_by('-pk').first()
        return prev_obj.pk if prev_obj else None

    def get_next_pk(self, obj):
        view = self.context.get('view')
        if view and view.action != 'retrieve':
            return None
        queryset = view.filter_queryset(Document.objects.all())
        next_obj = queryset.filter(pk__gt=obj.pk).order_by('pk').first()
        return next_obj.pk if next_obj else None

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        issue_project = self.initial_data.get('issue_project')
        if issue_project and str(issue_project).isdigit():
            validated_data['issue_project_id'] = int(issue_project)

        validated_data['ip'] = request.META.get('REMOTE_ADDR')
        validated_data['device'] = request.META.get('HTTP_USER_AGENT')
        if user and user.is_authenticated:
            validated_data['creator'] = user

        docs = super().create(validated_data)

        # multipart/form-data 요청(QueryDict)인 경우에만 링크 처리
        if hasattr(self.initial_data, 'getlist'):
            new_links = self.initial_data.getlist('newLinks', [])
            for link in new_links:
                Link.objects.create(docs=docs, link=validate_link(link))

        FileService.manage_files(docs, request.data, user, File, related_name='docs')
        return docs

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get('request')
        user = request.user

        issue_project = self.initial_data.get('issue_project')
        if issue_project and str(issue_project).isdigit():
            validated_data['issue_project_id'] = int(issue_project)

        validated_data['ip'] = request.META.get('REMOTE_ADDR')
        validated_data['device'] = request.META.get('HTTP_USER_AGENT')

        if hasattr(request, 'user') and request.user:
            instance.updator = request.user

        instance = super().update(instance, validated_data)

        # multipart/form-data 요청(QueryDict)인 경우에만 링크/파일 처리
        if hasattr(self.initial_data, 'getlist'):
            # --- Links 처리 ---
            old_links = self.initial_data.getlist('links', [])
            for json_link in old_links:
                try:
                    link = json.loads(json_link)
                    link_object = Link.objects.get(pk=link.get('pk'))
                    if link.get('del'):
                        link_object.delete()
                    else:
                        link_object.link = validate_link(link.get('link'))
                        link_object.save()
                except (json.JSONDecodeError, Link.DoesNotExist):
                    continue

            new_links = self.initial_data.getlist('newLinks', [])
            for link in new_links:
                Link.objects.create(docs=instance, link=validate_link(link))

            FileService.manage_files(instance, request.data, user, File, related_name='docs')

        return instance


class LinkSerializer(serializers.ModelSerializer):
    creator = serializers.SlugField(read_only=True)

    class Meta:
        model = Link
        fields = ('pk', 'docs', 'link', 'description', 'hit', 'creator', 'created')
        read_only_fields = ('hit', 'created')


class FileSerializer(serializers.ModelSerializer):
    creator = serializers.SlugField(read_only=True)

    class Meta:
        model = File
        fields = ('pk', 'docs', 'file', 'file_name', 'file_type',
                  'file_size', 'description', 'hit', 'creator', 'created')
        read_only_fields = ('file_name', 'file_type', 'file_size', 'hit', 'created')


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('pk', 'docs', 'image', 'image_name', 'image_type', 'image_size', 'created')
        read_only_fields = ('image_name', 'image_type', 'image_size', 'created')


class DocumentInTrashSerializer(serializers.ModelSerializer):
    type_name = serializers.SerializerMethodField()
    cate_name = serializers.SlugField(source='category', read_only=True)
    creator = serializers.SlugField(read_only=True)

    class Meta:
        model = Document
        fields = ('pk', 'type_name', 'cate_name', 'title', 'description', 'creator', 'created', 'deleted')

    @staticmethod
    def get_type_name(obj):
        return obj.get_doc_type_display()

    def update(self, instance, validated_data):
        instance.restore()
        return instance


class OfficialLetterSerializer(serializers.ModelSerializer):
    company_name = serializers.SlugField(source='company', read_only=True)
    creator = SimpleUserSerializer(read_only=True)
    updator = SimpleUserSerializer(read_only=True)
    approval_document_detail = serializers.SerializerMethodField(read_only=True)
    approval_status_desc = serializers.CharField(source='get_approval_status_display', read_only=True)
    prev_pk = serializers.SerializerMethodField(read_only=True)
    next_pk = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OfficialLetter
        fields = ('pk', 'company', 'company_name', 'document_number', 'title',
                  'recipient_name', 'recipient_address', 'recipient_contact',
                  'recipient_reference', 'sender_name', 'sender_position',
                  'sender_department', 'content', 'issue_date', 'pdf_file',
                  'approval_document', 'approval_document_detail', 'approval_status', 'approval_status_desc',
                  'creator', 'updator', 'created', 'updated', 'prev_pk', 'next_pk')
        read_only_fields = ('document_number', 'pdf_file')

    def get_approval_document_detail(self, obj):
        if obj.approval_document:
            return {
                'pk': obj.approval_document.pk,
                'doc_number': obj.approval_document.doc_number,
                'title': obj.approval_document.title,
                'status': obj.approval_document.status,
                'status_desc': obj.approval_document.get_status_display(),
            }
        return None

    def get_prev_pk(self, obj):
        view = self.context.get('view')
        if view and view.action != 'retrieve':
            return None
        queryset = view.filter_queryset(OfficialLetter.objects.all())
        # 개선: pk 비교 기준 정렬을 pk 기준으로 통일 (순서 논리 오류 방지)
        prev_obj = queryset.filter(pk__lt=obj.pk).order_by('-pk').first()
        return prev_obj.pk if prev_obj else None

    def get_next_pk(self, obj):
        view = self.context.get('view')
        if view and view.action != 'retrieve':
            return None
        queryset = view.filter_queryset(OfficialLetter.objects.all())
        # 개선: pk 비교 기준 정렬을 pk 기준으로 통일 (순서 논리 오류 방지)
        next_obj = queryset.filter(pk__gt=obj.pk).order_by('pk').first()
        return next_obj.pk if next_obj else None


class SimpleOfficialLetterSerializer(serializers.ModelSerializer):
    """목록 조회용 간략 시리얼라이저"""
    creator = SimpleUserSerializer(read_only=True)
    approval_status_desc = serializers.CharField(source='get_approval_status_display', read_only=True)

    class Meta:
        model = OfficialLetter
        fields = ('pk', 'document_number', 'title', 'recipient_name',
                  'issue_date', 'pdf_file', 'approval_document', 'approval_status',
                  'approval_status_desc', 'creator', 'created')
