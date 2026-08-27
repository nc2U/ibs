import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/dio_provider.dart';
import 'models/site_models.dart';

final siteRepositoryProvider = Provider<SiteRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return SiteRepository(dio: dio);
});

/// 사업 부지 관리 Repository
class SiteRepository {
  final Dio dio;

  SiteRepository({required this.dio});

  /// 0. 부지 종합 집계 데이터 조회 (/api/v1/sites-total/, /api/v1/conts-total/, etc)
  Future<SiteAggregateModel> fetchSiteAggregate(int projectId, {bool isReturnedArea = false}) async {
    try {
      final results = await Future.wait([
        // 1. 총 대상면적 (official_area, returned_area) -> /api/v1/sites-total/
        dio.get('/api/v1/sites-total/', queryParameters: {'project': projectId}),
        // 2. 총 소유면적 -> /api/v1/owners-total/
        dio.get('/api/v1/owners-total/', queryParameters: {'project': projectId}),
        // 3. 총 계약면적 (contract_area) -> /api/v1/conts-total/
        dio.get('/api/v1/conts-total/', queryParameters: {'project': projectId}),
        // 4. 필지 수 카운트
        dio.get('/api/v1/site/', queryParameters: {'project': projectId, 'limit': 1}),
        // 5. 소유자 수 카운트
        dio.get('/api/v1/site-owner/', queryParameters: {'project': projectId, 'limit': 1}),
        // 6. 매입계약 수 카운트 및 금액 추출
        dio.get('/api/v1/site-contract/', queryParameters: {'project': projectId, 'limit': 1}),
      ]);

      double officialArea = 0.0;
      double returnedArea = 0.0;
      final siteAreaRaw = results[0].data;
      final siteAreaList = siteAreaRaw is Map && siteAreaRaw.containsKey('results')
          ? siteAreaRaw['results'] as List<dynamic>
          : (siteAreaRaw is List ? siteAreaRaw : []);

      if (siteAreaList.isNotEmpty) {
        officialArea = double.tryParse(siteAreaList[0]['official']?.toString() ?? '') ?? 0.0;
        returnedArea = double.tryParse(siteAreaList[0]['returned']?.toString() ?? '') ?? 0.0;
      }

      double contractedArea = 0.0;
      final contAreaRaw = results[2].data;
      final contAreaList = contAreaRaw is Map && contAreaRaw.containsKey('results')
          ? contAreaRaw['results'] as List<dynamic>
          : (contAreaRaw is List ? contAreaRaw : []);

      if (contAreaList.isNotEmpty) {
        contractedArea = double.tryParse(contAreaList[0]['contracted_area']?.toString() ?? '') ?? 0.0;
      }

      final totalSites = results[3].data is Map && results[3].data.containsKey('count')
          ? results[3].data['count'] as int
          : 0;

      final totalOwners = results[4].data is Map && results[4].data.containsKey('count')
          ? results[4].data['count'] as int
          : 0;

      final totalContracts = results[5].data is Map && results[5].data.containsKey('count')
          ? results[5].data['count'] as int
          : 0;

      return SiteAggregateModel(
        totalSitesCount: totalSites,
        totalOfficialArea: officialArea,
        totalReturnedArea: returnedArea,
        isReturnedArea: isReturnedArea,
        totalOwnersCount: totalOwners,
        totalContractsCount: totalContracts,
        totalContractedArea: contractedArea,
        totalPrice: 0,
      );
    } catch (e) {
      return SiteAggregateModel(
        totalSitesCount: 0,
        totalOfficialArea: 0.0,
        totalReturnedArea: 0.0,
        isReturnedArea: isReturnedArea,
        totalOwnersCount: 0,
        totalContractsCount: 0,
        totalContractedArea: 0.0,
        totalPrice: 0,
      );
    }
  }

