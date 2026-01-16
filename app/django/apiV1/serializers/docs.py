import json
import os
from urllib.parse import urlparse

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from docs.models import DocType, Category, LawsuitCase, Document, Link, File, Image, OfficialLetter


# Docs --------------------------------------------------------------------------
class DocTypeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = DocType
        fields = ('pk', 'type', 'name')

    @staticmethod
    def get_name(obj):
        return obj.get_type_display()


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
        documents = obj.document_set.all().order_by('id')
        for doc in documents:
            category = Category.objects.get(pk=doc.category.id)
            category_data = {'color': category.color, 'name': category.name}
            for link in doc.links.values():
                links.append({
                    'pk': link.get('id'),
                    'category': {'name': category_data.get('name'),
                                 'color': category_data.get('color')},
                    'link': link.get('link')})
        return links

    @staticmethod
    def get_files(obj):
        files = []
        documents = obj.document_set.all().order_by('id')
        for doc in documents:
            category = Category.objects.get(pk=doc.category.id)
            category_data = {'color': category.color, 'name': category.name}
            for file in doc.files.values():
                files.append({
                    'pk': file.get('id'),
                    'category': {'name': category_data.get('name'),
                                 'color': category_data.get('color')},
                    'file': settings.MEDIA_URL + file.get('file')})
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
    links = LinksInDocumentSerializer(many=True, read_only=True)
    files = FilesInDocumentSerializer(many=True, read_only=True)
    creator = SimpleUserSerializer(read_only=True)
    updator = SimpleUserSerializer(read_only=True)
    scrape = serializers.SerializerMethodField(read_only=True)
    my_scrape = serializers.SerializerMethodField(read_only=True)
    prev_pk = serializers.SerializerMethodField(read_only=True)
    next_pk = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Document
        fields = ('pk', 'issue_project', 'proj_name', 'proj_sort', 'doc_type', 'type_name', 'category',
                  'cate_name', 'cate_color', 'lawsuit', 'lawsuit_name', 'title', 'execution_date', 'content',
                  'hit', 'scrape', 'my_scrape', 'ip', 'device', 'is_secret', 'password', 'is_blind', 'deleted',
                  'links', 'files', 'creator', 'updator', 'created', 'updated', 'is_new', 'prev_pk', 'next_pk')
        read_only_fields = ('ip',)

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
        return len(obj.docscrape_set.all())

    def get_my_scrape(self, obj):
        user = self.context['request'].user
        scrapes = obj.docscrape_set.all()
        users = [s.user for s in scrapes]
        return user in users

    def get_prev_pk(self, obj):
        queryset = self.context['view'].filter_queryset(Document.objects.all())
        prev_obj = queryset.filter(pk__lt=obj.pk).order_by('-pk').first()
        return prev_obj.pk if prev_obj else None

    def get_next_pk(self, obj):
        queryset = self.context['view'].filter_queryset(Document.objects.all())
        next_obj = queryset.filter(pk__gt=obj.pk).order_by('pk').first()
        return next_obj.pk if next_obj else None

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')

        validated_data['ip'] = request.META.get('REMOTE_ADDR')  # ip 추가
        validated_data['device'] = request.META.get('HTTP_USER_AGENT')  # device 추가

        docs = super().create(validated_data)  # 기본 create 처리 (save 포함)
        user = request.user

        new_links = self.initial_data.getlist('newLinks', [])  # Links 처리
        if new_links:
            for link in new_links:
                Link.objects.create(docs=docs, link=validate_link(link))

        # Files 처리
        new_files = request.FILES.getlist('new_files')
        new_descs = request.data.getlist('new_descs')
        if new_files:
            for file, desc in zip(new_files, new_descs):
                File.objects.create(docs=docs, file=file, description=desc, creator=user)
        return docs

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get('request')
        user = request.user

        validated_data['ip'] = request.META.get('REMOTE_ADDR')
        validated_data['device'] = request.META.get('HTTP_USER_AGENT')
        
        # updator 설정
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

            # --- Files 처리 ---
            new_files = request.FILES.getlist('new_files')
            new_descs = request.data.getlist('new_descs')

            if new_files:
                for file, desc in zip(new_files, new_descs):
                    File.objects.create(docs=instance, file=file, description=desc, creator=user)

            old_files = self.initial_data.getlist('files', [])
            cng_pks = self.initial_data.getlist('cngPks', [])
            cng_files = self.initial_data.getlist('cngFiles', [])
            cng_maps = dict(zip(cng_pks, cng_files))

            if old_files:
                for json_file in old_files:
                    file = json.loads(json_file)
                    file_object = File.objects.get(pk=file.get('pk'))

                    if file.get('del'):
                        file_object.delete()
                        continue

                    cng_file = cng_maps.get(str(file.get('pk')))
                    if cng_file:
                        try:
                            if default_storage.exists(file_object.file.name):
                                default_storage.delete(file_object.file.name)
                        except Exception as e:
                            print(f"파일 처리 중 오류 발생: {e}")
                        file_object.file = cng_file
                        file_object.creator = user
                        file_object.save()

        except Exception as e:
            print(f"링크 및 파일 처리 중 오류 발생: {e}")

        return instance


class LinkSerializer(serializers.ModelSerializer):
    creator = serializers.SlugField(read_only=True)

    class Meta:
        model = Link
        fields = ('pk', 'docs', 'link', 'description', 'hit', 'creator', 'created')

    readonly_fields = ('hit', 'created')


class FileSerializer(serializers.ModelSerializer):
    creator = serializers.SlugField(read_only=True)

    class Meta:
        model = File
        fields = ('pk', 'docs', 'file', 'file_name', 'file_type',
                  'file_size', 'description', 'hit', 'creator', 'created')

    readonly_fields = ('file_name', 'file_type', 'file_size', 'hit', 'created')


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
        fields = ('pk', 'type_name', 'cate_name', 'title', 'content', 'creator', 'created', 'deleted')

    @staticmethod
    def get_type_name(obj):
        return obj.doc_type.get_type_display()

    def update(self, instance, validated_data):
        instance.restore()
        return instance


# Official Letter --------------------------------------------------------------------------
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
        queryset = self.context['view'].filter_queryset(OfficialLetter.objects.all())
        prev_obj = queryset.filter(pk__lt=obj.pk).order_by('-issue_date', '-pk').first()
        return prev_obj.pk if prev_obj else None

    def get_next_pk(self, obj):
        queryset = self.context['view'].filter_queryset(OfficialLetter.objects.all())
        next_obj = queryset.filter(pk__gt=obj.pk).order_by('issue_date', 'pk').first()
        return next_obj.pk if next_obj else None


class SimpleOfficialLetterSerializer(serializers.ModelSerializer):
    """목록 조회용 간략 시리얼라이저"""
    creator = serializers.SlugField(read_only=True)

    class Meta:
        model = OfficialLetter
        fields = ('pk', 'document_number', 'title', 'recipient_name',
                  'issue_date', 'pdf_file', 'creator', 'created')
