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

  /// 2. 프로젝트 거래 전표 목록 조회 (/api/v1/ledger/project-transaction/?project={projectId}&page={page})
  Future<List<ProjectTransactionItemModel>> fetchProjectTransactions({
    required int projectId,
    String? search,
    String? sort,
    int? bankAccount,
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

  /// 4. 회계 자금 총괄 KPI 계산
  Future<LedgerOverallAggregateModel?> fetchLedgerAggregate(int projectId) async {
    try {
      final balances = await fetchBalanceByAccount(projectId);
      if (balances.isEmpty) return null;

      int totalBalance = 0;
      int totalIncome = 0;
      int totalExpense = 0;

      for (final item in balances) {
        totalBalance += item.balance;
        totalIncome += item.incSum;
        totalExpense += item.outSum;
      }

      return LedgerOverallAggregateModel(
        totalBalance: totalBalance,
        totalIncome: totalIncome,
        totalExpense: totalExpense,
        currentBalance: totalIncome - totalExpense,
      );
    } catch (e) {
      return null;
    }
  }
}
