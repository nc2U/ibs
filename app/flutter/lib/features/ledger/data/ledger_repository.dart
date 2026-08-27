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
        queryParameters: {'project': projectId, 'is_hide': false, 'inactive': false},
      );
      final List<dynamic> results = response.data is Map && response.data.containsKey('results')
          ? response.data['results']
          : (response.data is List ? response.data : []);
      return results.map((json) => ProjectBankAccountModel.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }

  /// 1-2. 프로젝트 거래 전표 적요 및 비고(현장 메모) 수정 (PATCH)
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

  /// 2. 프로젝트 거래 전표 목록 조회 (/api/v1/ledger/project-transaction/?project={projectId}&page={page})
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

      final List<dynamic> results = response.data is Map && response.data.containsKey('results')
          ? response.data['results']
          : (response.data is List ? response.data : []);

      return results.map((json) => ProjectTransactionItemModel.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
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
    } catch (e) {
      return [];
    }
  }

  /// 4. 회계 자금 총괄 KPI 계산 (100% 팩트 기반: 총 잔고액 | 당월 입금 | 당월 지출 | 당월 수지차)
  Future<LedgerOverallAggregateModel?> fetchLedgerAggregate(int projectId) async {
    try {
      final now = DateTime.now();
      final monthStr = '${now.year}-${now.month.toString().padLeft(2, '0')}';

      // 1. 계좌별 잔액 조회 (모든 프로젝트 계좌 실시간 가용 잔액)
      final balancesFuture = fetchBalanceByAccount(projectId);

      // 2. 당월 입금 거래 내역 조회 (sort=1)
      final monthIncomeFuture = fetchProjectTransactions(
        projectId: projectId,
        sort: '1',
        limit: 100,
      );

      // 3. 당월 출금 거래 내역 조회 (sort=2)
      final monthExpenseFuture = fetchProjectTransactions(
        projectId: projectId,
        sort: '2',
        limit: 100,
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

      // 만약 거래 목록에서 0건이고 balance_by_account에 당일 집계가 있으면 보정
      if (monthIncome == 0 && monthExpense == 0) {
        for (final item in balances) {
          monthIncome += item.dateInc;
          monthExpense += item.dateOut;
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
