import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../data/models/chat_model.dart';
import '../providers/chat_provider.dart';
import 'widgets/user_select_sheet.dart';

/// 메신저 대화방 목록 화면
class ChatRoomListScreen extends ConsumerStatefulWidget {
  const ChatRoomListScreen({super.key});

  @override
  ConsumerState<ChatRoomListScreen> createState() => _ChatRoomListScreenState();
}

class _ChatRoomListScreenState extends ConsumerState<ChatRoomListScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final chatRoomsAsync = ref.watch(chatRoomsProvider);
    final currentUser = ref.watch(currentUserProvider).valueOrNull;
    final currentUserId = currentUser?.pk ?? 0;

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      appBar: AppBar(
        backgroundColor: context.colors.bgSurface,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new_rounded, color: context.colors.textPrimary, size: 20),
          onPressed: () => context.pop(),
        ),
        title: Text(
          '실시간 메신저',
          style: AppTextStyles.titleMd.copyWith(
            fontWeight: FontWeight.bold,
            color: context.colors.textPrimary,
          ),
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.person_add_alt_1_rounded, color: context.colors.accentWork, size: 22),
            tooltip: '새 대화 상대 선택',
            onPressed: () => UserSelectSheet.show(context),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(48),
          child: Container(
            decoration: BoxDecoration(
              border: Border(bottom: BorderSide(color: context.colors.border, width: 0.8)),
            ),
            child: Builder(
              builder: (context) {
                final rooms = chatRoomsAsync.valueOrNull ?? [];
                final channelUnread = rooms
                    .where((r) => r.roomType == ChatRoomType.channel)
                    .fold<int>(0, (sum, r) => sum + r.unreadCount);
                final directUnread = rooms
                    .where((r) => r.roomType != ChatRoomType.channel)
                    .fold<int>(0, (sum, r) => sum + r.unreadCount);

                return TabBar(
                  controller: _tabController,
                  indicatorColor: context.colors.accentWork,
                  indicatorWeight: 2.5,
                  labelColor: context.colors.accentWork,
                  unselectedLabelColor: context.colors.textMuted,
                  labelStyle: AppTextStyles.titleSm.copyWith(fontWeight: FontWeight.bold),
                  tabs: [
                    Tab(
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Text('🏢 워크스페이스 채널'),
                          if (channelUnread > 0) ...[
                            const SizedBox(width: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: Colors.redAccent,
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Text(
                                '$channelUnread',
                                style: const TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                    Tab(
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Text('🔒 1:1 다이렉트 (DM)'),
                          if (directUnread > 0) ...[
                            const SizedBox(width: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: Colors.redAccent,
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Text(
                                '$directUnread',
                                style: const TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => UserSelectSheet.show(context),
        backgroundColor: context.colors.accentWork,
        icon: const Icon(Icons.chat_bubble_outline_rounded, color: Colors.white, size: 18),
        label: const Text('1:1 대화 시작', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(chatRoomsProvider),
        child: chatRoomsAsync.when(
          loading: () => const Padding(
            padding: EdgeInsets.all(16),
            child: LoadingShimmer(itemHeight: 76, itemCount: 5),
          ),
          error: (err, _) => ErrorView(
            message: '대화방 목록을 불러오지 못했습니다.',
            onRetry: () => ref.invalidate(chatRoomsProvider),
          ),
          data: (rooms) {
            final channelRooms = rooms.where((r) => r.roomType == ChatRoomType.channel).toList();
            final directRooms = rooms.where((r) => r.roomType != ChatRoomType.channel).toList();

            return TabBarView(
              controller: _tabController,
              children: [
                _buildRoomList(context, channelRooms, currentUserId, isChannel: true),
                _buildRoomList(context, directRooms, currentUserId, isChannel: false),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildRoomList(
    BuildContext context,
    List<ChatRoomModel> rooms,
    int currentUserId, {
    required bool isChannel,
  }) {
    if (rooms.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                isChannel ? Icons.tag_rounded : Icons.forum_outlined,
                size: 48,
                color: context.colors.textMuted.withAlpha(120),
              ),
              const SizedBox(height: 12),
              Text(
                isChannel ? '참여 중인 워크스페이스 채널이 없습니다.' : '진행 중인 1:1 대화가 없습니다.',
                style: AppTextStyles.bodyMd.copyWith(color: context.colors.textMuted),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () => UserSelectSheet.show(context),
                icon: const Icon(Icons.person_add_alt_1_rounded, size: 18),
                label: const Text('대화 상대 선택하기'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: context.colors.accentWork,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
            ],
          ),
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: rooms.length,
      separatorBuilder: (_, __) => Divider(color: context.colors.border, height: 1, indent: 68),
      itemBuilder: (context, index) {
        final room = rooms[index];
        final displayName = room.getDisplayName(currentUserId);
        final lastMsg = room.lastMessage;

        return InkWell(
          onTap: () {
            context.push('/chat/${room.id}', extra: room).then((_) {
              ref.invalidate(chatRoomsProvider);
              ref.invalidate(totalUnreadChatCountProvider);
            });
          },
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              children: [
                // ── 아바타 / 채널 아이콘 ──────────────────────────────
                Container(
                  width: 46,
                  height: 46,
                  decoration: BoxDecoration(
                    color: isChannel
                        ? context.colors.accentWork.withAlpha(25)
                        : context.colors.accentCorp.withAlpha(25),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: isChannel
                          ? context.colors.accentWork.withAlpha(50)
                          : context.colors.accentCorp.withAlpha(50),
                    ),
                  ),
                  child: Icon(
                    isChannel ? Icons.tag_rounded : Icons.person_rounded,
                    color: isChannel ? context.colors.accentWork : context.colors.accentCorp,
                    size: 22,
                  ),
                ),
                const SizedBox(width: 14),

                // ── 방 정보 및 최근 메시지 ─────────────────────────
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Row(
                              children: [
                                Flexible(
                                  child: Text(
                                    displayName,
                                    style: AppTextStyles.titleSm.copyWith(
                                      fontWeight: FontWeight.bold,
                                      color: context.colors.textPrimary,
                                    ),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                                if (isChannel && room.memberCount > 0) ...[
                                  const SizedBox(width: 4),
                                  Text(
                                    '${room.memberCount}',
                                    style: TextStyle(fontSize: 12, color: context.colors.textMuted),
                                  ),
                                ],
                              ],
                            ),
                          ),
                          if (lastMsg != null)
                            Text(
                              _formatTime(lastMsg.created),
                              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                            ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              lastMsg != null
                                  ? '${lastMsg.senderName}: ${lastMsg.content}'
                                  : (room.description.isNotEmpty ? room.description : '대화를 시작해보세요.'),
                              style: AppTextStyles.bodySm.copyWith(
                                color: room.unreadCount > 0
                                    ? context.colors.textPrimary
                                    : context.colors.textMuted,
                                fontWeight: room.unreadCount > 0 ? FontWeight.w600 : FontWeight.normal,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          if (room.unreadCount > 0) ...[
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                              decoration: BoxDecoration(
                                color: Colors.redAccent,
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Text(
                                '${room.unreadCount > 99 ? '99+' : room.unreadCount}',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  String _formatTime(DateTime time) {
    final now = DateTime.now();
    final localTime = time.toLocal();
    if (localTime.year == now.year && localTime.month == now.month && localTime.day == now.day) {
      return DateFormat('a h:mm', 'ko').format(localTime);
    }
    return DateFormat('M월 d일', 'ko').format(localTime);
  }
}
