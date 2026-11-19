import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../features/project/data/models/project_model.dart';
import '../../features/project/providers/project_provider.dart';
import '../models/user_model.dart';
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
      code == 'project.pub_query' ||
      code == 'project.save_query';
}

bool _evaluatePermission({
  required UserModel? currentUser,
  required List<ProjectModel> myProjects,
  required List<ProjectModel> allProjects,
  required SelectedProject? selectedWorkspace,
  required Set<String> globalSet,
  required String code,
  String? projectSlug,
  bool global = false,
}) {
  final isAdmin =
      currentUser != null && (currentUser.isSuperuser || currentUser.workManager);

  // 1. 특정 프로젝트(projectSlug)가 명시된 경우 -> 해당 프로젝트 기준 엄격히 검사
  if (projectSlug != null) {
    final target = myProjects.where((p) => p.slug == projectSlug).firstOrNull ??
        allProjects.where((p) => p.slug == projectSlug).firstOrNull;

    if (target != null) {
      // [잠금보관('9')] 최고관리자/업무관리자의 프로젝트 자체 관리(project.*) 외에는 모두 차단
      if (target.status == '9') {
        return isAdmin && code.startsWith('project.');
      }
      // [닫힘('2')] 읽기 전용 워크스페이스: 쓰기/수정/삭제 권한 차단
      if (target.status == '2' && !_isReadOnlyPerm(code)) {
        return false;
      }
    }

    if (isAdmin) {
      return true;
    }
    if (target == null) {
      return false;
    }
    // 공개 워크스페이스 읽기 요청 허용
    if (target.isPublic && _isReadOnlyPerm(code)) {
      return true;
    }
    return target.myPerms.contains(code);
  }

  // 2. 전역 스코프(global: true)가 아닌 경우, 선택된 활성 워크스페이스가 있으면 그 기준으로 검사
  if (!global && selectedWorkspace != null) {
    if (selectedWorkspace.status == '9') {
      return isAdmin && code.startsWith('project.');
    }
    if (selectedWorkspace.status == '2' && !_isReadOnlyPerm(code)) {
      return false;
    }
    if (isAdmin) {
      return true;
    }
    if (selectedWorkspace.isPublic && _isReadOnlyPerm(code)) {
      return true;
    }
    return selectedWorkspace.myPerms.contains(code);
  }

  // 3. 최고관리자/업무관리자 전역 허용
  if (isAdmin) {
    return true;
  }

  // 4. 전역 구간 ('전체 워크스페이스' / '전체 문서함') -> 멤버 프로젝트 권한 합집합에서 확인
  return globalSet.contains(code);
}

// ── 권한 검사 Extension (Vue의 can()과 100% 동일한 사용성) ────────────────────────

bool _evaluateWithGetter(
  T Function<T>(ProviderListenable<T>) getter, {
  required String code,
  String? projectSlug,
  bool global = false,
}) {
  final currentUser = getter(currentUserProvider).valueOrNull;
  final myProjects = projectSlug != null
      ? (getter(myProjectsProvider).valueOrNull ?? const <ProjectModel>[])
      : const <ProjectModel>[];
  final allProjects = projectSlug != null
      ? (getter(projectListProvider).valueOrNull ?? const <ProjectModel>[])
      : const <ProjectModel>[];
  final selectedWorkspace =
      (projectSlug == null && !global) ? getter(selectedWorkspaceProvider) : null;
  final globalSet = (projectSlug == null && (global || selectedWorkspace == null))
      ? getter(globalPermSetProvider)
      : const <String>{};

  return _evaluatePermission(
    currentUser: currentUser,
    myProjects: myProjects,
    allProjects: allProjects,
    selectedWorkspace: selectedWorkspace,
    globalSet: globalSet,
    code: code,
    projectSlug: projectSlug,
    global: global,
  );
}

extension WidgetRefPermissionX on WidgetRef {
  /// 특정 권한 코드(`code`)를 보유하고 있는지 확인 (`build` 내부 전용 — 상태 구독)
  /// - `projectSlug`: 특정 프로젝트 기준 권한 검사 (지정 시 해당 프로젝트 기준 엄격히 검사)
  /// - `global`: true면 `selectedWorkspaceProvider` 선택 여부와 무관하게 전역 권한으로 검사
  bool can(String code, {String? projectSlug, bool global = false}) {
    return _evaluateWithGetter(
      watch,
      code: code,
      projectSlug: projectSlug,
      global: global,
    );
  }

  /// 콜백(`onTap`, `_submit` 등) 내부에서 1회성 권한 확인 (`ref.read` 기반)
  bool canOnce(String code, {String? projectSlug, bool global = false}) {
    return _evaluateWithGetter(
      read,
      code: code,
      projectSlug: projectSlug,
      global: global,
    );
  }

  /// 여러 권한 중 하나라도 만족하는지 확인
  bool canAny(List<String> codes, {String? projectSlug, bool global = false}) {
    return codes.any((code) => can(code, projectSlug: projectSlug, global: global));
  }

  /// 여러 권한을 모두 만족하는지 확인
  bool canAll(List<String> codes, {String? projectSlug, bool global = false}) {
    return codes.every((code) => can(code, projectSlug: projectSlug, global: global));
  }
}

extension RefPermissionX on Ref {
  /// Ref (Provider 내부)용 can 헬퍼
  bool can(String code, {String? projectSlug, bool global = false}) {
    return _evaluateWithGetter(
      watch,
      code: code,
      projectSlug: projectSlug,
      global: global,
    );
  }
}
