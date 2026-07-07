import json
from urllib.parse import urlparse

from django.conf import settings
from django.db import transaction
from rest_framework import serializers

from _utils.file_service import FileService
from apiV1.serializers.accounts import SimpleUserSerializer
from docs.models import Category, LawsuitCase, Document, Link, File, Image, OfficialLetter


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
        return obj.issue_project.sort if obj.issue_project else None

    @staticmethod
    def get_links(obj):
        links = []
        documents = obj.document_set.all().select_related('category').prefetch_related('links').order_by('id')
        for doc in documents:
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
        files = []
        documents = obj.document_set.all().select_related('category').prefetch_related('files').order_by('id')
        for doc in documents:
            category_data = {
                'color': doc.category.color if doc.category else '',
                'name': doc.category.name if doc.category else ''
            }
            for file in doc.files.all():
                files.append({
                    'pk': file.id,
                    'category': {'name': category_data.get('name'),
                                 'color': category_data.get('color')},
                    'file': settings.MEDIA_URL + file.file.name if file.file else ''})
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
    creator = serializers.SlugField(read_only=True)

    class Meta:
        model = Link
        fields = ('pk', 'docs', 'link', 'description', 'creator', 'hit', 'created')


class FilesInDocumentSerializer(serializers.ModelSerializer):
    creator = serializers.SlugField(read_only=True)

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
    proj_name = serializers.SlugField(source='issue_project', read_only=True)
    proj_sort = serializers.SerializerMethodField(read_only=True)
    type_name = serializers.SerializerMethodField()
    cate_name = serializers.SlugField(source='category', read_only=True)
    cate_color = serializers.SerializerMethodField(read_only=True)
    lawsuit_name = serializers.SlugField(source='lawsuit', read_only=True)
    title = serializers.SerializerMethodField()
    links = serializers.SerializerMethodField(read_only=True)
    files = serializers.SerializerMethodField(read_only=True)
    description = serializers.SerializerMethodField()
    creator = SimpleUserSerializer(read_only=True)
    updator = SimpleUserSerializer(read_only=True)
    scrape = serializers.SerializerMethodField(read_only=True)
    my_scrape = serializers.SerializerMethodField(read_only=True)
    prev_pk = serializers.SerializerMethodField(read_only=True)
    next_pk = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Document
        fields = ('pk', 'issue_project', 'proj_name', 'proj_sort', 'doc_type', 'type_name',
                  'category', 'cate_name', 'cate_color', 'lawsuit', 'lawsuit_name', 'title',
                  'execution_date', 'description', 'hit', 'scrape', 'my_scrape', 'ip', 'device',
                  'is_pinned', 'is_secret', 'password', 'is_blind', 'deleted', 'links', 'files',
                  'creator', 'updator', 'created', 'updated', 'is_new', 'prev_pk', 'next_pk')
        read_only_fields = ('ip',)
        extra_kwargs = {'password': {'write_only': True}}

    def _is_visible_to_user(self, obj) -> bool:
        """비밀글 및 블라인드글 노출 제어 헬퍼"""
        request = self.context.get('request')
        if not request:
            return False
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # 1. 블라인드글인 경우 관리자(workManager)만 노출
        if obj.is_blind:
            return user.is_superuser or getattr(user, 'work_manager', False)
        # 2. 비밀글인 경우 관리자(workManager) 또는 작성자 본인만 노출
        if obj.is_secret:
            return user.is_superuser or getattr(user, 'work_manager', False) or obj.creator == user
        # 3. 일반 글인 경우 모든 유저 노출
        return True

    @staticmethod
    def get_proj_sort(obj):
        return obj.issue_project.sort if obj.issue_project else None

    @staticmethod
    def get_type_name(obj):
        return obj.doc_type.__str__()

    @staticmethod
    def get_cate_color(obj):
        return obj.category.color if obj.category else None

    @staticmethod
    def get_scrape(obj):
        return obj.docscrape_set.count()

    def get_my_scrape(self, obj):
        user = self.context['request'].user
        if not user or not user.is_authenticated:
            return False
        return obj.docscrape_set.filter(user=user).exists()

    def get_title(self, obj):
        user = self.context['request'].user
        # 블라인드글이고 관리자가 아닌 경우 제목을 마스킹 처리
        if obj.is_blind and not (user.is_superuser or getattr(user, 'work_manager', False)):
            return "[HIDDEN DOCUMENT]"
        return obj.title

    def get_description(self, obj):
        if not self._is_visible_to_user(obj):
            if obj.is_blind:
                return "이 문서는 관리자에 의해 숨김처리 되었습니다."
            return "비밀 문서입니다."
        return obj.description

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

        # title과 description은 SerializerMethodField라서 validated_data에서 제외되므로 직접 바인딩
        if 'title' in self.initial_data:
            validated_data['title'] = self.initial_data.get('title')
        if 'description' in self.initial_data:
            validated_data['description'] = self.initial_data.get('description')

        validated_data['ip'] = request.META.get('REMOTE_ADDR')
        validated_data['device'] = request.META.get('HTTP_USER_AGENT')
        if user and user.is_authenticated:
            validated_data['creator'] = user  # creator 안전 바인딩

        docs = super().create(validated_data)  # 기본 create 처리 (save 포함)

        new_links = self.initial_data.getlist('newLinks', [])  # Links 처리
        if new_links:
            for link in new_links:
                Link.objects.create(docs=docs, link=validate_link(link))

        # 파일 처리를 FileService로 위임
        FileService.manage_files(docs, request.data, user, File, related_name='docs')
        return docs

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get('request')
        user = request.user

        # title과 description은 SerializerMethodField라서 validated_data에서 제외되므로 직접 바인딩
        if 'title' in self.initial_data:
            validated_data['title'] = self.initial_data.get('title')
        if 'description' in self.initial_data:
            validated_data['description'] = self.initial_data.get('description')

        validated_data['ip'] = request.META.get('REMOTE_ADDR')
        validated_data['device'] = request.META.get('HTTP_USER_AGENT')

        if hasattr(request, 'user') and request.user:
            instance.updator = request.user

        instance = super().update(instance, validated_data)  # 기본 필드 업데이트 수행

        try:
            # --- Links 처리 ---
            old_links = self.initial_data.getlist('links', [])
            if old_links:
                for json_link in old_links:
                    link = json.loads(json_link)
                    link_object = Link.objects.get(pk=link.get('pk'))
                    if link.get('del'):
                        link_object.delete()
                    else:
                        link_object.link = validate_link(link.get('link'))
                        link_object.save()

            new_links = self.initial_data.getlist('newLinks', [])
            if new_links:
                for link in new_links:
                    Link.objects.create(docs=instance, link=validate_link(link))

            # 파일 처리를 FileService로 위임
            FileService.manage_files(instance, request.data, user, File, related_name='docs')
        except AttributeError:
            pass

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
        readonly_fields = ('image_name', 'image_type', 'image_size', 'created')


