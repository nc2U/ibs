from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import accounts
from .views import company
from .views import ibs
from .views import work
from .views import project
from .views import items
from .views import payment
from .views import cash
from .views import contract
from .views import notice
from .views import board
from .views import docs
from .views import ledger

app_name = 'api'

router = DefaultRouter()

# accounts
router.register(r'user', accounts.UserViewSet)
router.register(r'staff-auth', accounts.StaffAuthViewSet)
router.register(r'profile', accounts.ProfileViewSet)
router.register(r'doc-scrape', accounts.DocScrapeViewSet)
router.register(r'post-scrape', accounts.PostScrapeViewSet)
router.register(r'todo', accounts.TodoViewSet)
router.register(r'pass-reset-token', accounts.PasswordResetTokenViewSet)

# company
router.register(r'company', company.CompanyViewSet)
router.register(r'logo', company.LogoViewSet)
router.register(r'department', company.DepartmentViewSet)
router.register(r'grade', company.JobGradeViewSet)
router.register(r'position', company.PositionViewSet)
router.register(r'duty-title', company.DutyTitleViewSet)
router.register(r'staff', company.StaffViewSet)

# ibs
router.register(r'schedule', ibs.CalendarScheduleViewSet)
router.register(r'account-sort', ibs.AccountSortViewSet)  # only list
router.register(r'account-depth1', ibs.AccountSubD1ViewSet)  # only list
router.register(r'account-depth2', ibs.AccountSubD2ViewSet)  # only list
router.register(r'account-depth3', ibs.AccountSubD3ViewSet)  # only list
router.register(r'project-account-depth2', ibs.ProjectAccountD2ViewSet)  # only list
router.register(r'project-account-depth3', ibs.ProjectAccountD3ViewSet)  # only list
router.register(r'wise-say', ibs.WiseSayViewSet)

# work
router.register(r'issue-project', work.IssueProjectViewSet)
router.register(r'gantt-issues', work.IssueProjectForGanttViewSet, basename='gantt-issues')
router.register(r'role', work.RoleViewSet)
# router.register(r'permission', work.PermissionViewSet)
router.register(r'member', work.MemberViewSet)
router.register(r'module', work.ModuleViewSet)
router.register(r'version', work.VersionViewSet)
router.register(r'repository', work.RepositoryViewSet)
router.register(r'branch', work.BranchViewSet)
router.register(r'commit', work.CommitViewSet)
router.register(r'tracker', work.TrackerViewSet)
router.register(r'issue-by-tracker-summary', work.IssueCountByTrackerViewSet, basename='issue-by-tracker-summary')
router.register(r'issue-status', work.IssueStatusViewSet)
router.register(r'workflow', work.WorkflowViewSet)
router.register(r'code-activity', work.CodeActivityViewSet)
router.register(r'code-priority', work.CodeIssuePriorityViewSet)
router.register(r'code-docs-category', work.CodeDocsCategoryViewSet)
router.register(r'issue-category', work.IssueCategoryViewSet)
router.register(r'issue', work.IssueViewSet)
router.register(r'issue-relation', work.IssueRelationViewSet)
router.register(r'issue-file', work.IssueFileViewSet)
router.register(r'issue-comment', work.IssueCommentViewSet)
router.register(r'time-entry', work.TimeEntryViewSet)
router.register(r'news', work.NewsViewSet)
router.register(r'news-comment', work.NewsCommentViewSet)
router.register(r'act-entry', work.ActivityLogEntryViewSet)
router.register(r'log-entry', work.IssueLogEntryViewSet)
router.register(r'issue-search', work.SearchViewSet)

# project
router.register(r'project', project.ProjectViewSet)
router.register(r'inc-budget', project.ProjectIncBudgetViewSet)  # only list
router.register(r'out-budget', project.ProjectOutBudgetViewSet)  # only list
router.register(r'status-budget', project.StatusOutBudgetViewSet, basename='status-budget')  # only list
router.register(r'exec-amount', project.ExecAmountToBudgetViewSet, basename='exec-amount')  # only list
router.register(r'site', project.SiteViewSet)
router.register(r'all-site', project.AllSiteViewSet, basename='all-site')  # only list
router.register(r'sites-total', project.TotalSiteAreaViewSet, basename='sites-total')  # only list
router.register(r'site-owner', project.SiteOwnerViewSet)
router.register(r'all-owner', project.AllOwnerViewSet, basename='all-owner')  # only list
router.register(r'owners-total', project.TotalOwnerAreaViewSet, basename='owners-total')  # only list
router.register(r'site-relation', project.SiteRelationViewSet)
router.register(r'site-contract', project.SiteContractViewSet)
router.register(r'conts-total', project.TotalContractedAreaViewSet, basename='conts-total')  # only list

# items
router.register(r'type', items.UnitTypeViewSet)
router.register(r'floor', items.UnitFloorTypeViewSet)
router.register(r'key-unit', items.KeyUnitViewSet)
router.register(r'bldg', items.BuildingUnitViewSet)
router.register(r'house-unit', items.HouseUnitViewSet)
router.register(r'available-house-unit', items.AvailableHouseUnitViewSet,
                basename='available-house-unit')  # only list
