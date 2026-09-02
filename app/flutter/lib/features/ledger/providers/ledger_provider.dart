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

/// 날짜 범위 프리셋 (전체, 오늘, 이번달, 지난달, 최근3개월, 올해, 직접입력)
enum LedgerDatePreset {
  all,         // 전체 기간
  today,       // 오늘
  thisMonth,   // 이번 달
  lastMonth,   // 지난 달
  last3Months, // 최근 3개월
  thisYear,    // 올해
  custom,      // 직접 지정
}

/// 날짜 프리셋 상태
final ledgerDatePresetProvider =
    StateProvider<LedgerDatePreset>((ref) => LedgerDatePreset.all);

/// 시작일자 필터 (YYYY-MM-DD)
final ledgerFromDateFilterProvider = StateProvider<String?>((ref) => null);

/// 종료일자 필터 (YYYY-MM-DD)
final ledgerToDateFilterProvider = StateProvider<String?>((ref) => null);

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
    final fromDate = ref.read(ledgerFromDateFilterProvider);
    final toDate = ref.read(ledgerToDateFilterProvider);
    final repository = ref.read(ledgerRepositoryProvider);

    try {
      final items = await repository.fetchProjectTransactions(
        projectId: selectedProject.realProjectId,
        search: search,
        sort: sort,
        bankAccount: bankAcc,
        fromDate: fromDate,
        toDate: toDate,
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
    final fromDate = ref.read(ledgerFromDateFilterProvider);
    final toDate = ref.read(ledgerToDateFilterProvider);
    final repository = ref.read(ledgerRepositoryProvider);

    try {
      final newItems = await repository.fetchProjectTransactions(
        projectId: selectedProject.realProjectId,
        search: search,
        sort: sort,
        bankAccount: bankAcc,
        fromDate: fromDate,
        toDate: toDate,
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

/// 📊 최근 6개월 월별 캐시플로우(수입/지출/수지차) 집계 프로바이더
final monthlyCashflowChartProvider =
    FutureProvider<List<MonthlyCashflowItemModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final repository = ref.watch(ledgerRepositoryProvider);
  final now = DateTime.now();

  // 최근 6개월 범위 계산 (현재 월 포함 6개월)
  final sixMonthsAgo = DateTime(now.year, now.month - 5, 1);
  final fromDate = '${sixMonthsAgo.year}-${sixMonthsAgo.month.toString().padLeft(2, '0')}-01';
  final lastDayOfThisMonth = DateTime(now.year, now.month + 1, 0).day;
  final toDate = '${now.year}-${now.month.toString().padLeft(2, '0')}-${lastDayOfThisMonth.toString().padLeft(2, '0')}';

  // 최근 6개월 전체 거래 조회 (최대 500건)
  final transactions = await repository.fetchProjectTransactions(
    projectId: selectedProject.realProjectId,
    fromDate: fromDate,
    toDate: toDate,
    limit: 500,
  );

  // 6개월 월별 버킷 초기화
  final Map<String, MonthlyCashflowItemModel> monthlyMap = {};
  for (int i = 5; i >= 0; i--) {
    final d = DateTime(now.year, now.month - i, 1);
    final ym = '${d.year}-${d.month.toString().padLeft(2, '0')}';
    final label = '${d.month}월';
    monthlyMap[ym] = MonthlyCashflowItemModel(
      monthLabel: label,
      yearMonth: ym,
      income: 0,
      expense: 0,
      balance: 0,
    );
  }

  // 거래 금액 누적
  for (final tx in transactions) {
    if (tx.dealDate.length >= 7) {
      final ym = tx.dealDate.substring(0, 7);
      if (monthlyMap.containsKey(ym)) {
        final current = monthlyMap[ym]!;
        int inc = current.income;
        int exp = current.expense;
        if (tx.sort == '1') {
          inc += tx.amount;
        } else if (tx.sort == '2') {
          exp += tx.amount;
        }
        monthlyMap[ym] = MonthlyCashflowItemModel(
          monthLabel: current.monthLabel,
          yearMonth: ym,
          income: inc,
          expense: exp,
          balance: inc - exp,
        );
      }
    }
  }

  return monthlyMap.values.toList();
});

