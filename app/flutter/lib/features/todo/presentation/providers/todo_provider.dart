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
    return _fetchTodos();
  }

  Future<List<TodoItem>> _fetchTodos() async {
    final repo = ref.read(todoRepositoryProvider);
    final currentUser = ref.watch(currentUserProvider).valueOrNull;
    return await repo.getTodos(userId: currentUser?.pk);
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _fetchTodos());
  }

  /// 할일 추가
  Future<void> addTodo(String title) async {
    final trimmed = title.trim();
    if (trimmed.isEmpty) return;

    final repo = ref.read(todoRepositoryProvider);
    try {
      final newItem = await repo.createTodo(title: trimmed);
      final currentList = state.valueOrNull ?? [];
      state = AsyncData([newItem, ...currentList]);
    } catch (e, st) {
      state = AsyncError(e, st);
      // 실패 시 재조회로 정합성 보장
      refresh();
    }
  }

  /// 완료/미완료 토글 (낙관적 업데이트)
  Future<void> toggleCompleted(TodoItem item) async {
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
    } catch (e) {
      // 실패 시 롤백
      state = AsyncData(previousList);
    }
  }

  /// 제목 수정
  Future<void> updateTitle(int id, String newTitle) async {
    final trimmed = newTitle.trim();
    if (trimmed.isEmpty) return;

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
    } catch (e) {
      state = AsyncData(previousList);
    }
  }

  /// 할일 삭제 (소프트 삭제)
  Future<void> deleteTodo(int id) async {
    final previousList = state.valueOrNull ?? [];
    final updatedList = previousList.where((t) => t.pk != id).toList();

    // 낙관적 즉시 제거
    state = AsyncData(updatedList);

    try {
      final repo = ref.read(todoRepositoryProvider);
      await repo.softDeleteTodo(id);
    } catch (e) {
      state = AsyncData(previousList);
    }
  }

  /// 완료된 할일 전체 일괄 삭제
  Future<void> clearCompletedTodos() async {
    final previousList = state.valueOrNull ?? [];
    final completedItems = previousList.where((t) => t.completed).toList();
    if (completedItems.isEmpty) return;

    // 완료된 항목을 제외한 미완료 항목만 남김
    final activeList = previousList.where((t) => !t.completed).toList();
    state = AsyncData(activeList);

    try {
      final repo = ref.read(todoRepositoryProvider);
      // 백그라운드 병렬 소프트 삭제 처리
      await Future.wait(
        completedItems.map((item) => repo.softDeleteTodo(item.pk)),
      );
    } catch (e) {
      state = AsyncData(previousList);
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
