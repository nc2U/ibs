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

  /// Dio 에러 메시지 추출 헬퍼
  static String extractErrorMessage(Object error, String fallback) {
    if (error is DioException) {
      if (error.response?.statusCode == 403) {
        return '권한이 없습니다. (프로젝트 계약 관리 권한 확인 필요)';
      }
      final data = error.response?.data;
      if (data is Map) {
        if (data['detail'] != null) return data['detail'].toString();
        if (data['message'] != null) return data['message'].toString();
        final firstVal = data.values.firstOrNull;
        if (firstVal is List && firstVal.isNotEmpty) {
          return firstVal.first.toString();
        } else if (firstVal != null) {
          return firstVal.toString();
        }
      }
    }
    return fallback;
  }

  /// 1. 프로젝트 계약 집계 현황 조회 (/api/v1/cont-aggregate/{projectId}/)
  Future<ContractAggregateModel> fetchContractAggregate(int projectId) async {
    final response = await dio.get('/api/v1/cont-aggregate/$projectId/');
    return ContractAggregateModel.fromJson(response.data);
  }

  Future<({List<T> items, bool hasMore})> _fetchPaged<T>(
    String path, {
    required Map<String, dynamic> queryParams,
    required T Function(Map<String, dynamic>) fromJson,
  }) async {
    final response = await dio.get(path, queryParameters: queryParams);
    final data = response.data;
    final List<dynamic> results =
        data is Map && data.containsKey('results')
            ? (data['results'] as List<dynamic>? ?? const [])
            : (data is List ? data : const []);
    final hasMore = data is Map && data['next'] != null;
    return (
      items: results
          .map((json) => fromJson(json as Map<String, dynamic>))
          .toList(),
      hasMore: hasMore,
    );
  }

  /// 2. 유효 계약 목록 조회 (/api/v1/contract-set/?project={projectId}&is_active=true&is_contract=true)
  Future<({List<ContractItemModel> items, bool hasMore})> fetchContracts({
    required int projectId,
    String? search,
    int? orderGroup,
    int? unitType,
    int page = 1,
    int limit = 10,
  }) async {
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

    return _fetchPaged(
      '/api/v1/contract-set/',
      queryParams: queryParams,
      fromJson: ContractItemModel.fromJson,
    );
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
  Future<({List<SuccessionItemModel> items, bool hasMore})> fetchSuccessions({
    required int projectId,
    String? search,
    int page = 1,
    int limit = 10,
  }) async {
    final queryParams = <String, dynamic>{
      'contract__project': projectId,
      'page': page,
      'limit': limit,
    };
    if (search != null && search.trim().isNotEmpty) {
      queryParams['search'] = search.trim();
    }

    return _fetchPaged(
      '/api/v1/succession/',
      queryParams: queryParams,
      fromJson: SuccessionItemModel.fromJson,
    );
  }

  /// 4. 계약 해약/해지 목록 조회 (/api/v1/contractor-release/?project={projectId})
  Future<({List<ContractorReleaseItemModel> items, bool hasMore})> fetchReleases({
    required int projectId,
    String? search,
    int page = 1,
    int limit = 10,
  }) async {
    final queryParams = <String, dynamic>{
      'project': projectId,
      'page': page,
      'limit': limit,
    };
    if (search != null && search.trim().isNotEmpty) {
      queryParams['search'] = search.trim();
    }

    return _fetchPaged(
      '/api/v1/contractor-release/',
      queryParams: queryParams,
      fromJson: ContractorReleaseItemModel.fromJson,
    );
  }

  static Uint8List? _extractBinaryBytes(Response<dynamic> response) {
    final contentType =
        response.headers.value('content-type')?.toLowerCase() ?? '';
    if (contentType.contains('text/html')) return null;
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
  }

  /// 5. 분양대금 납부확인서 PDF 다운로드 (/pdf/ledger/payment/?project={projectId}&contract={contractId}&pub_date={date}&is_calc=1)
  Future<Uint8List?> downloadPaymentCertPdf({
    required int contractId,
    int? projectId,
    String? pubDate,
    bool isCalc = true,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'contract': contractId,
        'is_calc': isCalc ? '1' : '',
      };
      if (projectId != null && projectId > 0) {
        queryParams['project'] = projectId;
      }
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

      return _extractBinaryBytes(response);
    } catch (e) {
      return null;
    }
  }

  /// 6. 계약자별 상담/민원 이력 목록 조회 (/api/v1/contractor-consultations/?contractor={contractorId})
  Future<List<ContractorConsultationLogModel>> fetchConsultationLogs({
    required int contractorId,
  }) async {
    final response = await dio.get(
      '/api/v1/contractor-consultations/',
      queryParameters: {
        'contractor': contractorId,
        'limit': 500,
      },
    );

    final List<dynamic> results =
        response.data is Map && response.data.containsKey('results')
            ? response.data['results']
            : (response.data is List ? response.data : []);

    return results
        .map((json) => ContractorConsultationLogModel.fromJson(json))
        .toList();
  }

  /// 7. 계약자 상담/민원 기록 신규 등록 (/api/v1/contractor-consultations/)
  Future<({bool success, String? errorMessage})> createConsultationLog({
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

      final ok = response.statusCode == 201 || response.statusCode == 200;
      return (success: ok, errorMessage: ok ? null : '상담 기록 등록에 실패했습니다.');
    } catch (e) {
      return (
        success: false,
        errorMessage: extractErrorMessage(e, '상담 기록 등록에 실패했습니다.'),
      );
    }
  }

  /// 8. 계약자 주소 변경 이력 목록 조회 (/api/v1/contractor-address/?contractor={contractorId})
  Future<List<ContractorAddressModel>> fetchAddressHistory({
    required int contractorId,
  }) async {
    final response = await dio.get(
      '/api/v1/contractor-address/',
      queryParameters: {
        'contractor': contractorId,
        'limit': 500,
      },
    );

    final List<dynamic> results =
        response.data is Map && response.data.containsKey('results')
            ? response.data['results']
            : (response.data is List ? response.data : []);

    return results
        .map((json) => ContractorAddressModel.fromJson(json))
        .toList();
  }

  /// 9. 계약자 변경 주소 신규 등록 (/api/v1/contractor-address/)
  /// (백엔드 Serializer에서 생성 시 기존 주소를 자동으로 is_current=False 처리함)
  Future<({bool success, String? errorMessage})> createAddress({
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

      final ok = response.statusCode == 201 || response.statusCode == 200;
      return (success: ok, errorMessage: ok ? null : '주소 등록에 실패했습니다.');
    } catch (e) {
      return (
        success: false,
        errorMessage: extractErrorMessage(e, '주소 등록에 실패했습니다.'),
      );
    }
  }

  /// 10. 프로젝트 동 목록 조회 (/api/v1/bldg/?project={projectId})
  Future<List<BuildingUnitModel>> fetchBuildingUnits(int projectId) async {
    final response = await dio.get(
      '/api/v1/bldg/',
      queryParameters: {'project': projectId, 'limit': 500},
    );
    final List<dynamic> results =
        response.data is Map && response.data.containsKey('results')
            ? response.data['results']
            : (response.data is List ? response.data : []);
    return results.map((json) => BuildingUnitModel.fromJson(json)).toList();
  }

  /// 11. 프로젝트 유닛 타입 목록 조회 (/api/v1/type/?project={projectId})
  Future<List<UnitTypeItemModel>> fetchUnitTypes(int projectId) async {
    final response = await dio.get(
      '/api/v1/type/',
      queryParameters: {'project': projectId, 'limit': 500},
    );
    final List<dynamic> results =
        response.data is Map && response.data.containsKey('results')
            ? response.data['results']
            : (response.data is List ? response.data : []);
    return results.map((json) => UnitTypeItemModel.fromJson(json)).toList();
  }

  /// 12. 프로젝트 전체 동호수 배치 목록 조회 (/api/v1/all-house-unit/?building_unit__project={projectId})
  Future<List<LayoutHouseUnitModel>> fetchAllHouseUnits(int projectId, {int? buildingUnitId}) async {
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
  }

  /// 13. 동호수 현황표 엑셀 다운로드 (/excel/status/?project={projectId}&iscontor={true/false})
  Future<Uint8List?> downloadUnitStatusExcel({
    required int projectId,
    required bool isContractor,
  }) async {
    try {
      final response = await dio.get(
        '/excel/status/',
        queryParameters: {
          'project': projectId,
          'iscontor': isContractor ? 'true' : 'false',
        },
        options: Options(
          responseType: ResponseType.bytes,
        ),
      );

      return _extractBinaryBytes(response);
    } catch (e) {
      return null;
    }
  }
}