class DocumentInTrashSerializer(serializers.ModelSerializer):
    type_name = serializers.SerializerMethodField()
    cate_name = serializers.SlugField(source='category', read_only=True)
    creator = serializers.SlugField(read_only=True)

    class Meta:
        model = Document
        fields = ('pk', 'type_name', 'cate_name', 'title', 'description', 'creator', 'created', 'deleted')

    @staticmethod
    def get_type_name(obj):
        return obj.doc_type.get_type_display()

    def update(self, instance, validated_data):
        instance.restore()
        return instance


class OfficialLetterSerializer(serializers.ModelSerializer):
    company_name = serializers.SlugField(source='company', read_only=True)
    creator = SimpleUserSerializer(read_only=True)
    updator = SimpleUserSerializer(read_only=True)
    prev_pk = serializers.SerializerMethodField(read_only=True)
    next_pk = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OfficialLetter
        fields = ('pk', 'company', 'company_name', 'document_number', 'title',
                  'recipient_name', 'recipient_address', 'recipient_contact',
                  'recipient_reference', 'sender_name', 'sender_position',
                  'sender_department', 'content', 'issue_date', 'pdf_file',
                  'creator', 'updator', 'created', 'updated', 'prev_pk', 'next_pk')
        read_only_fields = ('document_number', 'pdf_file')

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

    class Meta:
        model = OfficialLetter
        fields = ('pk', 'document_number', 'title', 'recipient_name',
                  'issue_date', 'pdf_file', 'creator', 'created')
