from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportMixin
from rangefilter.filters import DateRangeFilter

from ledger.admin_async import AsyncImportExportMixin
from ledger.models import (
    CompanyAccount, ProjectAccount, Affiliate,
    CompanyBankAccount, ProjectBankAccount,
    CompanyBankTransaction, ProjectBankTransaction,
    CompanyAccountingEntry, ProjectAccountingEntry,
    CompanyLedgerCalculation, ProjectLedgerCalculation,
)
from ledger.resources import (
    CompanyAccountResource, ProjectAccountResource,
    CompanyBankTransactionResource, ProjectBankTransactionResource,
    CompanyAccountingEntryResource, ProjectAccountingEntryResource
)


# ============================================
# Account Admin - 계정 과목
# ============================================

class BaseAccountAdmin(ImportExportMixin, admin.ModelAdmin):
    """Account Admin 공통 기능 (CompanyAccount, ProjectAccount에서 상속)"""
    list_display = (
        'code', 'indented_name', 'category_display', 'direction_display',
        'depth', 'is_category_only', 'is_active', 'order'
    )
    list_display_links = ('indented_name',)
    list_editable = ('order', 'is_category_only', 'is_active')
    list_filter = ('category', 'direction', 'is_category_only', 'is_active')
    search_fields = ('code', 'name', 'description')
    ordering = ('code', 'order')
    readonly_fields = ('depth', 'full_path_display', 'children_display')

    fieldsets = (
        ('기본 정보', {
            'fields': ('code', 'name', 'description', 'parent', 'full_path_display')
        }),
        ('회계 속성', {
            'fields': ('category', 'direction')
        }),
        ('사용 제한', {
            'fields': ('is_active', 'is_category_only'),
            'description': '<strong>분류 전용</strong>: 체크 시 하위 계정만 거래에 사용 가능'
        }),
        ('정렬 및 계층', {
            'fields': ('order', 'depth', 'children_display')
        }),
    )

    @admin.display(description='계정명', ordering='name')
    def indented_name(self, obj):
        """계층 구조를 들여쓰기로 표시"""
        indent = '\u00A0\u00A0\u00A0\u00A0' * (obj.depth - 1)  # 유니코드 공백 문자 사용
        icon = '📁' if obj.is_category_only else '📄'

        # 분류 전용인 경우 굵게 표시
        if obj.is_category_only:
            return format_html('{}{} <strong>{}</strong>', indent, icon, obj.name)
        return format_html('{}{} {}', indent, icon, obj.name)

    @admin.display(description='계정구분')
    def category_display(self, obj):
        """계정구분을 색상과 함께 표시"""
        colors = {
            'asset': '#2196F3',  # 파랑 - 자산
            'liability': '#F44336',  # 빨강 - 부채
            'equity': '#4CAF50',  # 초록 - 자본
            'revenue': '#FF9800',  # 주황 - 수익
            'expense': '#9C27B0',  # 보라 - 비용
            'transfer': '#607D8B',  # 회색 - 대체
        }
        color = colors.get(obj.category, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_category_display()
        )

    @admin.display(description='거래방향')
    def direction_display(self, obj):
        """거래 방향을 아이콘과 함께 표시 (computed direction 포함)"""
        computed = obj.get_computed_direction()

        if computed == 'deposit':
            color = 'green'
            icon = '⬇'
            text = '입금'
        elif computed == 'withdraw':
            color = 'red'
            icon = '⬆'
            text = '출금'
        elif computed == 'both':
            color = 'purple'
            icon = '⬍'
            text = '입금/출금'
        else:
            color = 'gray'
            icon = '—'
            text = '미지정'

        # 분류 전용 계정인 경우 computed 표시임을 알 수 있도록 처리
        if obj.is_category_only and computed and obj.direction != computed:
            return format_html(
                '<span style="color: {};">{} {} <small>(자동)</small></span>',
                color, icon, text
            )
        else:
            return format_html('<span style="color: {};">{} {}</span>', color, icon, text)

    @admin.display(description='전체 경로')
    def full_path_display(self, obj):
        """전체 계층 경로 표시"""
        if obj.pk:
            full_path = obj.get_full_path()
            if full_path:
                return format_html('<code>{}</code>', full_path)
            return '-'
        return '-'

    @admin.display(description='하위 계정')
    def children_display(self, obj):
        """하위 계정 목록 표시"""
        if not obj.pk:
            return "저장 후 하위 계정을 확인할 수 있습니다."

        # 동적으로 모델명 가져오기
        model_name = obj._meta.model_name

        children = obj.children.all()
        if not children.exists():
            return format_html(
                '<em>하위 계정 없음</em><br>'
                '<a href="/admin/ledger/{}/add/?parent={}" target="_blank">+ 하위 계정 추가</a>',
                model_name, obj.pk
            )

        links = []
        for child in children:
            icon = '📁' if child.is_category_only else '📄'
            child_name = child.name or '이름 없음'
            links.append(format_html(
                '{} <a href="/admin/ledger/{}/{}/change/" target="_blank">{}</a>',
                icon, model_name, child.pk, child_name
            ))

        add_link = format_html(
            '<a href="/admin/ledger/{}/add/?parent={}" target="_blank">+ 하위 계정 추가</a>',
            model_name, obj.pk
        )

        if links:
            result = '<br>'.join(links) + '<br><br>' + add_link
            return mark_safe(result)
        else:
            return mark_safe(add_link)

    def get_changeform_initial_data(self, request):
        """URL 파라미터에서 초기값 설정"""
        initial = super().get_changeform_initial_data(request)

        # parent 파라미터가 있으면 상위 계정 설정
        if 'parent' in request.GET:
            try:
                # 동적으로 현재 모델 클래스 가져오기
                ModelClass = self.model
                parent = ModelClass.objects.get(pk=request.GET['parent'])
                initial['parent'] = parent
                # 상위 계정의 속성 상속
                initial['category'] = parent.category
                initial['direction'] = parent.direction
            except ModelClass.DoesNotExist:
                pass

        return initial


