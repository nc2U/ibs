import 'package:flutter_riverpod/flutter_riverpod.dart';

// ── 선택된 프로젝트 모델 (경량) ────────────────────────────────────────────────────
class SelectedProject {
  final int pk;
  final String name;
  final String slug;
  final String? description;
  final String type;
  final bool isPublic;
  final List<String> myPerms;

  const SelectedProject({
    required this.pk,
    required this.name,
    required this.slug,
    this.description,
    this.type = '1',
    this.isPublic = false,
    this.myPerms = const [],
  });
}

// ── 전역 프로젝트 선택 상태 ────────────────────────────────────────────────────────
/// 앱 전체에서 "현재 선택된 프로젝트"를 공유하는 전역 프로바이더
/// AppBar, 업무 목록, 재무 등 모든 탭에서 공통으로 참조
final selectedProjectProvider = StateProvider<SelectedProject?>((ref) => null);

/// 프로젝트 이름 (AppBar 표시용)
final selectedProjectNameProvider = Provider<String>((ref) {
  final project = ref.watch(selectedProjectProvider);
  return project?.name ?? '전체 워크스페이스';
});
