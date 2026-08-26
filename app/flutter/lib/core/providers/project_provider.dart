import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../features/project/data/models/project_model.dart';

// ── 선택된 프로젝트 모델 (경량) ────────────────────────────────────────────────────
class SelectedProject {
  final int pk;
  final int? projectId; // 실제 부동산 개발 프로젝트 (Project) PK
  final String name;
  final String slug;
  final String? description;
  final String type;
  final String status;
  final bool isPublic;
  final List<String> myPerms;
  final ProjectModuleModel? module;

  const SelectedProject({
    required this.pk,
    this.projectId,
    required this.name,
    required this.slug,
    this.description,
    this.type = '1',
    this.status = '1',
    this.isPublic = false,
    this.myPerms = const [],
    this.module,
  });

  /// 계약, 수납, 자금 등 부동산 도메인 API 호출 시 사용할 실제 Project PK
  int get realProjectId => projectId ?? pk;
}

// ── 전역 워크스페이스 / 프로젝트 선택 상태 ──────────────────────────────────────────
/// 1. 워크스페이스 전용 선택 상태 (업무, 회의, 채널, 검색 등 Work Core 공용)
/// - null: "🏢 전체 워크스페이스"
final selectedWorkspaceProvider = StateProvider<SelectedProject?>((ref) => null);

/// 워크스페이스 이름 (표시용)
final selectedWorkspaceNameProvider = Provider<String>((ref) {
  final ws = ref.watch(selectedWorkspaceProvider);
  return ws?.name ?? '전체 워크스페이스';
});

/// 2. 부동산 개발 프로젝트 전용 선택 상태 (계약, 수납, 자금, 부지 등 IBS Global 전용 - type == '2')
final selectedRealEstateProjectProvider = StateProvider<SelectedProject?>((ref) => null);

/// 부동산 개발 프로젝트 이름 (표시용)
final selectedRealEstateProjectNameProvider = Provider<String>((ref) {
  final pjt = ref.watch(selectedRealEstateProjectProvider);
  return pjt?.name ?? '프로젝트를 선택하세요';
});

/// 레거시 호환용 (selectedWorkspaceProvider를 가리킴)
final selectedProjectProvider = selectedWorkspaceProvider;
final selectedProjectNameProvider = selectedWorkspaceNameProvider;
