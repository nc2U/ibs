import os

from django.db import transaction
from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from notice.models import SalesBillIssue
from project.models import (Project, ProjectIncBudget, ProjectOutBudget, Site, SiteOwner,
                            SiteOwnshipRelationship, SiteContract, SiteContractFile)
from ibs.models import ProjectAccountD2, ProjectAccountD3
from cash.models import ProjectCashBook


# Project --------------------------------------------------------------------------
class SallesBillInProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesBillIssue
        fields = ('pk', 'project', 'now_payment_order', 'host_name', 'host_tel',
                  'agency', 'agency_tel', 'bank_account1', 'bank_number1', 'bank_host1',
                  'bank_account2', 'bank_number2', 'bank_host2', 'zipcode', 'address1',
                  'address2', 'address3', 'title', 'content')


class ProjectSerializer(serializers.ModelSerializer):
    company = serializers.SerializerMethodField(read_only=True)
    kind = serializers.ChoiceField(choices=Project.KIND_CHOICES)
    kind_desc = serializers.CharField(source='get_kind_display', read_only=True)
    salesbillissue = SallesBillInProjectSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ('pk', 'company', 'issue_project', 'name', 'order', 'kind', 'kind_desc',
                  'start_year', 'is_direct_manage', 'is_returned_area', 'is_unit_set',
                  'local_zipcode', 'local_address1', 'local_address2', 'local_address3',
                  'area_usage', 'build_size', 'num_unit', 'buy_land_extent', 'scheme_land_extent',
                  'donation_land_extent', 'on_floor_area', 'under_floor_area', 'total_floor_area',
                  'build_area', 'floor_area_ratio', 'build_to_land_ratio', 'num_legal_parking',
                  'num_planed_parking', 'salesbillissue')

    @staticmethod
    def get_company(obj):
        return obj.issue_project.company.pk


class ProjectIncBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectIncBudget
        fields = ('pk', 'project', 'account_d2', 'account_d3', 'order_group',
                  'unit_type', 'item_name', 'average_price', 'quantity', 'budget', 'revised_budget')


class ProjectOutBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectOutBudget
        fields = ('pk', 'project', 'order', 'account_d2', 'account_d3',
                  'account_opt', 'basis_calc', 'budget', 'revised_budget')


class ProAccoD2InBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAccountD2
        fields = ('pk', 'name', 'pro_d3s')


class ProAccoD3InBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAccountD3
        fields = ('pk', 'name')