router.register(r'all-house-unit', items.AllHouseUnitViewSet, basename='all-house-unit')  # only list
router.register(r'unit-summary', items.HouseUnitSummaryViewSet, basename='unit-summary')
router.register(r'option-item', items.OptionItemViewSet, basename='option-item')

# payment
router.register(r'pay-order', payment.InstallmentOrderViewSet)
router.register(r'price', payment.SalesPriceViewSet)
router.register(r'payment-installment', payment.PaymentPerInstallmentViewSet)
router.register(r'down-payment', payment.DownPaymentViewSet)
router.register(r'payment', payment.PaymentViewSet, basename='payment')  # only list
router.register(r'all-payment', payment.AllPaymentViewSet, basename='all-payment')  # only list
router.register(r'payment-summary', payment.PaymentSummaryViewSet, basename='payment-summary')  # only list
router.register(r'payment-status-by-unit-type', payment.PaymentStatusByUnitTypeViewSet,
                basename='payment-status-by-unit-type')  # only list
router.register(r'overall-summary', payment.OverallSummaryViewSet, basename='overall-summary')  # only list

# cash
router.register(r'bank-code', cash.BankCodeViewSet)
router.register(r'company-bank-account', cash.ComBankAccountViewSet)

# ledger (new architecture)
router.register(r'ledger/company-account', ledger.CompanyAccountViewSet, basename='ledger-company-account')
router.register(r'ledger/project-account', ledger.ProjectAccountViewSet, basename='ledger-project-account')
router.register(r'ledger/bank-code', ledger.LedgerBankCodeViewSet, basename='ledger-bank-code')
router.register(r'ledger/company-bank-account', ledger.LedgerCompanyBankAccountViewSet,
                basename='ledger-company-bank-account')
router.register(r'ledger/project-bank-account', ledger.LedgerProjectBankAccountViewSet,
                basename='ledger-project-bank-account')
router.register(r'ledger/affiliate', ledger.AffiliateViewSet, basename='ledger-affiliate')
router.register(r'ledger/company-transaction', ledger.CompanyBankTransactionViewSet,
                basename='ledger-company-transaction')
router.register(r'ledger/project-transaction', ledger.ProjectBankTransactionViewSet,
                basename='ledger-project-transaction')
router.register(r'ledger/company-accounting-entry', ledger.CompanyAccountingEntryViewSet,
                basename='ledger-company-accounting-entry')
router.register(r'ledger/project-accounting-entry', ledger.ProjectAccountingEntryViewSet,
                basename='ledger-project-accounting-entry')
router.register(r'ledger/company-composite-transaction', ledger.CompanyCompositeTransactionViewSet,
                basename='ledger-company-composite-transaction')
router.register(r'ledger/project-composite-transaction', ledger.ProjectCompositeTransactionViewSet,
                basename='ledger-project-composite-transaction')
router.register(r'ledger/company-calculation', ledger.CompanyLedgerCalculationViewSet)
router.register(r'ledger/project-calculation', ledger.ProjectLedgerCalculationViewSet)
router.register(r'ledger/company-last-deal-date', ledger.CompanyLedgerLastDealDateViewSet)
router.register(r'ledger/project-last-deal-date', ledger.ProjectLedgerLastDealDateViewSet)

# cash
router.register(r'balance-by-acc', cash.BalanceByAccountViewSet, basename='balance-by-acc')  # only list
router.register(r'cashbook', cash.CashBookViewSet)
router.register(r'com-cash-calc', cash.CompanyCashCalcViewSet)
router.register(r'com-last-deal', cash.CompanyLastDealDateViewSet, basename='com-last-deal')  # only list
router.register(r'date-cashbook', cash.DateCashBookViewSet, basename='date-cashbook')  # only list
router.register(r'project-bank-account', cash.ProjectBankAccountViewSet)
router.register(r'pr-balance-by-acc', cash.PrBalanceByAccountViewSet, basename='pr-balance-by-acc')  # only list
router.register(r'project-cashbook', cash.ProjectCashBookViewSet)
router.register(r'pro-cash-calc', cash.ProjectCashCalcViewSet)
router.register(r'pro-last-deal', cash.ProjectLastDealDateViewSet, basename='pro-last-deal')  # only list
router.register(r'pr-date-cashbook', cash.ProjectDateCashBookViewSet, basename='pr-date-cashbook')  # only list
router.register(r'project-imprest', cash.ProjectImprestViewSet, basename='pr-imprest')  # only list

