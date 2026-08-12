import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

part 'project_provider.freezed.dart';

// ── 선택된 프로젝트 모델 (경량) ────────────────────────────────────────────────────
@freezed
class SelectedProject with _$SelectedProject {
  const factory SelectedProject({
    required int pk,
    required String name,
    required String slug,
    String? description,
    @Default('1') String type,
    @Default(false) bool isPublic,
  }) = _SelectedProject;
}

// ── 전역 프로젝트 선택 상태 ────────────────────────────────────────────────────────
/// 앱 전체에서 "현재 선택된 프로젝트"를 공유하는 전역 프로바이더
/// AppBar, 업무 목록, 재무 등 모든 탭에서 공통으로 참조
final selectedProjectProvider = StateProvider<SelectedProject?>((ref) => null);

/// 프로젝트 이름 (AppBar 표시용)
final selectedProjectNameProvider = Provider<String>((ref) {
  final project = ref.watch(selectedProjectProvider);
  return project?.name ?? '전사 공통';
});