  /// 1. 지번별 토지 목록 조회 (/api/v1/site/?project={projectId})
  Future<List<SiteItemModel>> fetchSites({
    required int projectId,
    String? search,
    int page = 1,
    int limit = 15,
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
        '/api/v1/site/',
        queryParameters: queryParams,
      );

      final List<dynamic> results = response.data is Map && response.data.containsKey('results')
          ? response.data['results']
          : (response.data is List ? response.data : []);

      return results.map((json) => SiteItemModel.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }

  /// 2. 소유자별 토지 목록 조회 (/api/v1/site-owner/?project={projectId})
  Future<List<SiteOwnerItemModel>> fetchSiteOwners({
    required int projectId,
    String? search,
    String? ownSort,
    bool? useConsent,
    int page = 1,
    int limit = 15,
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
      if (ownSort != null && ownSort.isNotEmpty) {
        queryParams['own_sort'] = ownSort;
      }
      if (useConsent != null) {
        queryParams['use_consent'] = useConsent;
      }

      final response = await dio.get(
        '/api/v1/site-owner/',
        queryParameters: queryParams,
      );

      final List<dynamic> results = response.data is Map && response.data.containsKey('results')
          ? response.data['results']
          : (response.data is List ? response.data : []);

      return results.map((json) => SiteOwnerItemModel.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }

  /// 3. 사업부지 매입 계약 목록 조회 (/api/v1/site-contract/?project={projectId})
  Future<List<SiteContractItemModel>> fetchSiteContracts({
    required int projectId,
    String? search,
    String? ownSort,
    int page = 1,
    int limit = 15,
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
      if (ownSort != null && ownSort.isNotEmpty) {
        queryParams['owner__own_sort'] = ownSort;
      }

      final response = await dio.get(
        '/api/v1/site-contract/',
        queryParameters: queryParams,
      );

      final List<dynamic> results = response.data is Map && response.data.containsKey('results')
          ? response.data['results']
          : (response.data is List ? response.data : []);

      return results.map((json) => SiteContractItemModel.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }

  /// 4. 토지조서(지번별 토지목록) 엑셀 다운로드 (/excel/sites/?project={projectId})
  Future<List<int>?> downloadSitesExcel({
    required int projectId,
    String? search,
  }) async {
    try {
      final queryParams = <String, dynamic>{'project': projectId};
      if (search != null && search.trim().isNotEmpty) {
        queryParams['search'] = search.trim();
      }

      final response = await dio.get<List<int>>(
        '/excel/sites/',
        queryParameters: queryParams,
        options: Options(responseType: ResponseType.bytes),
      );
      return response.data;
    } catch (e) {
      return null;
    }
  }

  /// 5. 소유자별 토지조서 엑셀 다운로드 (/excel/sites-by-owner/?project={projectId})
  Future<List<int>?> downloadOwnersExcel({
    required int projectId,
    String? search,
    String? ownSort,
  }) async {
    try {
      final queryParams = <String, dynamic>{'project': projectId};
      if (search != null && search.trim().isNotEmpty) {
        queryParams['search'] = search.trim();
      }
      if (ownSort != null && ownSort.isNotEmpty) {
        queryParams['own_sort'] = ownSort;
      }

      final response = await dio.get<List<int>>(
        '/excel/sites-by-owner/',
        queryParameters: queryParams,
        options: Options(responseType: ResponseType.bytes),
      );
      return response.data;
    } catch (e) {
      return null;
    }
  }

  /// 6. 사업부지 매입계약 현황 엑셀 다운로드 (/excel/sites-contracts/?project={projectId})
  Future<List<int>?> downloadContractsExcel({
    required int projectId,
    String? search,
    String? ownSort,
  }) async {
    try {
      final queryParams = <String, dynamic>{'project': projectId};
      if (search != null && search.trim().isNotEmpty) {
        queryParams['search'] = search.trim();
      }
      if (ownSort != null && ownSort.isNotEmpty) {
        queryParams['own_sort'] = ownSort;
      }

      final response = await dio.get<List<int>>(
        '/excel/sites-contracts/',
        queryParameters: queryParams,
        options: Options(responseType: ResponseType.bytes),
      );
      return response.data;
    } catch (e) {
      return null;
    }
  }

  /// 7. 토지 소유자 상담 기록 목록 조회 (/api/v1/site-owner-consultations/?site_owner={ownerId})
  Future<List<SiteOwnerConsultationLogModel>> fetchOwnerConsultationLogs({
    required int siteOwnerId,
  }) async {
    try {
      final response = await dio.get(
        '/api/v1/site-owner-consultations/',
        queryParameters: {'site_owner': siteOwnerId},
      );

      final List<dynamic> results = response.data is Map && response.data.containsKey('results')
          ? response.data['results']
          : (response.data is List ? response.data : []);

      return results
          .map((json) => SiteOwnerConsultationLogModel.fromJson(json))
          .toList();
    } catch (e) {
      return [];
    }
  }

  /// 8. 토지 소유자 상담/협의 기록 신규 등록 (/api/v1/site-owner-consultations/)
  Future<String?> createOwnerConsultationLog({
    required int siteOwnerId,
    required String consultationDate,
    required String channel,
    required String title,
    required String content,
    bool followUpRequired = false,
    String? followUpNote,
  }) async {
    try {
      final payload = <String, dynamic>{
        'site_owner': siteOwnerId,
        'consultation_date': consultationDate,
        'channel': channel,
        'title': title,
        'content': content,
        'follow_up_required': followUpRequired,
      };
      if (followUpNote != null && followUpNote.trim().isNotEmpty) {
        payload['follow_up_note'] = followUpNote.trim();
      }

      final response = await dio.post(
        '/api/v1/site-owner-consultations/',
        data: payload,
      );
      if (response.statusCode == 200 || response.statusCode == 201) {
        return null; // 성공 (에러 없음)
      }
      return '서버 응답 오류: ${response.statusCode}';
    } on DioException catch (e) {
      if (e.response?.data is Map) {
        final map = e.response!.data as Map;
        return map.entries.map((entry) => '${entry.key}: ${entry.value}').join('\n');
      }
      return e.message ?? '상담일지 등록에 실패했습니다.';
    } catch (e) {
      return e.toString();
    }
  }

  /// 7. 토지 등기부등본(등기사항전부증명서) 파일 다운로드
  Future<List<int>?> downloadSiteRegisterFile(String fileUrl) async {
    try {
      String targetUrl = fileUrl.trim();

      // 상대경로(/media/...)인 경우 dio의 baseUrl과 결합
      if (targetUrl.startsWith('/')) {
        final response = await dio.get<List<int>>(
          targetUrl,
          options: Options(
            responseType: ResponseType.bytes,
            followRedirects: true,
          ),
        );
        return response.data;
      }

      // S3 Presigned URL 또는 절대 경로 URL (이미 백엔드에서 서명 및 인코딩된 URL이므로 이중 인코딩 방지)
      final downloadDio = Dio(
        BaseOptions(
          connectTimeout: const Duration(seconds: 15),
          receiveTimeout: const Duration(seconds: 30),
        ),
      );

      final response = await downloadDio.get<List<int>>(
        targetUrl,
        options: Options(
          responseType: ResponseType.bytes,
          followRedirects: true,
        ),
      );
      return response.data;
    } catch (e) {
      return null;
    }
  }
}
