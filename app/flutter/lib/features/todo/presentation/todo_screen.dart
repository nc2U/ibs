import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../data/models/todo_model.dart';
import 'providers/todo_provider.dart';

class TodoScreen extends ConsumerStatefulWidget {
  const TodoScreen({super.key});

  @override
  ConsumerState<TodoScreen> createState() => _TodoScreenState();
}

class _TodoScreenState extends ConsumerState<TodoScreen> {
  final TextEditingController _inputController = TextEditingController();
  final FocusNode _focusNode = FocusNode();
  bool _isAdding = false;

  @override
  void dispose() {
    _inputController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  Future<void> _submitNewTodo() async {
    final text = _inputController.text.trim();
    if (text.isEmpty) return;

    setState(() => _isAdding = true);
    await ref.read(todoListProvider.notifier).addTodo(text);
    if (mounted) {
      _inputController.clear();
      setState(() => _isAdding = false);
    }
  }

  void _showEditDialog(TodoItem item) {
    final editController = TextEditingController(text: item.title);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgPrimary,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text(
          '할일 수정',
          style: AppTextStyles.titleMd.copyWith(
            fontWeight: FontWeight.bold,
            color: context.colors.textPrimary,
          ),
        ),
        content: TextField(
          controller: editController,
          autofocus: true,
          maxLength: 50,
          style: TextStyle(color: context.colors.textPrimary),
          decoration: InputDecoration(
            hintText: '할일을 입력하세요 (최대 50자)',
            hintStyle: TextStyle(color: context.colors.textMuted),
            counterStyle: TextStyle(color: context.colors.textMuted, fontSize: 11),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: BorderSide(color: context.colors.border),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: BorderSide(color: context.colors.accentWork, width: 2),
            ),
          ),
          onSubmitted: (val) {
            final newTitle = val.trim();
            if (newTitle.isNotEmpty && newTitle != item.title) {
              ref.read(todoListProvider.notifier).updateTitle(item.pk, newTitle);
            }
            Navigator.of(ctx).pop();
          },
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: context.colors.accentWork,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            onPressed: () {
              final newTitle = editController.text.trim();
              if (newTitle.isNotEmpty && newTitle != item.title) {
                ref.read(todoListProvider.notifier).updateTitle(item.pk, newTitle);
              }
              Navigator.of(ctx).pop();
            },
            child: const Text('저장'),
          ),
        ],
      ),
    );
  }

  Future<void> _confirmDeleteItem(TodoItem item) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgPrimary,
        title: Text(
          '할일 삭제',
          style: AppTextStyles.titleMd.copyWith(
            fontWeight: FontWeight.bold,
            color: context.colors.textPrimary,
          ),
        ),
        content: Text(
          '"${item.title}" 항목을 삭제하시겠습니까?',
          style: AppTextStyles.bodyMd.copyWith(
            color: context.colors.textSecond,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Colors.redAccent,
            ),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('삭제'),
          ),
        ],
      ),
    );

    if (confirmed == true && mounted) {
      ref.read(todoListProvider.notifier).deleteTodo(item.pk);
    }
  }

  Future<void> _confirmClearCompleted(int completedCount) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgPrimary,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text(
          '완료된 할일 전체 삭제',
          style: AppTextStyles.titleMd.copyWith(
            fontWeight: FontWeight.bold,
            color: context.colors.textPrimary,
          ),
        ),
        content: Text(
          '완료된 $completedCount개의 할일을 모두 삭제하시겠습니까?\n삭제된 내용은 복구되지 않습니다.',
          style: AppTextStyles.bodyMd.copyWith(
            color: context.colors.textSecond,
            height: 1.4,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Colors.redAccent,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('모두 삭제'),
          ),
        ],
      ),
    );

    if (confirmed == true && mounted) {
      await ref.read(todoListProvider.notifier).clearCompletedTodos();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('완료된 할일이 모두 삭제되었습니다.'),
            behavior: SnackBarBehavior.floating,
            duration: Duration(seconds: 2),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final todoState = ref.watch(todoListProvider);
    final filteredTodos = ref.watch(filteredTodoListProvider);
    final currentFilter = ref.watch(todoFilterProvider);
    final allTodos = todoState.valueOrNull ?? [];
    final activeCount = allTodos.where((t) => !t.completed).length;
    final completedCount = allTodos.where((t) => t.completed).length;

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      appBar: AppBar(
        backgroundColor: context.colors.bgPrimary,
        foregroundColor: context.colors.textPrimary,
        elevation: 0,
        title: Text(
          '할일 관리',
          style: AppTextStyles.titleLg.copyWith(
            fontWeight: FontWeight.bold,
            color: context.colors.textPrimary,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: '새로고침',
            onPressed: () => ref.read(todoListProvider.notifier).refresh(),
          ),
        ],
      ),
      body: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: () => FocusScope.of(context).unfocus(),
        child: Column(
          children: [
            // ── 상단 신규 할일 입력창 ──────────────────────────────
            Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: context.colors.bgCard,
              border: Border(
                bottom: BorderSide(color: context.colors.borderSubtle, width: 1),
              ),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Container(
                    decoration: BoxDecoration(
                      color: context.colors.bgInput,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: _focusNode.hasFocus
                            ? context.colors.accentWork
                            : context.colors.border,
                        width: _focusNode.hasFocus ? 1.5 : 1,
                      ),
                    ),
                    child: TextField(
                      controller: _inputController,
                      focusNode: _focusNode,
                      maxLength: 50,
                      style: AppTextStyles.bodyMd.copyWith(
                        color: context.colors.textPrimary,
                      ),
                      textInputAction: TextInputAction.done,
                      onSubmitted: (_) => _submitNewTodo(),
                      decoration: InputDecoration(
                        hintText: '새로운 할일을 입력하세요 (최대 50자)',
                        hintStyle: AppTextStyles.bodyMd.copyWith(
                          color: context.colors.textMuted,
                        ),
                        counterText: '',
                        prefixIcon: Icon(
                          Icons.add_task_rounded,
                          size: 20,
                          color: context.colors.textMuted,
                        ),
                        border: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 14,
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  style: IconButton.styleFrom(
                    backgroundColor: context.colors.accentWork,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    padding: const EdgeInsets.all(12),
                  ),
                  icon: _isAdding
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.arrow_upward_rounded, size: 22),
                  onPressed: _isAdding ? null : _submitNewTodo,
                ),
              ],
            ),
          ),

          // ── 상태 필터 탭 (전체 / 진행 중 / 완료) ────────────────
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            color: context.colors.bgPrimary,
            child: Row(
              children: [
                _buildFilterChip(
                  label: '전체',
                  count: allTodos.length,
                  filter: TodoFilter.all,
                  currentFilter: currentFilter,
                ),
                const SizedBox(width: 8),
                _buildFilterChip(
                  label: '진행 중',
                  count: activeCount,
                  filter: TodoFilter.active,
                  currentFilter: currentFilter,
                ),
                const SizedBox(width: 8),
                _buildFilterChip(
                  label: '완료',
                  count: completedCount,
                  filter: TodoFilter.completed,
                  currentFilter: currentFilter,
                ),
                const Spacer(),
                if (completedCount > 0)
                  TextButton.icon(
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      visualDensity: VisualDensity.compact,
                      foregroundColor: Colors.redAccent,
                    ),
                    icon: const Icon(Icons.delete_sweep_outlined, size: 18),
                    label: const Text(
                      '완료 삭제',
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                    ),
                    onPressed: () => _confirmClearCompleted(completedCount),
                  ),
              ],
            ),
          ),
          Divider(height: 1, thickness: 1, color: context.colors.borderSubtle),

          // ── 할일 리스트 ─────────────────────────────────────────
          Expanded(
            child: todoState.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, _) => Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.error_outline_rounded,
                        size: 40, color: context.colors.textMuted),
                    const SizedBox(height: 12),
                    Text(
                      '할일 목록을 불러오지 못했습니다.',
                      style: AppTextStyles.bodyMd.copyWith(
                        color: context.colors.textSecond,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextButton(
                      onPressed: () =>
                          ref.read(todoListProvider.notifier).refresh(),
                      child: const Text('다시 시도'),
                    ),
                  ],
                ),
              ),
              data: (_) {
                if (filteredTodos.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.checklist_rounded,
                          size: 56,
                          color: context.colors.textMuted.withValues(alpha: 0.5),
                        ),
                        const SizedBox(height: 14),
                        Text(
                          currentFilter == TodoFilter.completed
                              ? '완료된 할일이 없습니다.'
                              : currentFilter == TodoFilter.active
                                  ? '남은 할일이 없습니다. 모두 완료했습니다! 🎉'
                                  : '등록된 할일이 없습니다.\n위 입력창에 새로운 메모를 추가해 보세요.',
                          textAlign: TextAlign.center,
                          style: AppTextStyles.bodyMd.copyWith(
                            color: context.colors.textMuted,
                            height: 1.4,
                          ),
                        ),
                      ],
                    ),
                  );
                }

                return RefreshIndicator(
                  onRefresh: () => ref.read(todoListProvider.notifier).refresh(),
                  child: ListView.separated(
                    keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 12,
                    ),
                    itemCount: filteredTodos.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (ctx, idx) {
                      final item = filteredTodos[idx];
                      return _buildTodoTile(item);
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    ),
  );
}

  Widget _buildFilterChip({
    required String label,
    required int count,
    required TodoFilter filter,
    required TodoFilter currentFilter,
  }) {
    final isSelected = filter == currentFilter;
    return GestureDetector(
      onTap: () => ref.read(todoFilterProvider.notifier).state = filter,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected
              ? context.colors.accentWork.withValues(alpha: 0.12)
              : context.colors.bgCard,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected
                ? context.colors.accentWork
                : context.colors.borderSubtle,
            width: isSelected ? 1.5 : 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              label,
              style: AppTextStyles.bodySm.copyWith(
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                color: isSelected
                    ? context.colors.accentWork
                    : context.colors.textSecond,
              ),
            ),
            const SizedBox(width: 5),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
              decoration: BoxDecoration(
                color: isSelected
                    ? context.colors.accentWork
                    : context.colors.textMuted.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '$count',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: isSelected ? Colors.white : context.colors.textMuted,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTodoTile(TodoItem item) {
    return Dismissible(
      key: ValueKey('todo_${item.pk}'),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.symmetric(horizontal: 20),
        decoration: BoxDecoration(
          color: Colors.redAccent,
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Icon(Icons.delete_outline_rounded, color: Colors.white, size: 24),
      ),
      confirmDismiss: (dir) async {
        return await showDialog<bool>(
          context: context,
          builder: (ctx) => AlertDialog(
            backgroundColor: context.colors.bgPrimary,
            title: Text(
              '할일 삭제',
              style: AppTextStyles.titleMd.copyWith(
                fontWeight: FontWeight.bold,
                color: context.colors.textPrimary,
              ),
            ),
            content: Text(
              '"${item.title}" 항목을 삭제하시겠습니까?',
              style: AppTextStyles.bodyMd.copyWith(
                color: context.colors.textSecond,
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(false),
                child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
              ),
              FilledButton(
                style: FilledButton.styleFrom(
                  backgroundColor: Colors.redAccent,
                ),
                onPressed: () => Navigator.of(ctx).pop(true),
                child: const Text('삭제'),
              ),
            ],
          ),
        );
      },
      onDismissed: (_) {
        ref.read(todoListProvider.notifier).deleteTodo(item.pk);
      },
      child: Material(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: () => ref.read(todoListProvider.notifier).toggleCompleted(item),
          onLongPress: () => _showEditDialog(item),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: item.completed
                    ? context.colors.borderSubtle.withValues(alpha: 0.5)
                    : context.colors.borderSubtle,
                width: 1,
              ),
            ),
            child: Row(
              children: [
                // 체크박스
                SizedBox(
                  width: 24,
                  height: 24,
                  child: Checkbox(
                    value: item.completed,
                    activeColor: context.colors.accentWork,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(5),
                    ),
                    onChanged: (_) {
                      ref.read(todoListProvider.notifier).toggleCompleted(item);
                    },
                  ),
                ),
                const SizedBox(width: 12),
                // 제목
                Expanded(
                  child: Text(
                    item.title,
                    style: AppTextStyles.bodyMd.copyWith(
                      color: item.completed
                          ? context.colors.textMuted
                          : context.colors.textPrimary,
                      decoration: item.completed
                          ? TextDecoration.lineThrough
                          : TextDecoration.none,
                      decorationColor: context.colors.textMuted,
                      height: 1.3,
                    ),
                  ),
                ),
                // 수정 아이콘 버튼
                IconButton(
                  icon: Icon(
                    Icons.edit_outlined,
                    size: 18,
                    color: context.colors.textMuted,
                  ),
                  tooltip: '수정',
                  onPressed: () => _showEditDialog(item),
                ),
                // 완료된 항목이거나 삭제 필요 시 즉시 삭제 가능한 쓰레기통 버튼
                IconButton(
                  icon: Icon(
                    Icons.delete_outline_rounded,
                    size: 19,
                    color: item.completed
                        ? Colors.redAccent.withValues(alpha: 0.8)
                        : context.colors.textMuted,
                  ),
                  tooltip: '삭제',
                  onPressed: () => _confirmDeleteItem(item),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