class StatusOutBudgetSerializer(serializers.ModelSerializer):
    account_d2 = ProAccoD2InBudgetSerializer()
    account_d3 = ProAccoD3InBudgetSerializer()

    class Meta:
        model = ProjectOutBudget
        fields = ('pk', 'project', 'order', 'account_d2', 'account_d3',
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


class SiteSerializer(serializers.ModelSerializer):
    owners = SiteOwnerInSiteSerializer(many=True, read_only=True)

    class Meta:
        model = Site
        fields = ('pk', 'project', 'order', 'district', 'lot_number', 'site_purpose',
                  'official_area', 'returned_area', 'notice_price', 'rights_a',
                  'rights_b', 'dup_issue_date', 'owners', 'note')


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

    class Meta:
        model = SiteOwner
        fields = ('pk', 'project', 'owner', 'use_consent', 'date_of_birth', 'phone1',
                  'phone2', 'zipcode', 'address1', 'address2', 'address3',
                  'own_sort', 'own_sort_desc', 'sites', 'counsel_record')

    @transaction.atomic
    def create(self, validated_data):
        site_owner = SiteOwner.objects.create(**validated_data)
        if 'sites' in self.initial_data:
            sites = self.initial_data.get('sites')
            # for site in sites:
            #     pk = site.get('pk')
            #     ownership_ratio = site.get('ownership_ratio')
            #     owned_area = site.get('owned_area')
            #     acquisition_date = site.get('acquisition_date')
            #     site_instance = Site.objects.get(pk=pk)
            #     SiteOwnshipRelationship(site=site_instance, site_owner=site_owner, ownership_ratio=ownership_ratio,
            #                             owned_area=owned_area, acquisition_date=acquisition_date).save()
            for site in sites:
                site_instance = Site.objects.get(pk=site)
                SiteOwnshipRelationship(site=site_instance, site_owner=site_owner).save()

        site_owner.save()
        return site_owner

    @transaction.atomic
    def update(self, instance, validated_data):
        sites = self.initial_data.get('sites')
        relations = SiteOwnshipRelationship.objects.filter(site_owner=instance)  # .delete()
        stored_sites = []
        for r in relations:
            if r.site.pk in sites:
                stored_sites.append(r.site.pk)
            else:
                r.delete()
        for site in sites:
            if site not in stored_sites:
                new_site = Site.objects.get(pk=site)
                SiteOwnshipRelationship(site=new_site, site_owner=instance).save()

        instance.__dict__.update(**validated_data)
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


class ContractFileInSiteContractSetSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = SiteContractFile
        fields = ('pk', 'file', 'file_name', 'file_size', 'created', 'user')


class SiteContractSerializer(serializers.ModelSerializer):
    owner_desc = SiteOwnerInSiteSerializer(source='owner', read_only=True)
    site_cont_files = ContractFileInSiteContractSetSerializer(many=True, read_only=True)

    class Meta:
        model = SiteContract
        fields = ('pk', 'project', 'owner', 'owner_desc', 'contract_date', 'total_price',
                  'contract_area', 'down_pay1', 'down_pay1_date', 'down_pay1_is_paid', 'down_pay2',
                  'down_pay2_date', 'down_pay2_is_paid', 'inter_pay1', 'inter_pay1_date',
                  'inter_pay1_is_paid', 'inter_pay2', 'inter_pay2_date', 'inter_pay2_is_paid',
                  'remain_pay', 'remain_pay_date', 'remain_pay_is_paid', 'ownership_completion',
                  'acc_bank', 'acc_number', 'acc_owner', 'site_cont_files', 'note')

    @transaction.atomic
    def create(self, validated_data):
        site_contract = SiteContract.objects.create(**validated_data)
        site_contract.save()

        owner = SiteOwner.objects.get(pk=site_contract.owner.id)
        owner.use_consent = True
        owner.save()

        new_file = self.initial_data.get('newFile', None)
        if new_file:
            user = self.context['request'].user
            cont_file = SiteContractFile(site_contract=site_contract, file=new_file, user=user)
            cont_file.save()
        return site_contract

    @transaction.atomic
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        new_file = self.initial_data.get('newFile', None)
        if new_file:
            user = self.context['request'].user
            SiteContractFile.objects.create(site_contract=instance, file=new_file, user=user)

        edit_file = self.initial_data.get('editFile', None)  # pk of file to edit
        cng_file = self.initial_data.get('cngFile', None)  # new file to replace

        if edit_file and cng_file:
            try:
                file_to_edit = SiteContractFile.objects.get(pk=edit_file)
                old_file_path = file_to_edit.file.path
                # Remove old file if it exists
                if os.path.isfile(old_file_path):
                    os.remove(old_file_path)
                # Save new file
                file_to_edit.file = cng_file
                file_to_edit.save()
            except SiteContractFile.DoesNotExist:
                raise serializers.ValidationError(f"File with ID {edit_file} does not exist.")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Error while replacing file: {str(e)}')
                raise serializers.ValidationError('An error occurred while replacing the file.')

        del_file = self.initial_data.get('delFile', None)
        if del_file:
            try:
                file_to_delete = SiteContractFile.objects.get(pk=del_file)
                file_to_delete.delete()
            except SiteContractFile.DoesNotExist:
                raise serializers.ValidationError(f"File with ID {del_file} does not exist.")

        return instance