# contract
router.register(r'order-group', contract.OrderGroupViewSet)
router.register(r'document-type', contract.DocumentTypeViewSet)
router.register(r'required-docs', contract.RequiredDocumentViewSet)
router.register(r'contract', contract.ContractViewSet)
router.register(r'contract-set', contract.ContractSetViewSet, basename='cont-set')
router.register(r'simple-contract', contract.SimpleContractViewSet, basename='simple-contract')
router.register(r'cont-price', contract.ContractPriceViewSet)
router.register(r'subs-sum', contract.SubsSummaryViewSet, basename='subs-sum')  # only list
router.register(r'cont-sum', contract.ContSummaryViewSet, basename='cont-sum')  # only list
router.register(r'contractor', contract.ContractorViewSet)
router.register(r'contract-file', contract.ContractFileViewSet)
router.register(r'contract-docs', contract.ContractDocumentViewSet)
router.register(r'contract-docs-file', contract.ContractDocumentFileViewSet)
router.register(r'contractor-address', contract.ContAddressViewSet)
router.register(r'contractor-contact', contract.ContContactViewSet)
router.register(r'contractor-consultations', contract.ContractorConsultationLogsViewSet)
router.register(r'succession', contract.SuccessionViewSet)
router.register(r'contractor-release', contract.ContReleaseViewSet)

# notice
router.register(r'sales-bill-issue', notice.BillIssueViewSet)
router.register(r'messages', notice.MessageViewSet, basename='messages')
router.register(r'registered-sender-numbers', notice.RegisteredSenderNumberViewSet)
router.register(r'message-templates', notice.MessageTemplateViewSet)
router.register(r'message-send-history', notice.MessageSendHistoryViewSet)

# board
router.register(r'board', board.BoardViewSet)
router.register(r'post-category', board.CategoryViewSet)
router.register(r'post', board.PostViewSet, basename='post')
router.register(r'post-like', board.PostLikeViewSet, basename='post-like')
router.register(r'post-blame', board.PostBlameViewSet, basename='post-blame')
router.register(r'post-link', board.PostLinkViewSet)
router.register(r'post-file', board.PostFileViewSet)
router.register(r'post-image', board.PostImageViewSet)
router.register(r'comment', board.CommentViewSet)
router.register(r'comment-like', board.CommentLikeViewSet, basename='comment-like')
router.register(r'comment-blame', board.CommentBlameViewSet, basename='comment-blame')
router.register(r'tag', board.TagViewSet)
router.register(r'post-trash-can', board.PostInTrashViewSet, basename='post-trash-can')

# docs
router.register(r'doc-type', docs.DocTypeViewSet)
router.register(r'category', docs.CategoryViewSet)
router.register(r'suitcase', docs.LawSuitCaseViewSet)
router.register(r'all-suitcase', docs.AllLawSuitCaseViewSet, basename='all-suitcase')
router.register(r'docs', docs.DocumentViewSet, basename='docs')
router.register(r'link', docs.LinkViewSet)
router.register(r'file', docs.FileViewSet)
router.register(r'image', docs.ImageViewSet)
router.register(r'docs-trash-can', docs.DocsInTrashViewSet, basename='docs-trash-can')

urlpatterns = router.urls
urlpatterns += [path('cont-aggregate/<int:project_id>/', contract.ContractAggreateView.as_view(),
                     name='cont-aggregate')]

# Contract price bulk update APIs
urlpatterns += [path('contract-bulk-price-update/', contract.bulk_update_contract_prices,
                     name='contract-bulk-price-update')]
urlpatterns += [path('contract-price-update-preview/', contract.contract_price_update_preview,
                     name='contract-price-update-preview')]
urlpatterns += [path('issue-by-member/', work.IssueCountByMemberView.as_view(), name='issue-by-member')]
urlpatterns += [path('admin-create-user/', accounts.AdminCreateUserView.as_view(), name='admin-create-user')]
urlpatterns += [path('check-password/', accounts.CheckPasswordView.as_view(), name='check-password')]
urlpatterns += [path('change-password/', accounts.ChangePasswordView.as_view(), name='change-password')]
urlpatterns += [path('password-reset/', accounts.PasswordResetRequestView.as_view(), name='password-reset')]
urlpatterns += [path('password-reset-confirm/<str:user_id>/<str:token>/', accounts.PasswordResetConfirmView.as_view(),
                     name='password-reset-confirm')]
urlpatterns += [path('post/<int:pk>/copy/', board.PostViewSet.as_view({'post': 'copy_and_create'}), name='post-copy')]
urlpatterns += [path('docs/<int:pk>/copy/', docs.DocumentViewSet.as_view({'docs': 'copy_and_create'}),
                     name='docs-copy')]

# github custom api
urlpatterns += [path('repo/<int:pk>/', work.GitRepoApiView.as_view(), name='git-repo')]
urlpatterns += [path('repo/<int:pk>/branches/', work.GitBranchesView.as_view(), name='git-branches')]
urlpatterns += [path('repo/<int:pk>/tags/', work.GitTagsView.as_view(), name='git-tags')]
urlpatterns += [path('repo/<int:pk>/tree/', work.GitTreeView.as_view(), name='git-root-tree')]
urlpatterns += [path('repo/<int:pk>/tree/<path:path>', work.GitTreeView.as_view(), name='git-sub-tree')]
urlpatterns += [path('repo/<int:pk>/file/<path:path>', work.GitFileContentView.as_view(), name='git-file')]
urlpatterns += [path('repo/<int:pk>/compare/', work.CompareCommitsView.as_view(), name='compare-commits')]
urlpatterns += [path('repo/<int:pk>/changed/', work.GetChangedFilesView.as_view(), name='get-changed-files')]
