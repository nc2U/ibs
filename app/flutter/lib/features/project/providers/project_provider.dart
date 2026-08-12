import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/project_provider.dart';
import '../data/models/project_model.dart';
import '../data/project_repository.dart';

// ── 프로젝트 전체 목록 프로바이더 ───────────────────────────────────────────────────

final projectListProvider = FutureProvider<List<ProjectModel>>((ref) async {
  return ref.watch(projectRepositoryProvider).fetchProjects();
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
      isPublic: project.visible,
    );
  }
}
