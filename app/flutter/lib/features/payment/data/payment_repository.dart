import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/dio_provider.dart';
import 'models/payment_models.dart';

final paymentRepositoryProvider = Provider<PaymentRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return PaymentRepository(dio: dio);
});

/// 대금 수납 관리 Repository
class PaymentRepository {
  final Dio dio;

  PaymentRepository({required this.dio});

  /// 1. 수납 총괄 KPI 집계 조회 (/api/v1/ledger/payment-summary/?project={projectId})
  Future<PaymentOverallAggregateModel?> fetchOverallAggregate(int projectId) async {
    try {
      final response = await dio.get(
        '/api/v1/ledger/payment-summary/',
        queryParameters: {'project': projectId},
      );

      if (response.data is List) {
        final List<dynamic> list = response.data;
        int totalBudget = 0;
        int totalContractAmt = 0;
        int totalPaid = 0;
        int totalUnpaid = 0;
        int totalUnsold = 0;

        for (final item in list) {
          if (item is Map) {
            totalBudget += (item['total_budget'] ?? 0) as int;
            totalContractAmt += (item['total_contract_amount'] ?? 0) as int;
            totalPaid += (item['total_paid_amount'] ?? 0) as int;
            totalUnpaid += (item['unpaid_amount'] ?? 0) as int;
            totalUnsold += (item['unsold_amount'] ?? 0) as int;
          }
        }

        // unsold_amount가 API에 없을 경우 보정
        if (totalUnsold == 0 && totalBudget > totalContractAmt) {
          totalUnsold = totalBudget - totalContractAmt;
        }
        // unpaid_amount가 API에 없을 경우 보정
        if (totalUnpaid == 0 && totalContractAmt > totalPaid) {
          totalUnpaid = totalContractAmt - totalPaid;
        }

        final rate = totalContractAmt > 0 ? (totalPaid / totalContractAmt) * 100 : 0.0;

        return PaymentOverallAggregateModel(
          totalBudget: totalBudget,
          totalContractAmount: totalContractAmt,
          totalPaidAmount: totalPaid,
          totalUnpaidAmount: totalUnpaid,
          unsoldAmount: totalUnsold,
          paymentRate: rate,
          totalUnits: 0,
          contractedUnits: 0,
        );
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  /// 2. 개별 납부 거래 내역 목록 조회 (/api/v1/ledger/payment/?project={projectId}&limit=10&page={page})
  Future<List<PaymentTransactionItemModel>> fetchPaymentTransactions({
    required int projectId,
    String? search,
    int? installmentOrder,
    bool? noContract,
    bool? noInstall,
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
      if (installmentOrder != null) {
        queryParams['installment_order'] = installmentOrder;
      }
      if (noContract == true) {
        queryParams['no_contract'] = 'true';
      }
      if (noInstall == true) {
        queryParams['no_install'] = 'true';
      }

      final response = await dio.get(
        '/api/v1/ledger/payment/',
        queryParameters: queryParams,
      );

      final List<dynamic> results =
          response.data is Map && response.data.containsKey('results')
              ? response.data['results']
              : (response.data is List ? response.data : []);

      return results
          .map((json) => PaymentTransactionItemModel.fromJson(json))
          .toList();
    } catch (e) {
      return [];
    }
  }

  /// 3. 회차별 수납 현황 목록 조회 (/api/v1/ledger/overall-summary/?project={projectId})
  Future<List<InstallmentStatusItemModel>> fetchInstallmentStatusList(int projectId) async {
    try {
      final response = await dio.get(
        '/api/v1/ledger/overall-summary/',
        queryParameters: {'project': projectId},
      );

      if (response.data is Map && response.data.containsKey('pay_orders')) {
        final List<dynamic> list = response.data['pay_orders'];
        return list.map((json) => InstallmentStatusItemModel.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  /// 4. 유효 계약건 실시간 검색 (/api/v1/contract-set/?project={projectId}&search={query}&is_active=true&is_contract=true)
  Future<List<Map<String, dynamic>>> searchContracts({
    required int projectId,
    required String query,
    int limit = 20,
  }) async {
    try {
      final response = await dio.get(
        '/api/v1/contract-set/',
        queryParameters: {
          'project': projectId,
          'search': query.trim(),
          'is_active': true,
          'is_contract': true,
          'limit': limit,
        },
      );

      final List<dynamic> results =
          response.data is Map && response.data.containsKey('results')
              ? response.data['results']
              : (response.data is List ? response.data : []);

      return results.cast<Map<String, dynamic>>();
    } catch (e) {
      return [];
    }
  }

  /// 5. 계약 및 납부회차 매칭 업데이트 (PATCH /api/v1/ledger/payment/{paymentPk}/)
  Future<bool> updateContractPayment({
    required int paymentPk,
    int? contractId,
    int? installmentOrderId,
    int? bankTransactionId,
    int? accountingEntryId,
  }) async {
    try {
      // 1순위: 복합 거래 수정이 필요한 경우 (bankTransactionId + accountingEntryId가 있을 때 웹 방식과 완벽 호환)
      if (bankTransactionId != null && accountingEntryId != null) {
        final patchData = <String, dynamic>{
          'accounting_entries': [
            {
              'pk': accountingEntryId,
              if (contractId != null) 'contract': contractId,
              if (installmentOrderId != null) 'installment_order': installmentOrderId,
            }
          ]
        };
        await dio.patch(
          '/api/v1/ledger/project-composite-transaction/$bankTransactionId/',
          data: patchData,
        );
        return true;
      }

      // 2순위: ContractPayment 직접 PATCH
      final data = <String, dynamic>{};
      if (contractId != null) data['contract'] = contractId;
      if (installmentOrderId != null) data['installment_order'] = installmentOrderId;

      if (data.isNotEmpty) {
        await dio.patch(
          '/api/v1/ledger/payment/$paymentPk/',
          data: data,
        );
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }
}
