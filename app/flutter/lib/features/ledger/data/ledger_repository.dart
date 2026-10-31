import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/dio_provider.dart';
import 'models/ledger_models.dart';

final ledgerRepositoryProvider = Provider<LedgerRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return LedgerRepository(dio: dio);
});

/// 회계 자금 관리 Repository
class LedgerRepository {
  final Dio dio;

  LedgerRepository({required this.dio});

  /// 1. 프로젝트 은행 계좌 목록 조회 (/api/v1/ledger/project-bank-account/?project={projectId})
  Future<List<ProjectBankAccountModel>> fetchProjectBankAccounts(int projectId) async {
    try {
      final response = await dio.get(
        '/api/v1/ledger/project-bank-account/',
        queryParameters: {'project': projectId, 'is_hide': false, 'inactive': false, 'limit': 500},
      );
      final List<dynamic> results = response.data is Map && response.data.containsKey('results')
          ? response.data['results']
          : (response.data is List ? response.data : []);
      return results.map((json) => ProjectBankAccountModel.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }

  /// 1-2. 프로젝트 거래 전표 적요 및 비고(프로젝트 메모) 수정 (PATCH)
  Future<bool> updateTransactionNoteAndContent({
    required int pk,
    String? content,
    String? note,
  }) async {
    try {
      final data = <String, dynamic>{};
      if (content != null) data['content'] = content;
      if (note != null) data['note'] = note;

      final response = await dio.patch(
        '/api/v1/ledger/project-transaction/$pk/',
        data: data,
      );
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  /// 2. 프로젝트 거래 전표 페이지 조회 (/api/v1/ledger/project-transaction/?project={projectId}&page={page})
  Future<ProjectTransactionPageResult> fetchProjectTransactionsPage({
    required int projectId,
    String? search,
    String? sort,
    int? bankAccount,
    String? fromDate,
    String? toDate,
    int page = 1,
    int limit = 10,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'project': projectId,
        'page': page,
        'limit': limit,
      };
      if (search != null && search.trim().isNotEmpty) {
        queryParams['search'] = search.trim();
      }
      if (sort != null && sort.isNotEmpty) {
        queryParams['sort'] = sort;
      }
      if (bankAccount != null) {
        queryParams['bank_account'] = bankAccount;
      }
      if (fromDate != null && fromDate.isNotEmpty) {
        queryParams['from_date'] = fromDate;
      }
      if (toDate != null && toDate.isNotEmpty) {
        queryParams['to_date'] = toDate;
      }

      final response = await dio.get(
        '/api/v1/ledger/project-transaction/',
        queryParameters: queryParams,
      );

      final data = response.data;
      final List<dynamic> results = data is Map && data.containsKey('results')
          ? data['results']
          : (data is List ? data : []);
      final items = results.map((json) => ProjectTransactionItemModel.fromJson(json)).toList();
      final bool hasMore = data is Map && data.containsKey('next')
          ? data['next'] != null
          : items.length >= limit;

      return ProjectTransactionPageResult(items: items, hasMore: hasMore);
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '출납 거래 내역을 불러오지 못했습니다.');
    }
  }

  /// 2-1. 프로젝트 거래 전표 목록 조회 (집계/차트용)
  Future<List<ProjectTransactionItemModel>> fetchProjectTransactions({
    required int projectId,
    String? search,
    String? sort,
    int? bankAccount,
    String? fromDate,
    String? toDate,
    int page = 1,
    int limit = 10,
  }) async {
    try {
      final res = await fetchProjectTransactionsPage(
        projectId: projectId,
        search: search,
        sort: sort,
        bankAccount: bankAccount,
        fromDate: fromDate,
        toDate: toDate,
        page: page,
        limit: limit,
      );
      return res.items;
    } catch (_) {
      return [];
    }
  }

  /// 2-2. 조건에 맞는 거래 전체 조회 (집계/차트용, 전 페이지 순회로 누락 방지)
  Future<List<ProjectTransactionItemModel>> fetchAllProjectTransactions({
    required int projectId,
    String? sort,
    String? fromDate,
    String? toDate,
    int pageSize = 1000,
    int maxPages = 20,
  }) async {
    final all = <ProjectTransactionItemModel>[];
    for (var page = 1; page <= maxPages; page++) {
      final res = await fetchProjectTransactionsPage(
        projectId: projectId,
        sort: sort,
        fromDate: fromDate,
        toDate: toDate,
        page: page,
        limit: pageSize,
      );
      all.addAll(res.items);
      if (!res.hasMore) break;
    }
    return all;
  }

  /// 3. 계좌별 잔액 현황 조회 (/api/v1/ledger/project-transaction/balance_by_account/?project={projectId})
  Future<List<ProjectBalanceByAccountModel>> fetchBalanceByAccount(int projectId) async {
    try {
      final response = await dio.get(
        '/api/v1/ledger/project-transaction/balance_by_account/',
        queryParameters: {'project': projectId},
      );

      if (response.data is List) {
        final List<dynamic> list = response.data;
        return list.map((json) => ProjectBalanceByAccountModel.fromJson(json)).toList();
      }
      return [];
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? '계좌별 잔액 현황을 불러오지 못했습니다.');
    }
  }

  /// 4. 회계 자금 총괄 KPI 계산 (100% 팩트 기반: 총 잔고액 | 당월 입금 | 당월 지출 | 당월 수지차)
  Future<LedgerOverallAggregateModel?> fetchLedgerAggregate(int projectId) async {
    try {
      final now = DateTime.now();
      final monthStr = '${now.year}-${now.month.toString().padLeft(2, '0')}';
      final lastDay = DateTime(now.year, now.month + 1, 0).day.toString().padLeft(2, '0');
      final fromDate = '$monthStr-01';
      final toDate = '$monthStr-$lastDay';

      // 1. 계좌별 잔액 조회 (모든 프로젝트 계좌 실시간 가용 잔액)
      final balancesFuture = fetchBalanceByAccount(projectId).catchError((_) => <ProjectBalanceByAccountModel>[]);

      // 2. 당월 입금 거래 내역 조회 (sort=1, 당월 일자 범위 지정)
      final monthIncomeFuture = fetchAllProjectTransactions(
        projectId: projectId,
        sort: '1',
        fromDate: fromDate,
        toDate: toDate,
      );

      // 3. 당월 출금 거래 내역 조회 (sort=2, 당월 일자 범위 지정)
      final monthExpenseFuture = fetchAllProjectTransactions(
        projectId: projectId,
        sort: '2',
        fromDate: fromDate,
        toDate: toDate,
      );

      final results = await Future.wait([
        balancesFuture,
        monthIncomeFuture,
        monthExpenseFuture,
      ]);

      final balances = results[0] as List<ProjectBalanceByAccountModel>;
      final incTransactions = results[1] as List<ProjectTransactionItemModel>;
      final expTransactions = results[2] as List<ProjectTransactionItemModel>;

      int totalBalance = 0;
      for (final item in balances) {
        totalBalance += item.balance;
      }

      // 당월(YYYY-MM)에 해당하는 실제 거래 금액만 필터링하여 합산
      int monthIncome = 0;
      for (final tx in incTransactions) {
        if (tx.dealDate.startsWith(monthStr)) {
          monthIncome += tx.amount;
        }
      }

      int monthExpense = 0;
      for (final tx in expTransactions) {
        if (tx.dealDate.startsWith(monthStr)) {
          monthExpense += tx.amount;
        }
      }

      return LedgerOverallAggregateModel(
        totalBalance: totalBalance,
        monthIncome: monthIncome,
        monthExpense: monthExpense,
        monthBalance: monthIncome - monthExpense,
      );
    } catch (e) {
      return null;
    }
  }
}
