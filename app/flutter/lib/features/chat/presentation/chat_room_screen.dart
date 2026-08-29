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

/// 실시간 대화방 화면 (채팅창)
class ChatRoomScreen extends ConsumerStatefulWidget {
  final int roomId;
  final ChatRoomModel? initialRoom;

  const ChatRoomScreen({
    super.key,
    required this.roomId,
    this.initialRoom,
  });

  @override
  ConsumerState<ChatRoomScreen> createState() => _ChatRoomScreenState();
}

class _ChatRoomScreenState extends ConsumerState<ChatRoomScreen> {
  final _textController = TextEditingController();
  final _scrollController = ScrollController();

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _onSend() {
    final text = _textController.text.trim();
    if (text.isEmpty) return;

    ref.read(chatRoomNotifierProvider(widget.roomId).notifier).sendMessage(
      content: text,
      type: ChatMessageType.text,
    );
    _textController.clear();
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    final messagesAsync = ref.watch(chatRoomNotifierProvider(widget.roomId));
    final currentUser = ref.watch(currentUserProvider).valueOrNull;
    final currentUserId = currentUser?.pk ?? 0;

    final roomTitle = widget.initialRoom?.getDisplayName(currentUserId) ?? '대화방 #${widget.roomId}';

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      appBar: AppBar(
        backgroundColor: context.colors.bgSurface,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new_rounded, color: context.colors.textPrimary, size: 20),
          onPressed: () => context.pop(),
        ),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              roomTitle,
              style: AppTextStyles.titleSm.copyWith(
                fontWeight: FontWeight.bold,
                color: context.colors.textPrimary,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            if (widget.initialRoom?.projectName != null)
              Text(
                widget.initialRoom!.projectName!,
                style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
              ),
          ],
        ),
      ),
      body: Column(
        children: [
          // ── 1. 메시지 목록 ─────────────────────────────────────────
          Expanded(
            child: messagesAsync.when(
              loading: () => const Padding(
                padding: EdgeInsets.all(16),
                child: LoadingShimmer(itemHeight: 60, itemCount: 6),
              ),
              error: (err, _) => ErrorView(
                message: '메시지를 불러오지 못했습니다.',
                onRetry: () => ref.invalidate(chatRoomNotifierProvider(widget.roomId)),
              ),
              data: (messages) {
                WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());

                if (messages.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.chat_bubble_outline_rounded, size: 48, color: context.colors.textMuted.withAlpha(120)),
                        const SizedBox(height: 12),
                        Text(
                          '첫 메시지를 보내 대화를 시작해보세요.',
                          style: AppTextStyles.bodyMd.copyWith(color: context.colors.textMuted),
                        ),
                      ],
                    ),
                  );
                }

                return ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  itemCount: messages.length,
                  itemBuilder: (context, index) {
                    final msg = messages[index];
                    final isMe = msg.sender?.pk == currentUserId;
                    final showSender = !isMe && (index == 0 || messages[index - 1].sender?.pk != msg.sender?.pk);

                    return _buildMessageItem(context, msg, isMe, showSender);
                  },
                );
              },
            ),
          ),

          // ── 2. 메시지 입력창 ────────────────────────────────────────
          _buildInputBar(context),
        ],
      ),
    );
  }

  Widget _buildMessageItem(BuildContext context, ChatMessageModel msg, bool isMe, bool showSender) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: isMe ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          if (showSender && msg.sender != null)
            Padding(
              padding: const EdgeInsets.only(left: 4, bottom: 4),
              child: Text(
                msg.sender!.username,
                style: AppTextStyles.caption.copyWith(
                  fontWeight: FontWeight.bold,
                  color: context.colors.textSecond,
                ),
              ),
            ),
          Row(
            mainAxisAlignment: isMe ? MainAxisAlignment.end : MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              if (isMe) ...[
                Text(
                  _formatTime(msg.created),
                  style: TextStyle(fontSize: 10, color: context.colors.textMuted),
                ),
                const SizedBox(width: 6),
              ],
              Flexible(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: isMe
                        ? context.colors.accentWork
                        : context.colors.bgCard,
                    borderRadius: BorderRadius.only(
                      topLeft: const Radius.circular(14),
                      topRight: const Radius.circular(14),
                      bottomLeft: Radius.circular(isMe ? 14 : 2),
                      bottomRight: Radius.circular(isMe ? 2 : 14),
                    ),
                    border: isMe ? null : Border.all(color: context.colors.border, width: 0.8),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withAlpha(8),
                        blurRadius: 3,
                        offset: const Offset(0, 1),
                      ),
                    ],
                  ),
                  child: _buildMessageContent(context, msg, isMe),
                ),
              ),
              if (!isMe) ...[
                const SizedBox(width: 6),
                Text(
                  _formatTime(msg.created),
                  style: TextStyle(fontSize: 10, color: context.colors.textMuted),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMessageContent(BuildContext context, ChatMessageModel msg, bool isMe) {
    // 📋 IBS 리치 링크 카드 렌더링
    if (msg.messageType == ChatMessageType.issue ||
        msg.messageType == ChatMessageType.meeting ||
        msg.messageType == ChatMessageType.approval) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                msg.messageType == ChatMessageType.issue
                    ? Icons.task_alt_rounded
                    : (msg.messageType == ChatMessageType.meeting
                        ? Icons.event_note_rounded
                        : Icons.fact_check_rounded),
                size: 16,
                color: isMe ? Colors.white : context.colors.accentWork,
              ),
              const SizedBox(width: 6),
              Text(
                msg.refTitle.isNotEmpty ? msg.refTitle : msg.content,
                style: TextStyle(
                  color: isMe ? Colors.white : context.colors.textPrimary,
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                ),
              ),
            ],
          ),
          if (msg.refSub.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              msg.refSub,
              style: TextStyle(
                color: isMe ? Colors.white.withAlpha(200) : context.colors.textMuted,
                fontSize: 11,
              ),
            ),
          ],
        ],
      );
    }

    // 일반 텍스트
    return Text(
      msg.content,
      style: TextStyle(
        color: isMe ? Colors.white : context.colors.textPrimary,
        fontSize: 14,
        height: 1.35,
      ),
    );
  }

  Widget _buildInputBar(BuildContext context) {
    return Container(
      color: context.colors.bgSurface,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: SafeArea(
        top: false,
        child: Row(
          children: [
            IconButton(
              icon: Icon(Icons.add_circle_outline_rounded, color: context.colors.textMuted, size: 24),
              onPressed: () {
                // 사진 / 파일 / 업무 공유 시트
              },
            ),
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: context.colors.bgCard,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: context.colors.border, width: 0.8),
                ),
                padding: const EdgeInsets.symmetric(horizontal: 14),
                child: TextField(
                  controller: _textController,
                  onSubmitted: (_) => _onSend(),
                  style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
                  decoration: InputDecoration(
                    hintText: '메시지를 입력하세요...',
                    hintStyle: TextStyle(color: context.colors.textMuted, fontSize: 13),
                    border: InputBorder.none,
                    isDense: true,
                    contentPadding: const EdgeInsets.symmetric(vertical: 10),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              icon: Icon(Icons.send_rounded, color: context.colors.accentWork, size: 22),
              onPressed: _onSend,
            ),
          ],
        ),
      ),
    );
  }

  String _formatTime(DateTime time) {
    final local = time.toLocal();
    return DateFormat('a h:mm', 'ko').format(local);
  }
}
