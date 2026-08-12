import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/project_provider.dart';
import '../data/models/project_model.dart';
import '../data/project_repository.dart';

// ── 프로젝트 목록 프로바이더 ───────────────────────────────────────────────────

final projectListProvider = FutureProvider<List<ProjectModel>>((ref) async {
  return ref.watch(projectRepositoryProvider).fetchProjects();
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
      isPublic: project.visible,
    );
  }
}