@admin.register(CompanyAccount)
class CompanyAccountAdmin(BaseAccountAdmin):
    """본사 계정 과목 Admin"""
    resource_class = CompanyAccountResource

    list_display = (
        'code', 'indented_name', 'category_display', 'direction_display',
        'depth', 'is_category_only', 'is_active', 'requires_affiliate', 'order'
    )
    list_editable = ('order', 'is_category_only', 'is_active', 'requires_affiliate')

    fieldsets = (
        ('기본 정보', {
            'fields': ('code', 'name', 'description', 'parent', 'full_path_display')
        }),
        ('회계 속성', {
            'fields': ('category', 'direction')
        }),
        ('사용 제한', {
            'fields': ('is_active', 'is_category_only', 'requires_affiliate'),
            'description': '<br>'.join([
                '<strong>분류 전용</strong>: 체크 시 하위 계정만 거래에 사용 가능',
                '<strong>관계회사/프로젝트 필수</strong>: 체크 시 회계분개 시 관계회사 또는 프로젝트 선택 필수 (대여금, 투자금 등)'
            ])
        }),
        ('정렬 및 계층', {
            'fields': ('order', 'depth', 'children_display')
        }),
    )


@admin.register(ProjectAccount)
class ProjectAccountAdmin(BaseAccountAdmin):
    """프로젝트 계정 과목 Admin"""
    resource_class = ProjectAccountResource

    list_display = (
        'code', 'indented_name', 'category_display', 'direction_display',
        'depth', 'is_category_only', 'is_active', 'is_payment', 'is_related_contract', 'order'
    )
    list_editable = ('order', 'is_category_only', 'is_active', 'is_payment', 'is_related_contract')
    list_filter = ('category', 'direction', 'is_category_only', 'is_active', 'is_payment', 'is_related_contract')

    fieldsets = (
        ('기본 정보', {
            'fields': ('code', 'name', 'description', 'parent', 'full_path_display')
        }),
        ('회계 속성', {
            'fields': ('category', 'direction')
        }),
        ('프로젝트 특수 속성', {
            'fields': ('is_payment', 'is_related_contract'),
            'description': 'is_payment: 분양대금 항목 여부 / is_related_contract: 공급계약 관련 항목 여부'
        }),
        ('사용 제한', {
            'fields': ('is_active', 'is_category_only'),
            'description': '분류 전용: 체크 시 하위 계정만 거래에 사용 가능'
        }),
        ('정렬 및 계층', {
            'fields': ('order', 'depth', 'children_display')
        }),
    )


