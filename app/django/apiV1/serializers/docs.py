import json
import os.path
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from docs.models import DocType, Category, LawsuitCase, Document, Link, File, Image


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
    user = SimpleUserSerializer(read_only=True)
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
                  'case_end_date', 'summary', 'user', 'links', 'files', 'created', 'prev_pk', 'next_pk')
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
    class Meta:
        model = Link
        fields = ('pk', 'docs', 'link', 'hit')


class FilesInDocumentSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = File
        fields = ('pk', 'docs', 'file_name', 'file', 'file_type',
                  'file_size', 'description', 'user', 'hit', 'created')


class DocumentSerializer(serializers.ModelSerializer):
    proj_name = serializers.SlugField(source='issue_project', read_only=True)
    proj_sort = serializers.SerializerMethodField(read_only=True)
    type_name = serializers.SerializerMethodField()
    cate_name = serializers.SlugField(source='category', read_only=True)
    cate_color = serializers.SerializerMethodField(read_only=True)
    lawsuit_name = serializers.SlugField(source='lawsuit', read_only=True)
    links = LinksInDocumentSerializer(many=True, read_only=True)
    files = FilesInDocumentSerializer(many=True, read_only=True)
    user = SimpleUserSerializer(read_only=True)
    scrape = serializers.SerializerMethodField(read_only=True)
    my_scrape = serializers.SerializerMethodField(read_only=True)
    prev_pk = serializers.SerializerMethodField(read_only=True)
    next_pk = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Document
        fields = ('pk', 'issue_project', 'proj_name', 'proj_sort', 'doc_type', 'type_name', 'category',
                  'cate_name', 'cate_color', 'lawsuit', 'lawsuit_name', 'title', 'execution_date', 'content',
                  'hit', 'scrape', 'my_scrape', 'ip', 'device', 'is_secret', 'password', 'is_blind', 'deleted',
                  'links', 'files', 'user', 'created', 'updated', 'is_new', 'prev_pk', 'next_pk')
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

    def to_python(self, value):

        def split_url(url):
            """
            Return a list of url parts via urlparse.urlsplit(), or raise
            ValidationError for some malformed URLs.
            """
            try:
                return list(urlsplit(url))
            except ValueError:
                # urlparse.urlsplit can raise a ValueError with some
                # misformatted URLs.
                raise ValidationError(self.error_messages['invalid'], code='invalid')

        if value:
            url_fields = split_url(value)
            if not url_fields[0]:
                # If no URL scheme given, assume http://
                url_fields[0] = 'http'
            if not url_fields[1]:
                # Assume that if no domain is provided, that the path segment
                # contains the domain.
                url_fields[1] = url_fields[2]
                url_fields[2] = ''
                # Rebuild the url_fields list, since the domain segment may now
                # contain the path too.
                url_fields = split_url(urlunsplit(url_fields))
            value = urlunsplit(url_fields)
        return value

    @transaction.atomic
    def create(self, validated_data):
        validated_data['ip'] = self.context.get('request').META.get('REMOTE_ADDR')
        validated_data['device'] = self.context.get('request').META.get('HTTP_USER_AGENT')
        docs = Document.objects.create(**validated_data)

        # Links 처리
        if self.initial_data.get('newLinks'):
            new_links = self.initial_data.getlist('newLinks')
            if new_links:
                for link in new_links:
                    Link.objects.create(docs=docs, link=self.to_python(link))

        # Files 처리
        if self.initial_data.get('newFiles'):
            new_files = self.initial_data.getlist('newFiles')
            if new_files:
                for file in new_files:
                    File.objects.create(docs=docs, file=file)

        return docs

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data['ip'] = self.context.get('request').META.get('REMOTE_ADDR')
        validated_data['device'] = self.context.get('request').META.get('HTTP_USER_AGENT')
        instance.__dict__.update(**validated_data)
        instance.issue_project = validated_data.get('issue_project', instance.issue_project)
        instance.doc_type = validated_data.get('doc_type', instance.doc_type)
        instance.category = validated_data.get('category', instance.category)
        instance.lawsuit = validated_data.get('lawsuit', instance.lawsuit)
        instance.save()

        try:
            # Links 처리
            old_links = self.initial_data.getlist('links')
            if old_links:
                for json_link in old_links:
                    link = json.loads(json_link)
                    link_object = Link.objects.get(pk=link.get('pk'))
                    if link.get('del'):
                        link_object.delete()
                    else:
                        link_object.link = self.to_python(link.get('link'))
                        link_object.save()

            new_links = self.initial_data.getlist('newLinks')
            if new_links:
                for link in new_links:
                    Link.objects.create(docs=instance, link=self.to_python(link))

            # Files 처리
            old_files = self.initial_data.getlist('files')
            if old_files:
                cng_pks = self.initial_data.getlist('cngPks')
                cng_files = self.initial_data.getlist('cngFiles')
                cng_maps = [(pk, cng_files[i]) for i, pk in enumerate(cng_pks)]

                for json_file in old_files:
                    file = json.loads(json_file)
                    file_object = File.objects.get(pk=file.get('pk'))

                    if file.get('del'):
                        file_object.delete()

                    for cng_map in cng_maps:
                        if int(file.get('pk')) == int(cng_map[0]):
                            old_file = file_object.file
                            if os.path.isfile(old_file.path):
                                os.remove(old_file.path)
                            file_object.file = cng_map[1]
                            file_object.save()

            new_files = self.initial_data.getlist('newFiles')
            if new_files:
                for file in new_files:
                    File.objects.create(docs=instance, file=file)
        except AttributeError:
            pass

        return instance


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ('pk', 'docs', 'link', 'hit')


class FileSerializer(serializers.ModelSerializer):
    user = serializers.SlugField(source='username', read_only=True)

    class Meta:
        model = File
        fields = ('pk', 'docs', 'file', 'file_name', 'file_type',
                  'file_size', 'description', 'hit', 'user', 'created')

    readonly_fields = ('file_name', 'file_type', 'file_size', 'hit', 'created')


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('pk', 'docs', 'image', 'image_name', 'image_type', 'image_size', 'created')

    readonly_fields = ('image_name', 'image_type', 'image_size', 'created')


class DocumentInTrashSerializer(serializers.ModelSerializer):
    type_name = serializers.SerializerMethodField()
    cate_name = serializers.SlugField(source='category', read_only=True)
    # user = serializers.SlugField(read_only=True)
    user = serializers.SlugField(source='username', read_only=True)

    class Meta:
        model = Document
        fields = ('pk', 'type_name', 'cate_name', 'title', 'content', 'user', 'created', 'deleted')

    @staticmethod
    def get_type_name(obj):
        return obj.doc_type.get_type_display()

    def update(self, instance, validated_data):
        instance.restore()
        return instance
