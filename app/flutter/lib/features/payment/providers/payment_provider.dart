import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../contract/data/models/contract_models.dart';
import '../../contract/providers/contract_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../data/models/payment_models.dart';
import '../data/payment_repository.dart';

/// 3대 서브 탭 구분 enum (납부 내역 목록, 계약건별 납부내역, 회차별 납부현황)
enum PaymentSubTab {
  transactions, // 💰 납부 내역 목록 (입금 건별)
  byContract,   // 📋 계약건별 납부내역 (동호수/계약자별 종합)
  byInstallment // 📊 회차별 납부 현황 (차수/회차별 집계)
}

/// 현재 선택된 서브 탭 프로바이더
final paymentCurrentSubTabProvider =
    StateProvider<PaymentSubTab>((ref) => PaymentSubTab.transactions);

/// 검색어 상태 프로바이더
final paymentSearchQueryProvider = StateProvider<String>((ref) => '');

/// 매칭 상태 필터 enum (전체, 계약 미매칭, 회차 미매칭)
enum PaymentMatchFilter {
  all,          // 전체
  noContract,   // 계약 미매칭
  noInstall,    // 회차 미매칭
}

/// 현재 선택된 매칭 필터 프로바이더
final paymentMatchFilterProvider =
    StateProvider<PaymentMatchFilter>((ref) => PaymentMatchFilter.all);

/// 계약건별 납부 탭에서 현재 선택된 계약건 프로바이더
final selectedContractForPaymentProvider =
    StateProvider<ContractItemModel?>((ref) => null);

/// 선택된 계약건의 전체 수납 내역 조회 프로바이더
final paymentsByContractProvider =
    FutureProvider.autoDispose<List<PaymentTransactionItemModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  final selectedContract = ref.watch(selectedContractForPaymentProvider);

  if (selectedProject == null || selectedContract == null) {
    return [];
  }

  final repository = ref.watch(paymentRepositoryProvider);
  return repository.fetchPaymentsByContract(
    projectId: selectedProject.realProjectId,
    contractId: selectedContract.pk,
  );
});

/// 수납 총괄 KPI 집계 프로바이더
final paymentOverallAggregateProvider =
    FutureProvider<PaymentOverallAggregateModel?>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return null;

  final repository = ref.watch(paymentRepositoryProvider);
  return repository.fetchOverallAggregate(selectedProject.realProjectId);
});

/// 📑 프로젝트 고지서 발행 설정 프로바이더
final salesBillIssueProvider = FutureProvider.autoDispose<SalesBillIssueModel?>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return null;
  final repository = ref.watch(paymentRepositoryProvider);
  return repository.fetchSalesBillIssue(selectedProject.realProjectId);
});

/// ── 1. 개별 납부 거래 내역 무한 스크롤 상태 Notifier ──────────────────────
class PaymentTransactionsState {
  final List<PaymentTransactionItemModel> items;
  final int page;
  final bool isLoading;
  final bool isFetchingNextPage;
  final bool hasMore;
  final String? error;

  const PaymentTransactionsState({
    this.items = const [],
    this.page = 1,
    this.isLoading = false,
    this.isFetchingNextPage = false,
    this.hasMore = true,
    this.error,
  });

  PaymentTransactionsState copyWith({
    List<PaymentTransactionItemModel>? items,
    int? page,
    bool? isLoading,
    bool? isFetchingNextPage,
    bool? hasMore,
    String? error,
  }) {
    return PaymentTransactionsState(
      items: items ?? this.items,
      page: page ?? this.page,
      isLoading: isLoading ?? this.isLoading,
      isFetchingNextPage: isFetchingNextPage ?? this.isFetchingNextPage,
      hasMore: hasMore ?? this.hasMore,
      error: error,
    );
  }
}

class PaymentTransactionsNotifier extends StateNotifier<PaymentTransactionsState> {
  final Ref ref;

  PaymentTransactionsNotifier(this.ref) : super(const PaymentTransactionsState()) {
    fetchInitial();
  }

  Future<void> fetchInitial() async {
    final selectedProject = ref.read(selectedRealEstateProjectProvider);
    if (selectedProject == null) {
      state = const PaymentTransactionsState(items: [], hasMore: false);
      return;
    }

    state = state.copyWith(isLoading: true, page: 1, items: [], hasMore: true, error: null);

    final search = ref.read(paymentSearchQueryProvider);
    final matchFilter = ref.read(paymentMatchFilterProvider);
    final repository = ref.read(paymentRepositoryProvider);

    try {
      final items = await repository.fetchPaymentTransactions(
        projectId: selectedProject.realProjectId,
        search: search,
        noContract: matchFilter == PaymentMatchFilter.noContract ? true : null,
        noInstall: matchFilter == PaymentMatchFilter.noInstall ? true : null,
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
    final search = ref.read(paymentSearchQueryProvider);
    final matchFilter = ref.read(paymentMatchFilterProvider);
    final repository = ref.read(paymentRepositoryProvider);

    try {
      final newItems = await repository.fetchPaymentTransactions(
        projectId: selectedProject.realProjectId,
        search: search,
        noContract: matchFilter == PaymentMatchFilter.noContract ? true : null,
        noInstall: matchFilter == PaymentMatchFilter.noInstall ? true : null,
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

  /// 계약/회차 매칭 실행 후 목록 새로고침
  Future<bool> matchPayment({
    required int paymentPk,
    int? contractId,
    int? installmentOrderId,
    int? bankTransactionId,
    int? accountingEntryId,
  }) async {
    final repository = ref.read(paymentRepositoryProvider);
    final success = await repository.updateContractPayment(
      paymentPk: paymentPk,
      contractId: contractId,
      installmentOrderId: installmentOrderId,
      bankTransactionId: bankTransactionId,
      accountingEntryId: accountingEntryId,
    );

    if (success) {
      // 목록 및 집계 갱신
      fetchInitial();
      ref.invalidate(paymentOverallAggregateProvider);
      ref.invalidate(installmentStatusListProvider);
      ref.invalidate(paymentsByContractProvider);
      ref.invalidate(validContractListProvider);
    }
    return success;
  }
}

final paymentTransactionsProvider =
    StateNotifierProvider<PaymentTransactionsNotifier, PaymentTransactionsState>(
        (ref) => PaymentTransactionsNotifier(ref));

/// ── 2. 회차별 수납 현황 목록 프로바이더 ─────────────────────────────────────
final installmentStatusListProvider =
    FutureProvider<List<InstallmentStatusItemModel>>((ref) async {
  final selectedProject = ref.watch(selectedRealEstateProjectProvider);
  if (selectedProject == null) return [];

  final repository = ref.watch(paymentRepositoryProvider);
  return repository.fetchInstallmentStatusList(selectedProject.realProjectId);
});
