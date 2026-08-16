import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/docs_context_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../data/models/project_model.dart';
import '../data/project_repository.dart';

// ── 트리 재구성 헬퍼 (Vue buildProjectTree와 100% 동일) ──────────────────────────
List<ProjectModel> buildProjectTree(List<ProjectModel> projects) {
  final map = <int, ProjectModel>{};
  for (final p in projects) {
    map[p.pk] = p.copyWith(subProjects: []);
  }

  final roots = <ProjectModel>[];
  for (final p in projects) {
    final current = map[p.pk]!;
    if (p.parent != null) {
      final parentNode = map[p.parent!];
      if (parentNode != null) {
        parentNode.subProjects.add(current);
      } else {
        roots.add(current);
      }
    } else {
      roots.add(current);
    }
  }
  return roots;
}

// ── 재귀적 평탄화 헬퍼 (DFS 순회, Vue flattenTree와 100% 동일) ─────────────────────
List<ProjectModel> flattenProjectTree(List<ProjectModel> tree) {
  final visited = <int>{};
  final result = <ProjectModel>[];

  void flatten(ProjectModel proj) {
    if (!visited.contains(proj.pk) && proj.visible) {
      visited.add(proj.pk);
      result.add(proj);
    }
    for (final sub in proj.subProjects) {
      flatten(sub);
    }
  }

  for (final root in tree) {
    flatten(root);
  }
  return result;
}

List<ProjectModel> toFlattenedTree(List<ProjectModel> projects) {
  final tree = buildProjectTree(projects);
  return flattenProjectTree(tree);
}

// ── 프로젝트 전체 목록 프로바이더 (트리 평탄화 정렬 적용) ─────────────────────────
final projectListProvider = FutureProvider<List<ProjectModel>>((ref) async {
  final raw = await ref.watch(projectRepositoryProvider).fetchProjects();
  return toFlattenedTree(raw);
});

// ── 전역 활성 워크스페이스 목록 프로바이더 (Vue Header의 allActiveProjects와 100% 동일) ──
/// 상태가 활성(status == '1')이고 가시성(visible == true)이 있는 프로젝트 목록
final activeWorkspaceListProvider = FutureProvider<List<ProjectModel>>((ref) async {
  final all = await ref.watch(projectListProvider.future);
  return all.where((p) => p.status == '1' && p.visible).toList();
});

// ── 내 워크스페이스 목록 프로바이더 (/api/v1/issue-project/my_projects/) ─────────────
final myProjectsProvider = FutureProvider<List<ProjectModel>>((ref) async {
  final raw = await ref.watch(projectRepositoryProvider).fetchMyProjects();
  return toFlattenedTree(raw);
});

// ── 업무(Issue) 등록 폼 주입용 워크스페이스 목록 프로바이더 ────────────────────────────
/// Vue의 `myProjects.filter(pjt => pjt.module?.issue)`와 100% 동일
final issueFormProjectsProvider = FutureProvider<List<ProjectModel>>((ref) async {
  final myProjects = await ref.watch(myProjectsProvider.future);
  // 이슈 모듈이 활성화된(module?.issue != false) 프로젝트만 주입
  final filtered = myProjects.where((p) => p.module?.issue ?? true).toList();
  // myProjects가 비어있을 경우 전체 목록에서 폴백
  if (filtered.isNotEmpty) return filtered;
  final all = await ref.watch(projectListProvider.future);
  return all.where((p) => p.module?.issue ?? true).toList();
});

// ── 회의(Meeting) 등록 폼 주입용 워크스페이스 목록 프로바이더 ──────────────────────────
/// Vue의 `myProjects.filter(pjt => pjt.module?.meeting)`와 100% 동일
final meetingFormProjectsProvider = FutureProvider<List<ProjectModel>>((ref) async {
  final myProjects = await ref.watch(myProjectsProvider.future);
  // 회의 모듈이 활성화된(module?.meeting != false) 프로젝트만 주입
  final filtered = myProjects.where((p) => p.module?.meeting ?? true).toList();
  // myProjects가 비어있을 경우 전체 목록에서 폴백
  if (filtered.isNotEmpty) return filtered;
  final all = await ref.watch(projectListProvider.future);
  return all.where((p) => p.module?.meeting ?? true).toList();
});

// ── 문서(Document) 등록 폼 주입용 워크스페이스 목록 프로바이더 ───────────────────────
/// 현재 진입 컨텍스트(업무 메뉴 vs 프로젝트 메뉴)에 따라:
/// - 프로젝트 메뉴(DocsScopeType.project): 부동산 개발 타입(type == '2') 내 프로젝트만 주입
/// - 업무 메뉴(DocsScopeType.all / workspace): 전체 내 프로젝트(myProjects) 주입
final docFormProjectsProvider = FutureProvider<List<ProjectModel>>((ref) async {
  final docsContext = ref.watch(docsContextProvider);
  final isProjectMenu = docsContext.scopeType == DocsScopeType.project;

  if (isProjectMenu) {
    // 프로젝트 메뉴: 부동산 개발(type == '2') 내 프로젝트만 필터링
    final devProjects = await ref.watch(realEstateProjectsProvider.future);
    return devProjects.where((p) => p.module?.document ?? true).toList();
  }

  // 업무 메뉴: 전체 내 프로젝트 목록
  final myProjects = await ref.watch(myProjectsProvider.future);
  final filtered = myProjects.where((p) => p.module?.document ?? true).toList();
  if (filtered.isNotEmpty) return filtered;
  final all = await ref.watch(projectListProvider.future);
  return all.where((p) => p.module?.document ?? true).toList();
});

// ── 공지(News) 등록 폼 주입용 워크스페이스 목록 프로바이더 ───────────────────────────
/// Vue의 `myProjects.filter(pjt => pjt.module?.news)`와 100% 동일
final newsFormProjectsProvider = FutureProvider<List<ProjectModel>>((ref) async {
  final myProjects = await ref.watch(myProjectsProvider.future);
  final filtered = myProjects.where((p) => p.module?.news ?? true).toList();
  if (filtered.isNotEmpty) return filtered;
  final all = await ref.watch(projectListProvider.future);
  return all.where((p) => p.module?.news ?? true).toList();
});

// ── 프로젝트 상세 프로바이더 (members, versions, categories 포함) ─────────────────
final projectDetailProvider =
    FutureProvider.family<ProjectModel, String>((ref, slug) async {
  return ref.watch(projectRepositoryProvider).fetchProjectDetail(slug);
});

// ── 부동산 개발 프로젝트 전용 프로바이더 (type == '2') ──────────────────────────────
/// Vue의 `getDevProjects`와 100% 동일 (myProjects 기반으로 type == '2' 필터링)
/// 계약/수납/자금 등 민감 정보를 다루므로 멤버로 속한 프로젝트(myProjects) 중에서만 주입
final realEstateProjectsProvider = FutureProvider<List<ProjectModel>>((ref) async {
  final myProjects = await ref.watch(myProjectsProvider.future);
  return myProjects.where((p) => p.type == '2' && p.status == '1' && p.visible).toList();
});

// ── 프로젝트 선택 조작 헬퍼 ────────────────────────────────────────────────────────

void selectProject(WidgetRef ref, ProjectModel? project) {
  if (project == null) {
    ref.read(selectedProjectProvider.notifier).state = null;
  } else {
    ref.read(selectedProjectProvider.notifier).state = SelectedProject(
      pk: project.pk,
      name: project.name,
      slug: project.slug,
      description: project.description,
      type: project.type,
      status: project.status,
      isPublic: project.isPublic,
      myPerms: project.myPerms,
      module: project.module,
    );
  }
}
