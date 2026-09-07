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
  Future<List<CommissionPolicyModel>> fetchCommissionPolicies(
    int projectId, {
    bool? isActive,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'project': projectId,
        'limit': 150,
      };
      if (isActive != null) {
        queryParams['is_active'] = isActive;
      }
      final response = await dio.get(
        '/api/v1/sales-policy/',
        queryParameters: queryParams,
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

  /// 6-1. 프로젝트 공급 차수 목록 조회 (/api/v1/order-group/)
  Future<List<OrderGroupOption>> fetchOrderGroups(int projectId) async {
    try {
      final response = await dio.get(
        '/api/v1/order-group/',
        queryParameters: {'project': projectId, 'limit': 100},
      );
      final data = response.data;
      final results = data is Map && data.containsKey('results')
          ? data['results'] as List<dynamic>
          : (data is List ? data : []);
      return results
          .map((item) => OrderGroupOption.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      return [];
    }
  }

  /// 6-2. 프로젝트 유니트 타입 목록 조회 (/api/v1/type/)
  Future<List<UnitTypeOption>> fetchUnitTypes(int projectId) async {
    try {
      final response = await dio.get(
        '/api/v1/type/',
        queryParameters: {'project': projectId, 'limit': 100},
      );
      final data = response.data;
      final results = data is Map && data.containsKey('results')
          ? data['results'] as List<dynamic>
          : (data is List ? data : []);
      return results
          .map((item) => UnitTypeOption.fromJson(item as Map<String, dynamic>))
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

  /// 8-1. 수수료 정산 승인 / 보류 상태 변경 (POST /api/v1/sales-contract-agent/{id}/toggle-approval/)
  Future<Map<String, dynamic>> toggleSettlementApproval(
    int id, {
    String? approvalNote,
    bool? isApproved,
  }) async {
    final payload = <String, dynamic>{};
    if (approvalNote != null) payload['approval_note'] = approvalNote;
    if (isApproved != null) payload['is_settlement_approved'] = isApproved;

    final response = await dio.post(
      '/api/v1/sales-contract-agent/$id/toggle-approval/',
      data: payload,
    );
    return response.data as Map<String, dynamic>;
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

  // ── 수수료 정책 CRUD ─────────────────────────────────────
  Future<CommissionPolicyModel> createCommissionPolicy(Map<String, dynamic> payload) async {
    final response = await dio.post('/api/v1/sales-policy/', data: payload);
    return CommissionPolicyModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<CommissionPolicyModel> updateCommissionPolicy(int id, Map<String, dynamic> payload) async {
    final response = await dio.patch('/api/v1/sales-policy/$id/', data: payload);
    return CommissionPolicyModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deleteCommissionPolicy(int id) async {
    await dio.delete('/api/v1/sales-policy/$id/');
  }

  // ── 수수료 정산 회차 CRUD & 액션 ────────────────────────
  Future<List<SettlementPeriodModel>> fetchSettlementPeriods(int projectId) async {
    try {
      final response = await dio.get(
        '/api/v1/sales-settlement-period/',
        queryParameters: {'project': projectId, 'limit': 100},
      );
      final data = response.data;
      final results = data is Map && data.containsKey('results')
          ? data['results'] as List<dynamic>
          : (data is List ? data : []);
      return results
          .map((item) => SettlementPeriodModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      return [];
    }
  }

  Future<SettlementPeriodModel> createSettlementPeriod(Map<String, dynamic> payload) async {
    final response = await dio.post('/api/v1/sales-settlement-period/', data: payload);
    return SettlementPeriodModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<SettlementPeriodModel> updateSettlementPeriod(int id, Map<String, dynamic> payload) async {
    final response = await dio.patch('/api/v1/sales-settlement-period/$id/', data: payload);
    return SettlementPeriodModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deleteSettlementPeriod(int id) async {
    await dio.delete('/api/v1/sales-settlement-period/$id/');
  }

  /// 정산 계산 자동 실행 (계약 실적 + R값 + 환수금 집계)
  Future<Map<String, dynamic>> generatePayouts(int periodId) async {
    final response = await dio.post(
      '/api/v1/sales-settlement-period/$periodId/generate-payouts/',
    );
    return response.data as Map<String, dynamic>;
  }

  /// 정산 회차 확정 (상태 1 -> 2)
  Future<void> confirmSettlement(int periodId) async {
    await dio.post(
      '/api/v1/sales-settlement-period/$periodId/confirm-settlement/',
    );
  }

  // ── 개인별 수수료 지급 명세 (CommissionPayout) ─────────
  Future<List<CommissionPayoutModel>> fetchCommissionPayouts({
    required int periodId,
    String? payStatus,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'period': periodId,
        'limit': 200,
      };
      if (payStatus != null && payStatus.isNotEmpty) {
        queryParams['pay_status'] = payStatus;
      }
      final response = await dio.get(
        '/api/v1/sales-payout/',
        queryParameters: queryParams,
      );
      final data = response.data;
      final results = data is Map && data.containsKey('results')
          ? data['results'] as List<dynamic>
          : (data is List ? data : []);
      return results
          .map((item) => CommissionPayoutModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      return [];
    }
  }

  /// 지급 상태 변경 (승인 / 완료 / 보류)
  Future<void> updatePayStatus(int payoutId, String payStatus) async {
    await dio.post(
      '/api/v1/sales-payout/$payoutId/update-pay-status/',
      data: {'pay_status': payStatus},
    );
  }

  /// 다중 선택 대상 일괄 지급 상태 변경
  Future<void> batchUpdatePayStatus(List<int> payoutIds, String payStatus) async {
    if (payoutIds.isEmpty) return;
    await Future.wait(
      payoutIds.map((id) => updatePayStatus(id, payStatus)),
    );
  }

  /// 정산 회차 지급 종결 처리 (상태 2 -> 3 지급 완료)
  Future<void> completeSettlementPeriod(int periodId) async {
    await updateSettlementPeriod(periodId, {'status': '3'});
  }

  /// 17. 영업 인력 제출 서류 목록 조회 (/api/v1/sales-person-document/)
  Future<List<SalesPersonDocumentModel>> fetchSalesPersonDocuments({
    required int salesPersonId,
    String? docType,
    bool? isVerified,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'sales_person': salesPersonId,
      };
      if (docType != null && docType.isNotEmpty) {
        queryParams['doc_type'] = docType;
      }
      if (isVerified != null) {
        queryParams['is_verified'] = isVerified;
      }
      final response = await dio.get(
        '/api/v1/sales-person-document/',
        queryParameters: queryParams,
      );
      final data = response.data;
      final results = data is Map && data.containsKey('results')
          ? data['results'] as List<dynamic>
          : (data is List ? data : []);
      return results
          .map((item) => SalesPersonDocumentModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      return [];
    }
  }

  /// 18. 영업 인력 서류 등록 (FormData 업로드)
  Future<SalesPersonDocumentModel> uploadSalesPersonDocument(FormData formData) async {
    final response = await dio.post(
      '/api/v1/sales-person-document/',
      data: formData,
    );
    return SalesPersonDocumentModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// 19. 영업 인력 서류 검증 처리 (verify)
  Future<void> verifySalesPersonDocument(int documentId, {required bool isVerified}) async {
    await dio.post(
      '/api/v1/sales-person-document/$documentId/verify/',
      data: {'is_verified': isVerified},
    );
  }

  /// 20. 영업 인력 서류 삭제
  Future<void> deleteSalesPersonDocument(int documentId) async {
    await dio.delete('/api/v1/sales-person-document/$documentId/');
  }
}
