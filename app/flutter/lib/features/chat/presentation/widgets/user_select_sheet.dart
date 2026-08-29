import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/models/user_model.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/providers/dio_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../../../../core/widgets/user_avatar.dart';
import '../../data/chat_repository.dart';
import '../../providers/chat_provider.dart';

/// 1:1 DM 가능 대상자 목록 프로바이더 (본사 재직 스태프 + 활성 워크스페이스 멤버 전체)
final allMembersProvider = FutureProvider.autoDispose<List<UserModel>>((ref) async {
  final dio = ref.watch(dioProvider);
  final res = await dio.get('/api/v1/chat-room/available-users/');
  final dynamic data = res.data;

  List<dynamic> list = [];
  if (data is List) {
    list = data;
  } else if (data is Map<String, dynamic> && data['results'] is List) {
    list = data['results'] as List<dynamic>;
  }

  return list
      .map((json) => UserModel.fromJson(json as Map<String, dynamic>))
      .toList();
});

/// 1:1 대화 상대 선택 바텀시트 모달
class UserSelectSheet extends ConsumerStatefulWidget {
  const UserSelectSheet({super.key});

  static Future<void> show(BuildContext context) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const UserSelectSheet(),
    );
  }

  @override
  ConsumerState<UserSelectSheet> createState() => _UserSelectSheetState();
}

class _UserSelectSheetState extends ConsumerState<UserSelectSheet> {
  final _searchController = TextEditingController();
  String _searchQuery = '';
  bool _isCreating = false;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _startDm(UserModel targetUser) async {
    setState(() => _isCreating = true);
    try {
      final repo = ref.read(chatRepositoryProvider);
      final room = await repo.getOrCreateDm(targetUser.pk);

      if (mounted) {
        Navigator.pop(context); // 시트 닫기
        ref.invalidate(chatRoomsProvider);
        ref.invalidate(totalUnreadChatCountProvider);
        context.push('/chat/${room.id}', extra: room);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('대화방 생성 실패: $e'),
            backgroundColor: context.colors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isCreating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final membersAsync = ref.watch(allMembersProvider);
    final currentUser = ref.watch(currentUserProvider).valueOrNull;
    final currentUserId = currentUser?.pk ?? 0;

    return Container(
      height: MediaQuery.of(context).size.height * 0.75,
      decoration: BoxDecoration(
        color: context.colors.bgSurface,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
      ),
      child: Column(
        children: [
          // ── 드래그 핸들 ──────────────────────────────────────────
          Container(
            margin: const EdgeInsets.symmetric(vertical: 10),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: context.colors.border,
              borderRadius: BorderRadius.circular(2),
            ),
          ),

          // ── 타이틀 바 ────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '1:1 대화 상대 선택',
                  style: AppTextStyles.titleMd.copyWith(
                    fontWeight: FontWeight.bold,
                    color: context.colors.textPrimary,
                  ),
                ),
                IconButton(
                  icon: Icon(Icons.close_rounded, color: context.colors.textMuted),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
          ),
          Divider(color: context.colors.border, height: 1),

          // ── 검색 입력창 ──────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.all(12),
            child: Container(
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: TextField(
                controller: _searchController,
                onChanged: (v) => setState(() => _searchQuery = v.trim().toLowerCase()),
                style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
                decoration: InputDecoration(
                  hintText: '이름, 부서 또는 계정 검색',
                  hintStyle: TextStyle(color: context.colors.textMuted, fontSize: 13),
                  prefixIcon: Icon(Icons.search_rounded, size: 20, color: context.colors.textMuted),
                  border: InputBorder.none,
                  contentPadding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
          ),

          // ── 직원 목록 ────────────────────────────────────────────
          Expanded(
            child: _isCreating
                ? const Center(child: CircularProgressIndicator())
                : membersAsync.when(
                    loading: () => const Padding(
                      padding: EdgeInsets.all(16),
                      child: LoadingShimmer(itemHeight: 56, itemCount: 6),
                    ),
                    error: (err, _) => ErrorView(
                      message: '직원 목록을 불러오지 못했습니다.',
                      onRetry: () => ref.invalidate(allMembersProvider),
                    ),
                    data: (members) {
                      final filtered = members.where((m) {
                        if (m.pk == currentUserId) return false;
                        if (_searchQuery.isEmpty) return true;
                        final name = (m.profile?.name ?? '').toLowerCase();
                        final username = m.username.toLowerCase();
                        return name.contains(_searchQuery) || username.contains(_searchQuery);
                      }).toList();

                      if (filtered.isEmpty) {
                        return Center(
                          child: Text(
                            '검색된 대화 상대가 없습니다.',
                            style: AppTextStyles.bodyMd.copyWith(color: context.colors.textMuted),
                          ),
                        );
                      }

                      return ListView.separated(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        itemCount: filtered.length,
                        separatorBuilder: (_, __) => Divider(color: context.colors.border, height: 1),
                        itemBuilder: (context, index) {
                          final user = filtered[index];
                          final displayName = user.profile?.name?.isNotEmpty == true
                              ? '${user.profile!.name} (${user.username})'
                              : user.username;

                          return ListTile(
                            contentPadding: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
                            leading: UserAvatar(user: user, radius: 18),
                            title: Text(
                              displayName,
                              style: AppTextStyles.bodyMd.copyWith(
                                fontWeight: FontWeight.w600,
                                color: context.colors.textPrimary,
                              ),
                            ),
                            subtitle: user.profile?.cellPhone?.isNotEmpty == true
                                ? Text(
                                    user.profile!.cellPhone!,
                                    style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                                  )
                                : null,
                            trailing: Icon(
                              Icons.chat_bubble_outline_rounded,
                              size: 20,
                              color: context.colors.accentWork,
                            ),
                            onTap: () => _startDm(user),
                          );
                        },
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