# ============================================
# Bank Account Admin
# ============================================

@admin.register(CompanyBankAccount)
class CompanyBankAccountAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'order', 'company', 'depart', 'bankcode', 'alias_name',
                    'number', 'holder', 'open_date', 'note', 'is_hide', 'inactive')
    list_editable = ('order', 'number', 'is_hide', 'inactive')
    list_display_links = ('alias_name',)
    list_filter = ('company', 'depart', 'bankcode', 'holder', 'is_hide', 'inactive')
    search_fields = ('alias_name', 'number', 'holder', 'note')
    ordering = ('order', 'id')


@admin.register(ProjectBankAccount)
class ProjectBankAccountAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'order', 'project', 'alias_name', 'bankcode', 'number',
                    'holder', 'open_date', 'note', 'is_hide', 'inactive', 'directpay', 'is_imprest')
    list_editable = ('order', 'number', 'is_hide', 'inactive', 'directpay', 'is_imprest')
    list_display_links = ('alias_name',)
    list_filter = ('project', 'bankcode', 'holder', 'is_hide', 'inactive', 'directpay', 'is_imprest')
    search_fields = ('alias_name', 'number', 'holder', 'note', 'project__name')
    ordering = ('order', 'id')


# ============================================
# Bank Transaction Admin
# ============================================

@admin.register(CompanyBankTransaction)
class CompanyBankTransactionAdmin(AsyncImportExportMixin, admin.ModelAdmin):
    resource_class = CompanyBankTransactionResource
    list_display = ('id', 'transaction_id_short', 'company', 'bank_account', 'deal_date',
                    'sort', 'formatted_amount', 'content', 'is_balanced', 'creator', 'created_at')
    list_display_links = ('transaction_id_short',)
    list_filter = ('company', 'bank_account', 'sort', 'is_balanced', ('deal_date', DateRangeFilter))
    search_fields = ('transaction_id', 'content', 'note')
    date_hierarchy = 'deal_date'
    ordering = ('-deal_date', '-created_at')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at', 'related_accounting_entries', 'validation_detail')

    def related_accounting_entries(self, obj):
        """연관된 회계분개 항목들을 표시"""
        if not obj.pk:
            return "저장 후 회계분개를 확인할 수 있습니다."

        entries = CompanyAccountingEntry.objects.filter(transaction_id=obj.transaction_id)
        if not entries.exists():
            return format_html(
                '<a href="/admin/ledger/companyaccountingentry/add/?transaction_id={}" target="_blank">'
                '+ 회계분개 추가</a>',
                obj.transaction_id
            )

        links = []
        for entry in entries:
            account_name = f"{entry.account.code} {entry.account.name}" if entry.account else "계정 없음"
            links.append(format_html(
                '<a href="/admin/ledger/companyaccountingentry/{}/change/" target="_blank">'
                '{} - {}원 ({})</a>',
                entry.pk,
                entry.sort,
                f"{entry.amount:,}",
                account_name
            ))

        add_link = format_html(
            '<a href="/admin/ledger/companyaccountingentry/add/?transaction_id={}" target="_blank">'
            '+ 추가</a>',
            obj.transaction_id
        )

        return mark_safe('<br>'.join(links) + '<br>' + add_link)

    related_accounting_entries.short_description = '연관 회계분개'

    @admin.display(description='거래 ID')
    def transaction_id_short(self, obj):
        return str(obj.transaction_id)[:8] + '...'

    @admin.display(description='금액')
    def formatted_amount(self, obj):
        color = 'green' if obj.sort_id == 1 else 'red'  # 1=입금, 2=출금
        sign = '+' if obj.sort_id == 1 else '-'
        formatted_amount = f"{obj.amount:,}"
        return format_html('<span style="color: {};">{} {}원</span>', color, sign, formatted_amount)

    def validation_detail(self, obj):
        """회계 분개 검증 상세 정보 (상세 페이지용)"""
        if not obj.pk:
            return "저장 후 검증 가능합니다."

        result = obj.validate_accounting_entries()

        # 상태 아이콘 및 색상
        if result['is_valid']:
            status_icon = '✅'
            status_color = 'green'
            status_text = '일치'
        else:
            status_icon = '❌'
            status_color = 'red'
            status_text = '불일치'

        return format_html(
            '<div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px;">'
            '<h3 style="color: {};">{} 금액 검증: {}</h3>'
            '<table style="width: 100%; border-collapse: collapse;">'
            '<tr><td style="padding: 5px; border-bottom: 1px solid #eee;"><strong>은행 거래 금액:</strong></td>'
            '<td style="padding: 5px; border-bottom: 1px solid #eee; text-align: right;">{:,}원</td></tr>'
            '<tr><td style="padding: 5px; border-bottom: 1px solid #eee;"><strong>회계 분개 총합:</strong></td>'
            '<td style="padding: 5px; border-bottom: 1px solid #eee; text-align: right;">{:,}원</td></tr>'
            '<tr><td style="padding: 5px; border-bottom: 1px solid #eee;"><strong>차액:</strong></td>'
            '<td style="padding: 5px; border-bottom: 1px solid #eee; text-align: right; color: {};">{:,}원</td></tr>'
            '<tr><td style="padding: 5px;"><strong>회계 분개 개수:</strong></td>'
            '<td style="padding: 5px; text-align: right;">{}개</td></tr>'
            '</table>'
            '</div>',
            status_color, status_icon, status_text,
            result['bank_amount'],
            result['accounting_total'],
            status_color if not result['is_valid'] else 'black',
            result['difference'],
            result['entry_count']
        )

    validation_detail.short_description = '금액 검증 상세'


