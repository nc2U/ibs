import 'dart:typed_data';
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

  /// 1. 프로젝트 계약 집계 현황 조회 (/api/v1/cont-aggregate/{projectId}/)
  Future<ContractAggregateModel> fetchContractAggregate(int projectId) async {
    try {
      final response = await dio.get('/api/v1/cont-aggregate/$projectId/');
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
    int page = 1,
    int limit = 10,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'project': projectId,
        'is_active': true,
        'is_contract': true, // 계약자('2') 및 변경처리중('3') 유효 계약만 조회
        'page': page,
        'limit': limit,
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

  /// 2-2. 계약 단건 상세 조회 (/api/v1/contract-set/{contractId}/)
  Future<ContractItemModel?> fetchContractDetail(int contractId) async {
    try {
      final response = await dio.get('/api/v1/contract-set/$contractId/');
      if (response.data is Map<String, dynamic>) {
        return ContractItemModel.fromJson(response.data as Map<String, dynamic>);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  /// 3. 권리의무 승계 목록 조회 (/api/v1/succession/?contract__project={projectId})
  Future<List<SuccessionItemModel>> fetchSuccessions({
    required int projectId,
    String? search,
    int page = 1,
    int limit = 10,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'contract__project': projectId,
        'page': page,
        'limit': limit,
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

  /// 5. 분양대금 납부확인서 PDF 다운로드 (/pdf/ledger/payment/?contract={contractId}&pub_date={date}&is_calc=1)
  Future<Uint8List?> downloadPaymentCertPdf({
    required int contractId,
    String? pubDate,
    bool isCalc = true,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'contract': contractId,
        'is_calc': isCalc ? '1' : '',
      };
      if (pubDate != null && pubDate.isNotEmpty) {
        queryParams['pub_date'] = pubDate;
      }

      final response = await dio.get(
        '/pdf/ledger/payment/',
        queryParameters: queryParams,
        options: Options(
          responseType: ResponseType.bytes,
        ),
      );

      if (response.statusCode == 200 && response.data != null) {
        if (response.data is Uint8List) {
          return response.data as Uint8List;
        } else if (response.data is List<int>) {
          return Uint8List.fromList(response.data as List<int>);
        } else if (response.data is List) {
          return Uint8List.fromList((response.data as List).cast<int>());
        }
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  /// 6. 계약자별 상담/민원 이력 목록 조회 (/api/v1/contractor-consultations/?contractor={contractorId})
  Future<List<ContractorConsultationLogModel>> fetchConsultationLogs({
    required int contractorId,
  }) async {
    try {
      final response = await dio.get(
        '/api/v1/contractor-consultations/',
        queryParameters: {
          'contractor': contractorId,
        },
      );

      final List<dynamic> results =
          response.data is Map && response.data.containsKey('results')
              ? response.data['results']
              : (response.data is List ? response.data : []);

      return results
          .map((json) => ContractorConsultationLogModel.fromJson(json))
          .toList();
    } catch (e) {
      return [];
    }
  }

  /// 7. 계약자 상담/민원 기록 신규 등록 (/api/v1/contractor-consultations/)
  Future<bool> createConsultationLog({
    required int contractorId,
    required String consultationDate,
    required String channel,
    required String category,
    required String title,
    required String content,
    String status = '1',
    String priority = 'normal',
    bool followUpRequired = false,
    String? followUpNote,
    bool isImportant = false,
  }) async {
    try {
      final payload = <String, dynamic>{
        'contractor': contractorId,
        'consultation_date': consultationDate,
        'channel': channel,
        'category': category,
        'title': title,
        'content': content,
        'status': status,
        'priority': priority,
        'follow_up_required': followUpRequired,
        'is_important': isImportant,
      };
      if (followUpNote != null && followUpNote.trim().isNotEmpty) {
        payload['follow_up_note'] = followUpNote.trim();
      }

      final response = await dio.post(
        '/api/v1/contractor-consultations/',
        data: payload,
      );

      return response.statusCode == 201 || response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  /// 8. 계약자 주소 변경 이력 목록 조회 (/api/v1/contractor-address/?contractor={contractorId})
  Future<List<ContractorAddressModel>> fetchAddressHistory({
    required int contractorId,
  }) async {
    try {
      final response = await dio.get(
        '/api/v1/contractor-address/',
        queryParameters: {
          'contractor': contractorId,
        },
      );

      final List<dynamic> results =
          response.data is Map && response.data.containsKey('results')
              ? response.data['results']
              : (response.data is List ? response.data : []);

      return results
          .map((json) => ContractorAddressModel.fromJson(json))
          .toList();
    } catch (e) {
      return [];
    }
  }

  /// 9. 계약자 변경 주소 신규 등록 (/api/v1/contractor-address/)
  /// (백엔드 Serializer에서 생성 시 기존 주소를 자동으로 is_current=False 처리함)
  Future<bool> createAddress({
    required int contractorId,
    required String idZipcode,
    required String idAddress1,
    String? idAddress2,
    String? idAddress3,
    required String dmZipcode,
    required String dmAddress1,
    String? dmAddress2,
    String? dmAddress3,
  }) async {
    try {
      final payload = <String, dynamic>{
        'contractor': contractorId,
        'id_zipcode': idZipcode.trim(),
        'id_address1': idAddress1.trim(),
        'id_address2': (idAddress2 ?? '').trim(),
        'id_address3': (idAddress3 ?? '').trim(),
        'dm_zipcode': dmZipcode.trim(),
        'dm_address1': dmAddress1.trim(),
        'dm_address2': (dmAddress2 ?? '').trim(),
        'dm_address3': (dmAddress3 ?? '').trim(),
        'is_current': true,
      };

      final response = await dio.post(
        '/api/v1/contractor-address/',
        data: payload,
      );

      return response.statusCode == 201 || response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  /// 10. 프로젝트 동 목록 조회 (/api/v1/building-unit/?project={projectId})
  Future<List<BuildingUnitModel>> fetchBuildingUnits(int projectId) async {
    try {
      final response = await dio.get(
        '/api/v1/building-unit/',
        queryParameters: {'project': projectId, 'limit': 100},
      );
      final List<dynamic> results =
          response.data is Map && response.data.containsKey('results')
              ? response.data['results']
              : (response.data is List ? response.data : []);
      return results.map((json) => BuildingUnitModel.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }

  /// 11. 프로젝트 유닛 타입 목록 조회 (/api/v1/unit-type/?project={projectId})
  Future<List<UnitTypeItemModel>> fetchUnitTypes(int projectId) async {
    try {
      final response = await dio.get(
        '/api/v1/unit-type/',
        queryParameters: {'project': projectId, 'limit': 100},
      );
      final List<dynamic> results =
          response.data is Map && response.data.containsKey('results')
              ? response.data['results']
              : (response.data is List ? response.data : []);
      return results.map((json) => UnitTypeItemModel.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }

  /// 12. 프로젝트 전체 동호수 배치 목록 조회 (/api/v1/all-house-unit/?building_unit__project={projectId})
  Future<List<LayoutHouseUnitModel>> fetchAllHouseUnits(int projectId, {int? buildingUnitId}) async {
    try {
      final queryParams = <String, dynamic>{
        'building_unit__project': projectId,
        'limit': 3000,
      };
      if (buildingUnitId != null) {
        queryParams['building_unit'] = buildingUnitId;
      }
      final response = await dio.get(
        '/api/v1/all-house-unit/',
        queryParameters: queryParams,
      );
      final List<dynamic> results =
          response.data is Map && response.data.containsKey('results')
              ? response.data['results']
              : (response.data is List ? response.data : []);
      return results.map((json) => LayoutHouseUnitModel.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }
}
