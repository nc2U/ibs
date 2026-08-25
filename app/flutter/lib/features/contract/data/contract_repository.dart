import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/dio_provider.dart';
import 'models/contract_models.dart';

final contractRepositoryProvider = Provider<ContractRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return ContractRepository(dio: dio);
});

class ContractRepository {
  final Dio dio;

  ContractRepository({required this.dio});

  /// 1. 프로젝트 계약 집계 현황 조회 (/api/v1/contract-aggregate/{projectId}/)
  Future<ContractAggregateModel> fetchContractAggregate(int projectId) async {
    try {
      final response = await dio.get('/api/v1/contract-aggregate/$projectId/');
      return ContractAggregateModel.fromJson(response.data);
    } catch (e) {
      return ContractAggregateModel(
        totalUnits: 0,
        subsNum: 0,
        contsNum: 0,
        nonContsNum: 0,
      );
    }
  }

  /// 2. 프로젝트 계약 목록 조회 (/api/v1/contract-set/?project={projectId}&search={search})
  Future<List<ContractItemModel>> fetchContracts({
    required int projectId,
    String? search,
    String? status,
    int? orderGroup,
    int? unitType,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'project': projectId,
        'limit': 100, // 모바일 목록 100건 우선 로드
      };
      if (search != null && search.trim().isNotEmpty) {
        queryParams['search'] = search.trim();
      }
      if (status != null && status.isNotEmpty) {
        queryParams['contractor__status'] = status;
      }
      if (orderGroup != null) {
        queryParams['order_group'] = orderGroup;
      }
      if (unitType != null) {
        queryParams['unit_type'] = unitType;
      }

      final response = await dio.get(
        '/api/v1/contract-set/',
        queryParameters: queryParams,
      );

      final List<dynamic> results =
          response.data is Map && response.data.containsKey('results')
              ? response.data['results']
              : (response.data is List ? response.data : []);

      return results.map((json) => ContractItemModel.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }
}
