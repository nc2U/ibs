import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/project_provider.dart';
import '../data/ledger_repository.dart';
import '../data/models/ledger_models.dart';

/// 3대 서브 탭 구분 enum (출납 전표 목록, 계좌별 잔액 현황, 전도금 정산)
enum LedgerSubTab {
  transactions, // 💳 입출금 출납내역
  balanceStatus, // 🏦 계좌별 잔액현황
  imprest,      // 💼 현장 전도금 관리
}

/// 현재 선택된 서브 탭
final ledgerCurrentSubTabProvider =
    StateProvider<LedgerSubTab>((ref) => LedgerSubTab.transactions);

/// 검색어 상태
final ledgerSearchQueryProvider = StateProvider<String>((ref) => '');

/// 거래 구분 필터 (전체 '', '1': 수입, '2': 지출, '3': 대체)
final ledgerSortFilterProvider = StateProvider<String>((ref) => '');

/// 계좌 필터 (선택된 계좌 ID)
final ledgerSelectedBankAccFilterProvider = StateProvider<int?>((ref) => null);

/// 프로젝트 은행 계좌 목록 프로바이더
final projectBankAccountsProvider =
    FutureProvider<List<ProjectBankAccountModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final repository = ref.watch(ledgerRepositoryProvider);
  return repository.fetchProjectBankAccounts(selectedProject.realProjectId);
});

/// 자금 총괄 KPI 집계 프로바이더
final ledgerOverallAggregateProvider =
    FutureProvider<LedgerOverallAggregateModel?>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return null;

  final repository = ref.watch(ledgerRepositoryProvider);
  return repository.fetchLedgerAggregate(selectedProject.realProjectId);
});

/// 계좌별 잔액 현황 목록 프로바이더
final ledgerBalanceByAccountProvider =
    FutureProvider<List<ProjectBalanceByAccountModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final repository = ref.watch(ledgerRepositoryProvider);
  return repository.fetchBalanceByAccount(selectedProject.realProjectId);
});

/// ── 1. 프로젝트 거래 전표 무한 스크롤 Notifier ──────────────────────────────
class ProjectTransactionsState {
  final List<ProjectTransactionItemModel> items;
  final int page;
  final bool isLoading;
  final bool isFetchingNextPage;
  final bool hasMore;
  final String? error;

  const ProjectTransactionsState({
    this.items = const [],
    this.page = 1,
    this.isLoading = false,
    this.isFetchingNextPage = false,
    this.hasMore = true,
    this.error,
  });

  ProjectTransactionsState copyWith({
    List<ProjectTransactionItemModel>? items,
    int? page,
    bool? isLoading,
    bool? isFetchingNextPage,
    bool? hasMore,
    String? error,
  }) {
    return ProjectTransactionsState(
      items: items ?? this.items,
      page: page ?? this.page,
      isLoading: isLoading ?? this.isLoading,
      isFetchingNextPage: isFetchingNextPage ?? this.isFetchingNextPage,
      hasMore: hasMore ?? this.hasMore,
      error: error,
    );
  }
}

class ProjectTransactionsNotifier
    extends StateNotifier<ProjectTransactionsState> {
  final Ref ref;

  ProjectTransactionsNotifier(this.ref)
      : super(const ProjectTransactionsState()) {
    fetchInitial();
  }

  Future<void> fetchInitial() async {
    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) {
      state = const ProjectTransactionsState(items: [], hasMore: false);
      return;
    }

    state = state.copyWith(
        isLoading: true, page: 1, items: [], hasMore: true, error: null);

    final search = ref.read(ledgerSearchQueryProvider);
    final sort = ref.read(ledgerSortFilterProvider);
    final bankAcc = ref.read(ledgerSelectedBankAccFilterProvider);
    final repository = ref.read(ledgerRepositoryProvider);

    try {
      final items = await repository.fetchProjectTransactions(
        projectId: selectedProject.realProjectId,
        search: search,
        sort: sort,
        bankAccount: bankAcc,
        page: 1,
        limit: 10,
      );

      state = state.copyWith(
        isLoading: false,
        items: items,
        page: 1,
        hasMore: items.length >= 10,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> fetchNextPage() async {
    if (state.isLoading || state.isFetchingNextPage || !state.hasMore) return;

    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) return;

    state = state.copyWith(isFetchingNextPage: true);

    final nextPage = state.page + 1;
    final search = ref.read(ledgerSearchQueryProvider);
    final sort = ref.read(ledgerSortFilterProvider);
    final bankAcc = ref.read(ledgerSelectedBankAccFilterProvider);
    final repository = ref.read(ledgerRepositoryProvider);

    try {
      final newItems = await repository.fetchProjectTransactions(
        projectId: selectedProject.realProjectId,
        search: search,
        sort: sort,
        bankAccount: bankAcc,
        page: nextPage,
        limit: 10,
      );

      state = state.copyWith(
        isFetchingNextPage: false,
        items: [...state.items, ...newItems],
        page: nextPage,
        hasMore: newItems.length >= 10,
      );
    } catch (e) {
      state = state.copyWith(isFetchingNextPage: false);
    }
  }
}

final projectTransactionsProvider = StateNotifierProvider<
    ProjectTransactionsNotifier, ProjectTransactionsState>(
  (ref) => ProjectTransactionsNotifier(ref),
);