@admin.register(ProjectBankTransaction)
class ProjectBankTransactionAdmin(AsyncImportExportMixin, admin.ModelAdmin):
    resource_class = ProjectBankTransactionResource
    list_display = ('id', 'transaction_id_short', 'project', 'bank_account', 'deal_date', 'sort',
                    'formatted_amount', 'content', 'is_balanced', 'is_imprest', 'creator', 'created_at')
    list_display_links = ('transaction_id_short',)
    list_filter = ('project', 'bank_account', 'sort', 'is_balanced', 'is_imprest', ('deal_date', DateRangeFilter))
    search_fields = ('transaction_id', 'content', 'note', 'project__name')
    date_hierarchy = 'deal_date'
    ordering = ('-deal_date', '-created_at')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at',
                       'related_accounting_entries', 'validation_detail')

    def related_accounting_entries(self, obj):
        """연관된 회계분개 항목들을 표시"""
        if not obj.pk:
            return "저장 후 회계분개를 확인할 수 있습니다."

        entries = ProjectAccountingEntry.objects.filter(transaction_id=obj.transaction_id)
        if not entries.exists():
            return format_html(
                '<a href="/admin/ledger/projectaccountingentry/add/?transaction_id={}" target="_blank">'
                '+ 회계분개 추가</a>',
                obj.transaction_id
            )

        links = []
        for entry in entries:
            account_name = f"{entry.account.code} {entry.account.name}" if entry.account else "계정 없음"
            links.append(format_html(
                '<a href="/admin/ledger/projectaccountingentry/{}/change/" target="_blank">'
                '{} - {}원 ({})</a>',
                entry.pk,
                entry.sort,
                f"{entry.amount:,}",
                account_name
            ))

        add_link = format_html(
            '<a href="/admin/ledger/projectaccountingentry/add/?transaction_id={}" target="_blank">'
            '+ 추가</a>',
            obj.transaction_id
        )

        return format_html('<br>'.join(links) + '<br>' + add_link)

    related_accounting_entries.short_description = '연관 회계분개'

    @admin.display(description='거래 ID')
    def transaction_id_short(self, obj):
        return str(obj.transaction_id)[:8] + '...'

    @admin.display(description='금액')
    def formatted_amount(self, obj):
        color = 'green' if obj.sort_id == 1 else 'red'  # 1=입금, 2=출금
        sign = '+' if obj.sort_id == 1 else '-'
        formatted_amount = f"{obj.amount:,}"
        return format_html('<span style="color: {};">{} {}원</span>', color, sign, formatted_amount)

    def validation_detail(self, obj):
        """회계 분개 검증 상세 정보 (상세 페이지용)"""
        if not obj.pk:
            return "저장 후 검증 가능합니다."

        result = obj.validate_accounting_entries()

        # 상태 아이콘 및 색상
        if result['is_valid']:
            status_icon = '✅'
            status_color = 'green'
            status_text = '일치'
        else:
            status_icon = '❌'
            status_color = 'red'
            status_text = '불일치'

        return format_html(
            '<div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px;">'
            '<h3 style="color: {};">{} 금액 검증: {}</h3>'
            '<table style="width: 100%; border-collapse: collapse;">'
            '<tr><td style="padding: 5px; border-bottom: 1px solid #eee;"><strong>은행 거래 금액:</strong></td>'
            '<td style="padding: 5px; border-bottom: 1px solid #eee; text-align: right;">{:,}원</td></tr>'
            '<tr><td style="padding: 5px; border-bottom: 1px solid #eee;"><strong>회계 분개 총합:</strong></td>'
            '<td style="padding: 5px; border-bottom: 1px solid #eee; text-align: right;">{:,}원</td></tr>'
            '<tr><td style="padding: 5px; border-bottom: 1px solid #eee;"><strong>차액:</strong></td>'
            '<td style="padding: 5px; border-bottom: 1px solid #eee; text-align: right; color: {};">{:,}원</td></tr>'
            '<tr><td style="padding: 5px;"><strong>회계 분개 개수:</strong></td>'
            '<td style="padding: 5px; text-align: right;">{}개</td></tr>'
            '</table>'
            '</div>',
            status_color, status_icon, status_text,
            result['bank_amount'],
            result['accounting_total'],
            status_color if not result['is_valid'] else 'black',
            result['difference'],
            result['entry_count']
        )

    validation_detail.short_description = '금액 검증 상세'


