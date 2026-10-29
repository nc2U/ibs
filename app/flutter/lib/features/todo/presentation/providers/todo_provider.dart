import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/providers/dio_provider.dart';
import '../../data/models/todo_model.dart';
import '../../data/repositories/todo_repository.dart';

final todoRepositoryProvider = Provider<TodoRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return TodoRepository(dio);
});

enum TodoFilter {
  all,
  active,
  completed,
}

final todoFilterProvider = StateProvider<TodoFilter>((ref) => TodoFilter.all);

class TodoListNotifier extends AsyncNotifier<List<TodoItem>> {
  @override
  Future<List<TodoItem>> build() async {
    final currentUser = ref.watch(currentUserProvider).valueOrNull;
    return _fetchTodos(currentUser?.pk);
  }

  Future<List<TodoItem>> _fetchTodos(int? userId) async {
    final repo = ref.read(todoRepositoryProvider);
    final list = await repo.getTodos(userId: userId);
    // 모바일 To-Do 특성에 맞게 최신순(id 내림차순)으로 일관되게 정렬
    list.sort((a, b) => b.pk.compareTo(a.pk));
    return list;
  }

  Future<void> refresh({bool showLoading = false}) async {
    final hasExistingData = state.hasValue;
    if (showLoading || !hasExistingData) {
      state = const AsyncLoading();
    }
    final currentUser = ref.read(currentUserProvider).valueOrNull;
    try {
      final list = await _fetchTodos(currentUser?.pk);
      state = AsyncData(list);
    } catch (e, st) {
      if (!hasExistingData || showLoading) {
        state = AsyncError(e, st);
      }
    }
  }

  /// 할일 추가 (성공 시 true, 실패 시 기존 목록을 유지하고 false 반환)
  Future<bool> addTodo(String title) async {
    final trimmed = title.trim();
    if (trimmed.isEmpty) return false;

    final currentUser = ref.read(currentUserProvider).valueOrNull;
    if (currentUser == null) return false;

    final repo = ref.read(todoRepositoryProvider);
    try {
      final newItem = await repo.createTodo(
        title: trimmed,
        userId: currentUser.pk,
      );
      final currentList = state.valueOrNull ?? [];
      state = AsyncData([newItem, ...currentList]);
      return true;
    } catch (_) {
      return false;
    }
  }

  /// 완료/미완료 토글 (낙관적 업데이트)
  Future<bool> toggleCompleted(TodoItem item) async {
    final previousList = state.valueOrNull ?? [];
    final updatedList = previousList.map((t) {
      if (t.pk == item.pk) {
        return t.copyWith(completed: !t.completed);
      }
      return t;
    }).toList();

    // 1. 낙관적 즉시 UI 반영
    state = AsyncData(updatedList);

    try {
      final repo = ref.read(todoRepositoryProvider);
      await repo.updateTodo(id: item.pk, completed: !item.completed);
      return true;
    } catch (_) {
      // 실패 시 롤백
      state = AsyncData(previousList);
      return false;
    }
  }

  /// 제목 수정
  Future<bool> updateTitle(int id, String newTitle) async {
    final trimmed = newTitle.trim();
    if (trimmed.isEmpty) return false;

    final previousList = state.valueOrNull ?? [];
    final updatedList = previousList.map((t) {
      if (t.pk == id) {
        return t.copyWith(title: trimmed);
      }
      return t;
    }).toList();

    state = AsyncData(updatedList);

    try {
      final repo = ref.read(todoRepositoryProvider);
      await repo.updateTodo(id: id, title: trimmed);
      return true;
    } catch (_) {
      state = AsyncData(previousList);
      return false;
    }
  }

  /// 할일 삭제 (소프트 삭제)
  Future<bool> deleteTodo(int id) async {
    final previousList = state.valueOrNull ?? [];
    final updatedList = previousList.where((t) => t.pk != id).toList();

    // 낙관적 즉시 제거
    state = AsyncData(updatedList);

    try {
      final repo = ref.read(todoRepositoryProvider);
      await repo.softDeleteTodo(id);
      return true;
    } catch (_) {
      state = AsyncData(previousList);
      return false;
    }
  }

  /// 할일을 워크스페이스 업무(Issue)로 전환
  /// 성공 시 서버가 반환한 할일(완료 처리 + 업무 연결)로 목록을 갱신하고 결과를 반환한다.
  /// 실패 시 예외를 그대로 던져 호출 측(UI)에서 에러 메시지를 표시할 수 있게 한다.
  Future<TodoConvertResult> convertToIssue({
    required TodoItem item,
    required int projectId,
    required String subject,
    String description = '',
  }) async {
    final repo = ref.read(todoRepositoryProvider);
    final result = await repo.convertToIssue(
      id: item.pk,
      projectId: projectId,
      subject: subject,
      description: description,
    );

    final currentList = state.valueOrNull ?? [];
    state = AsyncData(
      currentList.map((t) => t.pk == result.todo.pk ? result.todo : t).toList(),
    );
    return result;
  }

  /// 완료된 할일 전체 일괄 삭제
  Future<bool> clearCompletedTodos() async {
    final previousList = state.valueOrNull ?? [];
    final completedItems = previousList.where((t) => t.completed).toList();
    if (completedItems.isEmpty) return true;

    // 완료된 항목을 제외한 미완료 항목만 남김
    final activeList = previousList.where((t) => !t.completed).toList();
    state = AsyncData(activeList);

    try {
      final repo = ref.read(todoRepositoryProvider);
      // 백그라운드 병렬 소프트 삭제 처리
      await Future.wait(
        completedItems.map((item) => repo.softDeleteTodo(item.pk)),
      );
      return true;
    } catch (_) {
      state = AsyncData(previousList);
      return false;
    }
  }
}

final todoListProvider =
    AsyncNotifierProvider<TodoListNotifier, List<TodoItem>>(TodoListNotifier.new);

/// 필터가 적용된 할일 목록
final filteredTodoListProvider = Provider<List<TodoItem>>((ref) {
  final todos = ref.watch(todoListProvider).valueOrNull ?? [];
  final filter = ref.watch(todoFilterProvider);

  switch (filter) {
    case TodoFilter.all:
      return todos;
    case TodoFilter.active:
      return todos.where((t) => !t.completed).toList();
    case TodoFilter.completed:
      return todos.where((t) => t.completed).toList();
  }
});

/// 미완료 할일 개수 프로바이더 (AppBar 뱃지용)
final pendingTodoCountProvider = Provider<int>((ref) {
  final todos = ref.watch(todoListProvider).valueOrNull ?? [];
  return todos.where((t) => !t.completed).length;
});
