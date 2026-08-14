import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/project_provider.dart';
import '../data/models/project_model.dart';
import '../data/project_repository.dart';

// ── 프로젝트 전체 목록 프로바이더 ───────────────────────────────────────────────────

final projectListProvider = FutureProvider<List<ProjectModel>>((ref) async {
  return ref.watch(projectRepositoryProvider).fetchProjects();
});

// ── 전역 활성 워크스페이스 목록 프로바이더 (Vue Header의 allActiveProjects와 100% 동일) ──
/// 상태가 활성(status == '1')이고 가시성(visible == true)이 있는 프로젝트 목록
final activeWorkspaceListProvider = FutureProvider<List<ProjectModel>>((ref) async {
  final all = await ref.watch(projectListProvider.future);
  return all.where((p) => p.status == '1' && p.visible).toList();
});

// ── 내 워크스페이스 목록 프로바이더 (/api/v1/issue-project/my_projects/) ─────────────
final myProjectsProvider = FutureProvider<List<ProjectModel>>((ref) async {
  return ref.watch(projectRepositoryProvider).fetchMyProjects();
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
/// Vue의 `myProjects.filter(pjt => pjt.module?.document)`와 100% 동일
final docFormProjectsProvider = FutureProvider<List<ProjectModel>>((ref) async {
  final myProjects = await ref.watch(myProjectsProvider.future);
  // 문서 모듈이 활성화된(module?.document != false) 프로젝트만 주입
  final filtered = myProjects.where((p) => p.module?.document ?? true).toList();
  // myProjects가 비어있을 경우 전체 목록에서 폴백
  if (filtered.isNotEmpty) return filtered;
  final all = await ref.watch(projectListProvider.future);
  return all.where((p) => p.module?.document ?? true).toList();
});

// ── 프로젝트 상세 프로바이더 (members, versions, categories 포함) ─────────────────
final projectDetailProvider =
    FutureProvider.family<ProjectModel, String>((ref, slug) async {
  return ref.watch(projectRepositoryProvider).fetchProjectDetail(slug);
});

// ── 부동산 개발 프로젝트 전용 프로바이더 (type == '2') ──────────────────────────────
/// 계약/수납/재무/문서 모듈용 (부동산 개발 타입 프로젝트만 필터링)
final realEstateProjectsProvider = FutureProvider<List<ProjectModel>>((ref) async {
  final projects = await ref.watch(projectListProvider.future);
  return projects.where((p) => p.type == '2').toList();
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
      isPublic: project.isPublic,
      myPerms: project.myPerms,
    );
  }
}