# ============================================
# Accounting Entry Admin
# ============================================

@admin.register(CompanyAccountingEntry)
class CompanyAccountingEntryAdmin(AsyncImportExportMixin, admin.ModelAdmin):
    resource_class = CompanyAccountingEntryResource
    list_display = ('id', 'transaction_id_short', 'company', 'account_display',
                    'affiliate_display', 'formatted_amount', 'trader', 'evidence_type', 'created_at')
    list_display_links = ('transaction_id_short',)
    list_filter = ('company', 'account__category', 'evidence_type', 'affiliate__sort')
    search_fields = ('transaction_id', 'trader', 'account__name', 'account__code')
    ordering = ('-created_at',)
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')
    autocomplete_fields = ['account', 'affiliate']

    fieldsets = (
        ('거래 정보', {
            'fields': ('transaction_id', 'company', 'amount', 'trader')
        }),
        ('계정 정보', {
            'fields': ('account', 'affiliate')
        }),
        ('증빙 정보', {
            'fields': ('evidence_type',)
        }),
        ('감사 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_changeform_initial_data(self, request):
        """URL 파라미터에서 초기값 설정"""
        initial = super().get_changeform_initial_data(request)

        # transaction_id 파라미터가 있으면 초기값으로 설정
        if 'transaction_id' in request.GET:
            initial['transaction_id'] = request.GET['transaction_id']

            # CompanyBankTransaction에서 company 정보 가져오기
            try:
                bank_transaction = CompanyBankTransaction.objects.get(
                    transaction_id=request.GET['transaction_id']
                )
                initial['company'] = bank_transaction.company
            except CompanyBankTransaction.DoesNotExist:
                pass

        return initial

    @admin.display(description='거래 ID')
    def transaction_id_short(self, obj):
        return str(obj.transaction_id)[:8] + '...'

    @admin.display(description='금액')
    def formatted_amount(self, obj):
        color = 'green' if obj.sort == 1 else 'red'  # 1=입금, 2=출금
        sign = '+' if obj.sort == 1 else '-'
        formatted_amount = f"{obj.amount:,}"
        return format_html('<span style="color: {};">{} {}원</span>', color, sign, formatted_amount)

    @admin.display(description='계정 과목')
    def account_display(self, obj):
        if obj.account:
            return f"{obj.account.code} {obj.account.name}"
        return '-'

    @admin.display(description='관계회사/프로젝트')
    def affiliate_display(self, obj):
        if obj.affiliate:
            return str(obj.affiliate)
        return '-'


@admin.register(ProjectAccountingEntry)
class ProjectAccountingEntryAdmin(AsyncImportExportMixin, admin.ModelAdmin):
    resource_class = ProjectAccountingEntryResource
    list_display = ('id', 'transaction_id_short', 'project', 'account_display', 'contract_display',
                    'installment_order', 'formatted_amount', 'trader', 'evidence_type', 'created_at')
    list_display_links = ('transaction_id_short',)
    list_filter = ('project', 'account__category', 'evidence_type', 'account__is_related_contract')
    search_fields = ('transaction_id', 'trader', 'project__name', 'account__name', 'account__code')
    ordering = ('-created_at',)
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')
    autocomplete_fields = ['account', 'contract']

    fieldsets = (
        ('거래 정보', {
            'fields': ('transaction_id', 'project', 'amount', 'trader')
        }),
        ('계정 정보', {
            'fields': ('account', 'contract')
        }),
        ('증빙 정보', {
            'fields': ('evidence_type',)
        }),
        ('감사 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='거래 ID')
    def transaction_id_short(self, obj):
        return str(obj.transaction_id)[:8] + '...'

    @admin.display(description='금액')
    def formatted_amount(self, obj):
        color = 'green' if obj.sort_id == 1 else 'red'  # 1=입금, 2=출금
        sign = '+' if obj.sort_id == 1 else '-'
        formatted_amount = f"{obj.amount:,}"
        return format_html('<span style="color: {};">{} {}원</span>', color, sign, formatted_amount)

    @admin.display(description='계정 과목')
    def account_display(self, obj):
        if obj.account:
            return f"{obj.account.code} {obj.account.name}"
        return '-'

    @admin.display(description='공급계약')
    def contract_display(self, obj):
        if obj.contract:
            return str(obj.contract)
        return '-'


# ============================================
# Affiliate Admin - 관계회사/프로젝트
# ============================================

@admin.register(Affiliate)
class AffiliateAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('id', 'sort_display', 'company', 'project', 'description_short', 'created_at')
    list_display_links = ('id',)
    list_filter = ('sort', 'company', 'project')
    search_fields = ('company__name', 'project__name', 'description')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('기본 정보', {
            'fields': ('sort',)
        }),
        ('대상 선택', {
            'fields': ('company', 'project'),
            'description': '관계 회사 또는 관련 프로젝트 중 하나를 선택해주세요.'
        }),
        ('상세 정보', {
            'fields': ('description',)
        }),
        ('감사 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='구분')
    def sort_display(self, obj):
        colors = {
            'company': '#2196F3',  # 파랑
            'project': '#4CAF50',  # 초록
        }
        color = colors.get(obj.sort, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color, obj.get_sort_display()
        )

    @admin.display(description='설명')
    def description_short(self, obj):
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'


@admin.register(CompanyLedgerCalculation)
class CompanyLedgerCalculationAdmin(admin.ModelAdmin):
    """본사 원장 정산 Admin"""
    list_display = ('company', 'calculated', 'creator', 'created_at', 'updated_at')
    list_filter = ('company', 'calculated')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('정산 정보', {
            'fields': ('company', 'calculated')
        }),
        ('시스템 정보', {
            'fields': ('creator', 'created_at', 'updated_at')
        }),
    )


@admin.register(ProjectLedgerCalculation)
class ProjectLedgerCalculationAdmin(admin.ModelAdmin):
    """프로젝트 원장 정산 Admin"""
    list_display = ('project', 'calculated', 'creator', 'created_at', 'updated_at')
    list_filter = ('project', 'calculated')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('정산 정보', {
            'fields': ('project', 'calculated')
        }),
        ('시스템 정보', {
            'fields': ('creator', 'created_at', 'updated_at')
        }),
    )
