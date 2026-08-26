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
        int totalSales = 0;
        int totalPaid = 0;
        int totalUnpaid = 0;

        for (final item in list) {
          if (item is Map) {
            totalSales += (item['total_budget'] ?? 0) as int;
            totalPaid += (item['total_paid_amount'] ?? 0) as int;
            totalUnpaid += (item['unpaid_amount'] ?? 0) as int;
          }
        }

        final rate = totalSales > 0 ? (totalPaid / totalSales) * 100 : 0.0;

        return PaymentOverallAggregateModel(
          totalSalesPrice: totalSales,
          totalPaidAmount: totalPaid,
          totalUnpaidAmount: totalUnpaid,
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
}
