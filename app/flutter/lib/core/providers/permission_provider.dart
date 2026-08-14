import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../features/project/providers/project_provider.dart';
import '../constants/permissions.dart';
import 'project_provider.dart';

// ── 전역 권한 집합 (사용자가 속한 모든 프로젝트 권한 병합) ─────────────────────────

final globalPermSetProvider = Provider<Set<String>>((ref) {
  final projectsAsync = ref.watch(projectListProvider);
  final permSet = <String>{};

  projectsAsync.whenData((projects) {
    for (final p in projects) {
      permSet.addAll(p.myPerms);
    }
  });

  return permSet;
});

// ── 권한 검사 Extension (Vue의 can()과 100% 동일한 사용성) ────────────────────────

extension WidgetRefPermissionX on WidgetRef {
  /// 특정 권한 코드(`code`)를 보유하고 있는지 확인
  /// - `projectSlug`: 특정 프로젝트 기준 권한 검사 (지정하지 않으면 현재 선택된 프로젝트 또는 전역 권한 기준)
  bool can(String code, {String? projectSlug}) {
    if (projectSlug != null) {
      final projects = watch(projectListProvider).valueOrNull ?? [];
      final target = projects.cast<dynamic>().firstWhere(
            (p) => p.slug == projectSlug,
            orElse: () => null,
          );
      if (target != null && target.myPerms != null) {
        return (target.myPerms as List<String>).contains(code);
      }
    }

    // 1. 현재 선택된 활성 프로젝트가 있으면 해당 프로젝트 권한 확인
    final selectedProj = watch(selectedProjectProvider);
    if (selectedProj != null && selectedProj.myPerms.isNotEmpty) {
      return selectedProj.myPerms.contains(code);
    }

    // 2. 전체(전역) 권한 집합에서 확인
    final globalSet = watch(globalPermSetProvider);
    return globalSet.contains(code);
  }

  /// 여러 권한 중 하나라도 만족하는지 확인
  bool canAny(List<String> codes, {String? projectSlug}) {
    return codes.any((code) => can(code, projectSlug: projectSlug));
  }

  /// 여러 권한을 모두 만족하는지 확인
  bool canAll(List<String> codes, {String? projectSlug}) {
    return codes.every((code) => can(code, projectSlug: projectSlug));
  }
}

extension RefPermissionX on Ref {
  /// Ref (Provider 내부)용 can 헬퍼
  bool can(String code, {String? projectSlug}) {
    if (projectSlug != null) {
      final projects = watch(projectListProvider).valueOrNull ?? [];
      final target = projects.cast<dynamic>().firstWhere(
            (p) => p.slug == projectSlug,
            orElse: () => null,
          );
      if (target != null && target.myPerms != null) {
        return (target.myPerms as List<String>).contains(code);
      }
    }

    final selectedProj = watch(selectedProjectProvider);
    if (selectedProj != null && selectedProj.myPerms.isNotEmpty) {
      return selectedProj.myPerms.contains(code);
    }

    final globalSet = watch(globalPermSetProvider);
    return globalSet.contains(code);
  }
}
