import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../features/project/providers/project_provider.dart';
import 'auth_provider.dart';
import 'project_provider.dart';

// ── 전역 권한 집합 (사용자가 멤버로 속한 모든 프로젝트 권한 병합 — Vue의 globalPermSet과 100% 동일) ──

final globalPermSetProvider = Provider<Set<String>>((ref) {
  final projectsAsync = ref.watch(myProjectsProvider);
  final permSet = <String>{};

  projectsAsync.whenData((projects) {
    for (final p in projects) {
      permSet.addAll(p.myPerms);
    }
  });

  return permSet;
});

bool _isReadOnlyPerm(String code) {
  return code.endsWith('.read') ||
      code.contains('.view') ||
      code.contains('.download') ||
      code.startsWith('project.');
}

// ── 권한 검사 Extension (Vue의 can()과 100% 동일한 사용성) ────────────────────────

extension WidgetRefPermissionX on WidgetRef {
  /// 특정 권한 코드(`code`)를 보유하고 있는지 확인
  /// - `projectSlug`: 특정 프로젝트 기준 권한 검사 (지정 시 해당 프로젝트 멤버 권한만 엄격히 검사)
  bool can(String code, {String? projectSlug}) {
    final currentUser = watch(currentUserProvider).valueOrNull;

    // 1. 특정 프로젝트(projectSlug)가 명시된 경우 -> 해당 프로젝트 내 권한만 엄격히 검사 (다른 프로젝트 권한으로 우회 불가)
    if (projectSlug != null) {
      final myProjects = watch(myProjectsProvider).valueOrNull ?? [];
      final target = myProjects.where((p) => p.slug == projectSlug).firstOrNull;
      if (target != null) {
        // [닫힘('2')] 읽기 전용 워크스페이스: 쓰기/수정/삭제 권한 차단
        if (target.status == '2' && !_isReadOnlyPerm(code)) {
          return false;
        }
        // [잠금보관('9')] 접근 차단 (프로젝트 자체 관리 외 차단)
        if (target.status == '9' && !code.startsWith('project.')) {
          return false;
        }

        // 최고관리자/업무관리자라도 닫힌/잠금보관 워크스페이스 내 일반 쓰기 권한은 위에서 필터링됨
        if (currentUser != null && (currentUser.isSuperuser || currentUser.workManager)) {
          return true;
        }
        return target.myPerms.contains(code);
      }
      return false; // 해당 프로젝트의 멤버가 아니면 권한 없음
    }

    // 2. 현재 선택된 활성 프로젝트가 있는 경우 -> 해당 프로젝트 권한만 엄격히 검사
    final selectedProj = watch(selectedProjectProvider);
    if (selectedProj != null) {
      if (selectedProj.status == '2' && !_isReadOnlyPerm(code)) {
        return false;
      }
      if (selectedProj.status == '9' && !code.startsWith('project.')) {
        return false;
      }

      if (currentUser != null && (currentUser.isSuperuser || currentUser.workManager)) {
        return true;
      }
      return selectedProj.myPerms.contains(code);
    }

    // 최고관리자/업무관리자 전역 허용
    if (currentUser != null && (currentUser.isSuperuser || currentUser.workManager)) {
      return true;
    }

    // 3. 활성 프로젝트가 없는 전역 구간 ('전체 워크스페이스') -> 내가 멤버인 프로젝트들의 권한 합집합(globalPermSet)에서 확인
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
    final currentUser = watch(currentUserProvider).valueOrNull;

    // 1. 특정 프로젝트(projectSlug)가 명시된 경우
    if (projectSlug != null) {
      final myProjects = watch(myProjectsProvider).valueOrNull ?? [];
      final target = myProjects.where((p) => p.slug == projectSlug).firstOrNull;
      if (target != null) {
        if (target.status == '2' && !_isReadOnlyPerm(code)) {
          return false;
        }
        if (target.status == '9' && !code.startsWith('project.')) {
          return false;
        }

        if (currentUser != null && (currentUser.isSuperuser || currentUser.workManager)) {
          return true;
        }
        return target.myPerms.contains(code);
      }
      return false;
    }

    // 2. 현재 선택된 활성 프로젝트가 있는 경우
    final selectedProj = watch(selectedProjectProvider);
    if (selectedProj != null) {
      if (selectedProj.status == '2' && !_isReadOnlyPerm(code)) {
        return false;
      }
      if (selectedProj.status == '9' && !code.startsWith('project.')) {
        return false;
      }

      if (currentUser != null && (currentUser.isSuperuser || currentUser.workManager)) {
        return true;
      }
      return selectedProj.myPerms.contains(code);
    }

    if (currentUser != null && (currentUser.isSuperuser || currentUser.workManager)) {
      return true;
    }

    // 3. 활성 프로젝트가 없는 전역 구간
    final globalSet = watch(globalPermSetProvider);
    return globalSet.contains(code);
  }
}
