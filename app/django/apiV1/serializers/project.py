import os

from django.db import transaction
from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from cash.models import ProjectCashBook
from contract.models import DocumentType, RequiredDocument
from ibs.models import ProjectAccountD2, ProjectAccountD3
from ledger.models import ProjectAccount
from notice.models import SalesBillIssue
from project.models import (Project, ProjectIncBudget, ProjectOutBudget, Site, SiteInfoFile,
                            SiteOwner, SiteOwnshipRelationship, SiteContract, SiteContractFile)


# Project --------------------------------------------------------------------------
class SallesBillInProjectSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = SalesBillIssue
        fields = ('pk', 'project', 'now_payment_order', 'host_name', 'host_tel',
                  'agency', 'agency_tel', 'bank_account1', 'bank_number1', 'bank_host1',
                  'bank_account2', 'bank_number2', 'bank_host2', 'zipcode', 'address1',
                  'address2', 'address3', 'title', 'content', 'creator', 'updated')


class ProjectSerializer(serializers.ModelSerializer):
    company = serializers.SerializerMethodField(read_only=True)
    kind = serializers.ChoiceField(choices=Project.KIND_CHOICES)
    kind_desc = serializers.CharField(source='get_kind_display', read_only=True)
    salesbillissue = SallesBillInProjectSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ('pk', 'company', 'issue_project', 'name', 'order', 'kind', 'kind_desc', 'start_year',
                  'is_direct_manage', 'is_returned_area', 'is_unit_set', 'monthly_aggr_start_date',
                  'construction_start_date', 'construction_period_months', 'location', 'area_usage', 'build_size',
                  'num_unit', 'buy_land_extent', 'scheme_land_extent', 'donation_land_extent', 'on_floor_area',
                  'under_floor_area', 'total_floor_area', 'build_area', 'floor_area_ratio', 'build_to_land_ratio',
                  'num_legal_parking', 'num_planed_parking', 'salesbillissue')

    @staticmethod
    def get_company(obj):
        return obj.issue_project.company.pk

    def _create_default_required_documents(self, project):
        """
        프로젝트에 기본 필요 서류 자동 생성

        Args:
            project: Project 인스턴스
        """
        # 기본 서류 타입들을 RequiredDocument로 자동 등록
        default_document_types = DocumentType.objects.filter(
            is_default_item=True,
            is_active=True
        ).order_by('id')

        required_docs = [
            RequiredDocument(
                project=project,
                document_type=doc_type,
                sort=doc_type.sort,
                quantity=doc_type.default_quantity,
                require_type=doc_type.require_type,
                description=doc_type.description,
                creator=self.context.get('request').user if self.context.get('request') else None
            )
            for doc_type in default_document_types
        ]

        if required_docs:
            RequiredDocument.objects.bulk_create(required_docs)

    def _sync_required_documents(self, project):
        """
        프로젝트의 필요 서류를 DocumentType과 동기화

        1. 기존 서류의 필드 업데이트 (sort, quantity, require_type, description)
        2. 새로운 기본 서류 추가
        3. 비활성화된 서류는 그대로 유지 (이미 제출된 서류가 있을 수 있음)

        Args:
            project: Project 인스턴스
        """
        # 현재 프로젝트의 RequiredDocument 조회 (document_type과 함께)
        existing_docs = RequiredDocument.objects.filter(project=project).select_related('document_type')

        # 기존 문서들의 필드를 DocumentType과 동기화
        docs_to_update = []
        for req_doc in existing_docs:
            doc_type = req_doc.document_type
            # DocumentType의 필드가 변경되었는지 확인
            if (req_doc.sort != doc_type.sort or
                    req_doc.quantity != doc_type.default_quantity or
                    req_doc.require_type != doc_type.require_type or
                    req_doc.description != doc_type.description):
                req_doc.sort = doc_type.sort
                req_doc.quantity = doc_type.default_quantity
                req_doc.require_type = doc_type.require_type
                req_doc.description = doc_type.description
                req_doc.updator = self.context.get('request').user if self.context.get('request') else None
                docs_to_update.append(req_doc)

        # 변경된 문서들 일괄 업데이트
        if docs_to_update:
            RequiredDocument.objects.bulk_update(
                docs_to_update,
                ['sort', 'quantity', 'require_type', 'description', 'updator', 'updated']
            )

        # 현재 프로젝트에 등록된 서류 타입 ID들
        existing_doc_types = set(doc.document_type_id for doc in existing_docs)

        # 기본 서류 중 아직 없는 것들만 추가
        default_document_types = DocumentType.objects.filter(
            is_default_item=True,
            is_active=True
        ).exclude(id__in=existing_doc_types).order_by('id')

        new_docs = [
            RequiredDocument(
                project=project,
                document_type=doc_type,
                sort=doc_type.sort,
                quantity=doc_type.default_quantity,
                require_type=doc_type.require_type,
                description=doc_type.description,
                creator=self.context.get('request').user if self.context.get('request') else None
            )
            for doc_type in default_document_types
        ]

        if new_docs:
            RequiredDocument.objects.bulk_create(new_docs)

    @transaction.atomic
    def create(self, validated_data):
        """프로젝트 생성 시 기본 필요 서류 자동 생성"""
        project = super().create(validated_data)
        self._create_default_required_documents(project)
        return project

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        프로젝트 업데이트 시 필요 서류 동기화
        RequiredDocument가 없으면 생성, 있으면 DocumentType과 동기화
        """
        # 프로젝트 업데이트
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # RequiredDocument가 없으면 생성, 있으면 동기화
        if not RequiredDocument.objects.filter(project=instance).exists():
            self._create_default_required_documents(instance)
        else:
            self._sync_required_documents(instance)

        return instance


class ProjectIncBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectIncBudget
        fields = ('pk', 'project', 'account', 'account_d2', 'account_d3', 'order_group',
                  'unit_type', 'item_name', 'average_price', 'quantity', 'budget', 'revised_budget')


class ProjectOutBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectOutBudget
        fields = ('pk', 'project', 'order', 'account', 'account_d2', 'account_d3',
                  'account_opt', 'basis_calc', 'budget', 'revised_budget')


class ProAccountInBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAccount
        fields = ('pk', 'name')


class ProAccoD2InBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAccountD2
        fields = ('pk', 'name', 'pro_d3s')


class ProAccoD3InBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAccountD3
        fields = ('pk', 'name')


class StatusOutBudgetSerializer(serializers.ModelSerializer):
    account = ProAccountInBudgetSerializer()
    account_d2 = ProAccoD2InBudgetSerializer()
    account_d3 = ProAccoD3InBudgetSerializer()

    class Meta:
        model = ProjectOutBudget
        fields = ('pk', 'project', 'order', 'account', 'account_d2', 'account_d3',
                  'account_opt', 'basis_calc', 'budget', 'revised_budget')


class ExecAmountToBudget(serializers.ModelSerializer):
    acc_d3 = serializers.IntegerField()
    all_sum = serializers.IntegerField()
    month_sum = serializers.IntegerField()

    class Meta:
        model = ProjectCashBook
        fields = ('acc_d3', 'all_sum', 'month_sum')


class TotalSiteAreaSerializer(serializers.ModelSerializer):
    project = serializers.IntegerField()
    official = serializers.DecimalField(max_digits=12, decimal_places=7)
    returned = serializers.DecimalField(max_digits=12, decimal_places=7)

    class Meta:
        model = Site
        fields = ('project', 'official', 'returned')


class SiteOwnerInSiteSerializer(serializers.ModelSerializer):
    own_sort_desc = serializers.CharField(source='get_own_sort_display', read_only=True)

    class Meta:
        model = SiteOwner
        fields = ('pk', 'owner', 'own_sort_desc')


class FileInSiteDataSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = SiteContractFile
        fields = ('pk', 'file', 'file_name', 'file_size', 'created', 'creator')


class SiteSerializer(serializers.ModelSerializer):
    owners = SiteOwnerInSiteSerializer(many=True, read_only=True)
    site_info_files = FileInSiteDataSerializer(many=True, read_only=True)
    creator = SimpleUserSerializer(read_only=True)
    updator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Site
        fields = ('pk', 'project', 'order', 'district', 'lot_number', 'site_purpose',
                  'official_area', 'returned_area', 'notice_price', 'rights_a',
                  'rights_b', 'dup_issue_date', 'owners', 'note', 'site_info_files',
                  'creator', 'updator', 'created', 'updated')

    @transaction.atomic
    def create(self, validated_data):
        site = Site.objects.create(**validated_data)

        request = self.context['request']
        new_file = request.data.get('newFile', None)
        if new_file:
            info_file = SiteInfoFile(site=site, file=new_file, creator=request.user)
            info_file.save()
        return site

    @transaction.atomic
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Set updator from request context
        instance.updator = self.context['request'].user
        instance.save()

        data = self.context['request'].data
        user = self.context['request'].user

        new_file = data.get('newFile')
        if new_file:
            SiteInfoFile.objects.create(site=instance, file=new_file, creator=user)

        edit_file = data.get('editFile', None)  # pk of a file to edit
        cng_file = data.get('cngFile', None)  # new file to replace

        if edit_file and cng_file:
            try:
                file_to_edit = SiteInfoFile.objects.get(pk=edit_file, site=instance)
                old_file_path = file_to_edit.file.path

                if file_to_edit.file and os.path.isfile(old_file_path):
                    try:  # Remove an old file if it exists
                        os.remove(old_file_path)
                    except OSError as e:
                        print(f"Error while deleting old file {old_file_path}: {e}")

                file_to_edit.file = cng_file  # Save new file
                file_to_edit.save()
            except SiteInfoFile.DoesNotExist:
                raise serializers.ValidationError(f"File with ID {edit_file} does not exist.")
            except Exception as e:
                print(f"Exception occurred: {e}")
                raise serializers.ValidationError('An error occurred while replacing the file.')

        del_file = data.get('delFile', None)
        if del_file:
            try:
                file_to_delete = SiteInfoFile.objects.get(pk=del_file, site=instance)
                file_to_delete.delete()
            except SiteInfoFile.DoesNotExist:
                raise serializers.ValidationError(f"File with ID {del_file} does not exist.")

        return instance


class AllSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ('pk', '__str__')


class TotalOwnerAreaSerializer(serializers.ModelSerializer):
    project = serializers.IntegerField()
    owned_area = serializers.DecimalField(max_digits=12, decimal_places=7)

    class Meta:
        model = SiteOwner
        fields = ('project', 'owned_area')


class RelationsInSiteOwnerSerializer(serializers.ModelSerializer):
    site = serializers.ReadOnlyField(source='site.pk')
    __str__ = serializers.ReadOnlyField(source='site.__str__')

    class Meta:
        model = SiteOwnshipRelationship
        fields = ('pk', 'site', '__str__', 'ownership_ratio', 'owned_area', 'acquisition_date')


class SiteOwnerSerializer(serializers.ModelSerializer):
    date_of_birth = serializers.DateField(
        input_formats=["%Y-%m-%d"],  # 허용할 날짜 형식
        required=False,  # 필수 입력이 아님
        allow_null=True,  # Null 값 허용
        error_messages={
            "invalid": "날짜 형식이 잘못되었습니다. YYYY-MM-DD 형식으로 입력하세요."
        }
    )
    own_sort_desc = serializers.CharField(source='get_own_sort_display', read_only=True)
    sites = RelationsInSiteOwnerSerializer(source='relations', many=True, read_only=True)
    creator = SimpleUserSerializer(read_only=True)
    updator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = SiteOwner
        fields = ('pk', 'project', 'owner', 'use_consent', 'date_of_birth', 'phone1',
                  'phone2', 'zipcode', 'address1', 'address2', 'address3',
                  'own_sort', 'own_sort_desc', 'sites', 'note',
                  'creator', 'updator', 'created', 'updated')

    @transaction.atomic
    def create(self, validated_data):
        sites = self.initial_data.get('sites', [])
        site_owner = SiteOwner.objects.create(**validated_data)

        for site in sites:
            site_instance = Site.objects.get(pk=site)
            SiteOwnshipRelationship.objects.create(site=site_instance, site_owner=site_owner)

        return site_owner

    @transaction.atomic
    def update(self, instance, validated_data):
        sites = self.initial_data.get('sites', [])
        existing_relations = SiteOwnshipRelationship.objects.filter(site_owner=instance)

        existing_site_pks = set(r.site.pk for r in existing_relations)
        incoming_site_pks = set(sites)

        # 삭제할 관계
        for relation in existing_relations:
            if relation.site.pk not in incoming_site_pks:
                relation.delete()

        # 새로 추가할 관계
        for site_pk in incoming_site_pks - existing_site_pks:
            site = Site.objects.get(pk=site_pk)
            SiteOwnshipRelationship.objects.create(site=site, site_owner=instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Set updator from request context
        instance.updator = self.context['request'].user
        instance.save()
        return instance


class AllOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteOwner
        fields = ('pk', 'owner')


class SiteOwnshipRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteOwnshipRelationship
        fields = ('pk', 'site', 'site_owner', 'ownership_ratio', 'owned_area', 'acquisition_date')


class TotalContractedAreaSerializer(serializers.ModelSerializer):
    project = serializers.IntegerField()
    contracted_area = serializers.DecimalField(max_digits=12, decimal_places=7)

    class Meta:
        model = SiteOwner
        fields = ('project', 'contracted_area')


class SiteContractSerializer(serializers.ModelSerializer):
    owner_desc = SiteOwnerInSiteSerializer(source='owner', read_only=True)
    site_cont_files = FileInSiteDataSerializer(many=True, read_only=True)
    creator = SimpleUserSerializer(read_only=True)
    updator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = SiteContract
        fields = ('pk', 'project', 'owner', 'owner_desc', 'contract_date', 'total_price',
                  'contract_area', 'down_pay1', 'down_pay1_date', 'down_pay1_is_paid', 'down_pay2',
                  'down_pay2_date', 'down_pay2_is_paid', 'inter_pay1', 'inter_pay1_date',
                  'inter_pay1_is_paid', 'inter_pay2', 'inter_pay2_date', 'inter_pay2_is_paid',
                  'remain_pay', 'remain_pay_date', 'remain_pay_is_paid', 'ownership_completion',
                  'acc_bank', 'acc_number', 'acc_owner', 'site_cont_files', 'note',
                  'creator', 'updator', 'created', 'updated')

    @transaction.atomic
    def create(self, validated_data):
        site_contract = SiteContract.objects.create(**validated_data)

        owner = SiteOwner.objects.get(pk=site_contract.owner.id)
        owner.use_consent = True
        owner.save()

        new_file = self.initial_data.get('newFile', None)
        if new_file:
            user = self.context['request'].user
            cont_file = SiteContractFile(site_contract=site_contract, file=new_file, creator=user)
            cont_file.save()
        return site_contract

    @transaction.atomic
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Set updator from request context
        instance.updator = self.context['request'].user
        instance.save()

        data = self.context['request'].data
        user = self.context['request'].user

        new_file = data.get('newFile')
        if new_file:
            SiteContractFile.objects.create(site_contract=instance, file=new_file, creator=user)

        edit_file = data.get('editFile', None)  # pk of file to edit
        cng_file = data.get('cngFile', None)  # new file to replace

        if edit_file and cng_file:
            try:
                file_to_edit = SiteContractFile.objects.get(pk=edit_file, site_contract=instance)
                old_file_path = file_to_edit.file.path

                if file_to_edit.file and os.path.isfile(old_file_path):
                    try:  # Remove an old file if it exists
                        os.remove(old_file_path)
                    except OSError as e:
                        print(f"오류: {e}")

                file_to_edit.file = cng_file  # Save new file
                file_to_edit.save()
            except SiteContractFile.DoesNotExist:
                raise serializers.ValidationError(f"File with ID {edit_file} does not exist.")
            except Exception as e:
                print(f"Exception occurred: {e}")
                raise serializers.ValidationError('An error occurred while replacing the file.')

        del_file = data.get('delFile', None)
        if del_file:
            try:
                file_to_delete = SiteContractFile.objects.get(pk=del_file, site_contract=instance)
                file_to_delete.delete()
            except SiteContractFile.DoesNotExist:
                raise serializers.ValidationError(f"File with ID {del_file} does not exist.")

        return instance
