import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/common_models.dart';

/// 공용 문서함 진입 컨텍스트 모델
enum DocsScopeType { all, workspace, project }

class DocsContext {
  final DocsScopeType scopeType;
  final SimpleProjectModel? project; // IssueProject (type='1' 워크스페이스 or type='2' 프로젝트)

  const DocsContext._({required this.scopeType, this.project});

  factory DocsContext.all() => const DocsContext._(scopeType: DocsScopeType.all);

  factory DocsContext.workspace(SimpleProjectModel ws) =>
      DocsContext._(scopeType: DocsScopeType.workspace, project: ws);

  factory DocsContext.project(SimpleProjectModel proj) =>
      DocsContext._(scopeType: DocsScopeType.project, project: proj);

  String get displayName {
    switch (scopeType) {
      case DocsScopeType.all:
        return '전체 문서';
      case DocsScopeType.workspace:
        return '📋 ${project?.name ?? "워크스페이스"} 문서';
      case DocsScopeType.project:
        return '🏗 ${project?.name ?? "프로젝트"} 문서';
    }
  }
}

/// 현재 선택된 공용 문서함 컨텍스트 StateProvider
final docsContextProvider = StateProvider<DocsContext>((ref) {
  return DocsContext.all();
});
