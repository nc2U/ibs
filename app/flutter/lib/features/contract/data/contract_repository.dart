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

  /// 2. 유효 계약 목록 조회 (/api/v1/contract-set/?project={projectId}&is_active=true&is_contract=true)
  Future<List<ContractItemModel>> fetchContracts({
    required int projectId,
    String? search,
    int? orderGroup,
    int? unitType,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'project': projectId,
        'is_active': true,
        'is_contract': true, // 계약자('2') 및 변경처리중('3') 유효 계약만 조회
        'limit': 100,
      };
      if (search != null && search.trim().isNotEmpty) {
        queryParams['search'] = search.trim();
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

  /// 3. 권리의무 승계 목록 조회 (/api/v1/succession/?contract__project={projectId})
  Future<List<SuccessionItemModel>> fetchSuccessions({
    required int projectId,
    String? search,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'contract__project': projectId,
        'limit': 100,
      };
      if (search != null && search.trim().isNotEmpty) {
        queryParams['search'] = search.trim();
      }

      final response = await dio.get(
        '/api/v1/succession/',
        queryParameters: queryParams,
      );

      final List<dynamic> results =
          response.data is Map && response.data.containsKey('results')
              ? response.data['results']
              : (response.data is List ? response.data : []);

      return results.map((json) => SuccessionItemModel.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }

  /// 4. 계약 해약/해지 목록 조회 (/api/v1/contractor-release/?project={projectId})
  Future<List<ContractorReleaseItemModel>> fetchReleases({
    required int projectId,
    String? search,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'project': projectId,
        'limit': 100,
      };
      if (search != null && search.trim().isNotEmpty) {
        queryParams['search'] = search.trim();
      }

      final response = await dio.get(
        '/api/v1/contractor-release/',
        queryParameters: queryParams,
      );

      final List<dynamic> results =
          response.data is Map && response.data.containsKey('results')
              ? response.data['results']
              : (response.data is List ? response.data : []);

      return results
          .map((json) => ContractorReleaseItemModel.fromJson(json))
          .toList();
    } catch (e) {
      return [];
    }
  }
}
