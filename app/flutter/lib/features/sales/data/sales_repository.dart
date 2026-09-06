import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/dio_provider.dart';
import 'models/sales_models.dart';

final salesRepositoryProvider = Provider<SalesRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return SalesRepository(dio: dio);
});

/// 분양 대행 관리 API Repository
class SalesRepository {
  final Dio dio;

  SalesRepository({required this.dio});

  /// 1. 계약 영업 담당자 매핑 목록 조회 (/api/v1/sales-contract-agent/)
  Future<List<ContractSalesAgentModel>> fetchContractSalesAgents({
    required int projectId,
    String? search,
    int? teamId,
    int? salesPersonId,
    int limit = 500,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'contract__project': projectId,
        'limit': limit,
      };
      if (search != null && search.trim().isNotEmpty) {
        queryParams['search'] = search.trim();
      }
      if (teamId != null) {
        queryParams['team'] = teamId;
      }
      if (salesPersonId != null) {
        queryParams['sales_person'] = salesPersonId;
      }

      final response = await dio.get(
        '/api/v1/sales-contract-agent/',
        queryParameters: queryParams,
      );

      final data = response.data;
      final results = data is Map && data.containsKey('results')
          ? data['results'] as List<dynamic>
          : (data is List ? data : []);

      return results
          .map((item) => ContractSalesAgentModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      return [];
    }
  }

  /// 2. 프로젝트 전체 간단 계약 목록 조회 (/api/v1/simple-contract/)
  Future<List<SimpleContractOption>> fetchSimpleContracts(int projectId) async {
    try {
      final response = await dio.get(
        '/api/v1/simple-contract/',
        queryParameters: {
          'project': projectId,
          'limit': 1000,
        },
      );

      final data = response.data;
      final results = data is Map && data.containsKey('results')
          ? data['results'] as List<dynamic>
          : (data is List ? data : []);

      return results
          .map((item) => SimpleContractOption.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      return [];
    }
  }

  /// 3. 분양 대행사 목록 조회 (/api/v1/sales-agency/)
  Future<List<SalesAgencyModel>> fetchSalesAgencies(int projectId) async {
    try {
      final response = await dio.get(
        '/api/v1/sales-agency/',
        queryParameters: {
          'project': projectId,
          'limit': 100,
        },
      );

      final data = response.data;
      final results = data is Map && data.containsKey('results')
          ? data['results'] as List<dynamic>
          : (data is List ? data : []);

      return results
          .map((item) => SalesAgencyModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      return [];
    }
  }

  /// 4. 영업 조직 (팀/본부) 목록 조회 (/api/v1/sales-team/)
  Future<List<SalesTeamModel>> fetchSalesTeams(int projectId) async {
    try {
      final response = await dio.get(
        '/api/v1/sales-team/',
        queryParameters: {
          'agency__project': projectId,
          'limit': 100,
        },
      );

      final data = response.data;
      final results = data is Map && data.containsKey('results')
          ? data['results'] as List<dynamic>
          : (data is List ? data : []);

      return results
          .map((item) => SalesTeamModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      return [];
    }
  }

  /// 5. 영업 인력 (상담사/팀장/본부장) 목록 조회 (/api/v1/sales-person/)
  Future<List<SalesPersonModel>> fetchSalesPersons({
    required int projectId,
    int? teamId,
    String? status,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'team__agency__project': projectId,
        'limit': 300,
      };
      if (teamId != null) {
        queryParams['team'] = teamId;
      }
      if (status != null && status.isNotEmpty) {
        queryParams['status'] = status;
      }

      final response = await dio.get(
        '/api/v1/sales-person/',
        queryParameters: queryParams,
      );

      final data = response.data;
      final results = data is Map && data.containsKey('results')
          ? data['results'] as List<dynamic>
          : (data is List ? data : []);

      return results
          .map((item) => SalesPersonModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      return [];
    }
  }

  /// 6. 수수료 정책 목록 조회 (/api/v1/sales-policy/)
  Future<List<CommissionPolicyModel>> fetchCommissionPolicies(int projectId) async {
    try {
      final response = await dio.get(
        '/api/v1/sales-policy/',
        queryParameters: {
          'project': projectId,
          'is_active': true,
          'limit': 100,
        },
      );

      final data = response.data;
      final results = data is Map && data.containsKey('results')
          ? data['results'] as List<dynamic>
          : (data is List ? data : []);

      return results
          .map((item) => CommissionPolicyModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      return [];
    }
  }

  /// 6. 계약 영업 담당자 배정 등록 (POST /api/v1/sales-contract-agent/)
  Future<ContractSalesAgentModel> createContractSalesAgent(
    Map<String, dynamic> payload,
  ) async {
    final response = await dio.post(
      '/api/v1/sales-contract-agent/',
      data: payload,
    );
    return ContractSalesAgentModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// 7. 계약 영업 담당자 매핑 수정 (PATCH /api/v1/sales-contract-agent/{id}/)
  Future<ContractSalesAgentModel> updateContractSalesAgent(
    int id,
    Map<String, dynamic> payload,
  ) async {
    final response = await dio.patch(
      '/api/v1/sales-contract-agent/$id/',
      data: payload,
    );
    return ContractSalesAgentModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// 8. 계약 영업 담당자 매핑 삭제 (DELETE /api/v1/sales-contract-agent/{id}/)
  Future<void> deleteContractSalesAgent(int id) async {
    await dio.delete('/api/v1/sales-contract-agent/$id/');
  }

  // ── 대행사 CRUD ──────────────────────────────────────────
  Future<SalesAgencyModel> createSalesAgency(Map<String, dynamic> payload) async {
    final response = await dio.post('/api/v1/sales-agency/', data: payload);
    return SalesAgencyModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<SalesAgencyModel> updateSalesAgency(int id, Map<String, dynamic> payload) async {
    final response = await dio.patch('/api/v1/sales-agency/$id/', data: payload);
    return SalesAgencyModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deleteSalesAgency(int id) async {
    await dio.delete('/api/v1/sales-agency/$id/');
  }

  // ── 영업 팀 CRUD ─────────────────────────────────────────
  Future<SalesTeamModel> createSalesTeam(Map<String, dynamic> payload) async {
    final response = await dio.post('/api/v1/sales-team/', data: payload);
    return SalesTeamModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<SalesTeamModel> updateSalesTeam(int id, Map<String, dynamic> payload) async {
    final response = await dio.patch('/api/v1/sales-team/$id/', data: payload);
    return SalesTeamModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deleteSalesTeam(int id) async {
    await dio.delete('/api/v1/sales-team/$id/');
  }

  // ── 영업 인력 CRUD ────────────────────────────────────────
  Future<SalesPersonModel> createSalesPerson(Map<String, dynamic> payload) async {
    final response = await dio.post('/api/v1/sales-person/', data: payload);
    return SalesPersonModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<SalesPersonModel> updateSalesPerson(int id, Map<String, dynamic> payload) async {
    final response = await dio.patch('/api/v1/sales-person/$id/', data: payload);
    return SalesPersonModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deleteSalesPerson(int id) async {
    await dio.delete('/api/v1/sales-person/$id/');
  }
}
