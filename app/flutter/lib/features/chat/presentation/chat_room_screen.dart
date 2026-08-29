import 'dart:io';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/api/api_client.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../data/chat_repository.dart';
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
  final _picker = ImagePicker();

  // 답장 대상 메시지 상태
  ChatMessageModel? _replyTarget;
  bool _isUploading = false;

  @override
  void initState() {
    super.initState();
    // 대화방 진입 즉시 최신 메시지 동기화 & 읽음 처리 & 전역 배지 갱신
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(chatRoomNotifierProvider(widget.roomId).notifier).refreshMessages();
      ref.read(chatRepositoryProvider).markAsRead(widget.roomId).then((_) {
        if (mounted) {
          ref.invalidate(totalUnreadChatCountProvider);
          ref.invalidate(chatRoomsProvider);
        }
      });
    });
  }

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final messagesAsync = ref.watch(chatRoomNotifierProvider(widget.roomId));
    final currentUser = ref.watch(currentUserProvider).valueOrNull;
    final currentUserId = currentUser?.pk ?? 0;
    final currentUsername = currentUser?.username ?? '';

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
          mainAxisSize: MainAxisSize.min,
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
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
          ],
        ),
        actions: [
          IconButton(
            icon: Stack(
              clipBehavior: Clip.none,
              children: [
                Icon(Icons.people_alt_outlined, color: context.colors.textPrimary, size: 22),
                if ((widget.initialRoom?.members.length ?? 0) > 0)
                  Positioned(
                    top: -4,
                    right: -6,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                      decoration: BoxDecoration(
                        color: context.colors.accentWork,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        '${widget.initialRoom!.members.length}',
                        style: const TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                          height: 1.1,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
            tooltip: '참여자 목록',
            onPressed: () => _showMembersSheet(widget.initialRoom, currentUserId),
          ),
          const SizedBox(width: 4),
        ],
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
                    final isMe = (msg.sender != null && currentUserId > 0 && msg.sender!.pk == currentUserId) ||
                                 (msg.sender != null && currentUsername.isNotEmpty && msg.sender!.username == currentUsername);
                    final showSender = !isMe && (index == 0 || messages[index - 1].sender?.pk != msg.sender?.pk);

                    return _buildMessageItem(context, msg, isMe, showSender);
                  },
                );
              },
            ),
          ),

          // ── 2. 업로드 인디케이터 ─────────────────────────────────────
          if (_isUploading)
            LinearProgressIndicator(color: context.colors.accentWork, minHeight: 2),

          // ── 3. 답장 대상 프리뷰 바 ──────────────────────────────────
          if (_replyTarget != null) _buildReplyTargetBar(context),

          // ── 4. 메시지 입력창 ────────────────────────────────────────
          _buildInputBar(context),
        ],
      ),
    );
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
      replyToId: _replyTarget?.id,
    );

    _textController.clear();
    setState(() => _replyTarget = null);
    _scrollToBottom();
  }

  // 📷 카메라 / 갤러리 사진 전송
  Future<void> _pickImage(ImageSource source) async {
    try {
      final picked = await _picker.pickImage(source: source, imageQuality: 85);
      if (picked == null) return;

      setState(() => _isUploading = true);
      final file = File(picked.path);

      await ref.read(chatRoomNotifierProvider(widget.roomId).notifier).sendFile(
        file: file,
        messageType: 'image',
        replyToId: _replyTarget?.id,
      );

      setState(() {
        _replyTarget = null;
        _isUploading = false;
      });
      _scrollToBottom();
    } catch (e) {
      setState(() => _isUploading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('사진 전송 실패: $e'), backgroundColor: Colors.redAccent),
        );
      }
    }
  }

  // 📎 일반 문서 / 도면 / PDF 파일 전송
  Future<void> _pickDocument() async {
    try {
      final result = await FilePicker.platform.pickFiles();
      if (result == null || result.files.single.path == null) return;

      setState(() => _isUploading = true);
      final file = File(result.files.single.path!);

      await ref.read(chatRoomNotifierProvider(widget.roomId).notifier).sendFile(
        file: file,
        messageType: 'file',
        replyToId: _replyTarget?.id,
      );

      setState(() {
        _replyTarget = null;
        _isUploading = false;
      });
      _scrollToBottom();
    } catch (e) {
      setState(() => _isUploading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('파일 전송 실패: $e'), backgroundColor: Colors.redAccent),
        );
      }
    }
  }

  // ➕ 하단 첨부 메뉴 바텀시트
  void _showAttachmentSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: context.colors.bgSurface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildAttachOption(
                icon: Icons.photo_library_rounded,
                label: '사진 보관함',
                color: Colors.purpleAccent,
                onTap: () {
                  Navigator.pop(ctx);
                  _pickImage(ImageSource.gallery);
                },
              ),
              _buildAttachOption(
                icon: Icons.camera_alt_rounded,
                label: '카메라',
                color: Colors.blueAccent,
                onTap: () {
                  Navigator.pop(ctx);
                  _pickImage(ImageSource.camera);
                },
              ),
              _buildAttachOption(
                icon: Icons.attach_file_rounded,
                label: '파일 / 도면',
                color: Colors.amber.shade800,
                onTap: () {
                  Navigator.pop(ctx);
                  _pickDocument();
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAttachOption({
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircleAvatar(
              radius: 26,
              backgroundColor: color.withAlpha(30),
              child: Icon(icon, color: color, size: 28),
            ),
            const SizedBox(height: 8),
            Text(label, style: AppTextStyles.caption.copyWith(fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }

  // 💬 말풍선 롱프레스 메뉴 (답장 / 복사 / 전달)
  void _showMessageActionMenu(ChatMessageModel msg) {
    showModalBottomSheet(
      context: context,
      backgroundColor: context.colors.bgSurface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.reply_rounded, color: Colors.blueAccent),
              title: const Text('답장하기'),
              onTap: () {
                Navigator.pop(ctx);
                setState(() => _replyTarget = msg);
              },
            ),
            ListTile(
              leading: const Icon(Icons.content_copy_rounded),
              title: const Text('텍스트 복사'),
              onTap: () {
                Navigator.pop(ctx);
                final text = msg.content.isNotEmpty ? msg.content : (msg.file ?? '');
                Clipboard.setData(ClipboardData(text: text));
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('클립보드에 복사되었습니다.'), duration: Duration(seconds: 1)),
                );
              },
            ),
            ListTile(
              leading: const Icon(Icons.forward_rounded, color: Colors.teal),
              title: const Text('다른 대화방으로 전달'),
              onTap: () {
                Navigator.pop(ctx);
                _showForwardRoomDialog(msg);
              },
            ),
          ],
        ),
      ),
    );
  }

  // 🔗 다른 대화방으로 메시지 전달 모달
  void _showForwardRoomDialog(ChatMessageModel msg) {
    final rooms = ref.read(chatRoomsProvider).valueOrNull ?? [];
    final otherRooms = rooms.where((r) => r.id != widget.roomId).toList();

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgSurface,
        title: const Text('전달할 대화방 선택', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: SizedBox(
          width: double.maxFinite,
          height: 300,
          child: otherRooms.isEmpty
            ? const Center(child: Text('전달 가능한 다른 대화방이 없습니다.'))
            : ListView.separated(
                itemCount: otherRooms.length,
                separatorBuilder: (_, __) => const Divider(height: 1),
                itemBuilder: (c, idx) {
                  final room = otherRooms[idx];
                  final currentUserId = ref.read(currentUserProvider).valueOrNull?.pk ?? 0;
                  return ListTile(
                    leading: CircleAvatar(
                      backgroundColor: context.colors.accentWork.withAlpha(30),
                      child: Icon(
                        room.roomType == ChatRoomType.channel ? Icons.tag_rounded : Icons.person_rounded,
                        color: context.colors.accentWork,
                        size: 18,
                      ),
                    ),
                    title: Text(room.getDisplayName(currentUserId), style: const TextStyle(fontSize: 14)),
                    onTap: () {
                      Navigator.pop(ctx);
                      ref.read(chatRoomNotifierProvider(room.id).notifier).sendMessage(
                        content: msg.content.isNotEmpty ? msg.content : (msg.refTitle.isNotEmpty ? msg.refTitle : '전달된 메시지'),
                        type: msg.messageType,
                      );
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('${room.getDisplayName(currentUserId)} 방으로 전달했습니다.')),
                      );
                    },
                  );
                },
              ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('취소')),
        ],
      ),
    );
  }

  // 👥 참여 멤버 목록 바텀시트
  void _showMembersSheet(ChatRoomModel? room, int currentUserId) {
    final members = room?.members ?? [];
    final isChannel = room?.roomType == ChatRoomType.channel;

    showModalBottomSheet(
      context: context,
      backgroundColor: context.colors.bgSurface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── 헤더 ─────────────────────────────────────────────
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Icon(
                          isChannel ? Icons.group_rounded : Icons.people_alt_rounded,
                          color: context.colors.accentWork,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          isChannel ? '채널 참여 멤버' : '대화방 참여자',
                          style: AppTextStyles.titleSm.copyWith(
                            fontWeight: FontWeight.bold,
                            color: context.colors.textPrimary,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                          decoration: BoxDecoration(
                            color: context.colors.accentWork.withAlpha(30),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Text(
                            '${members.length}명',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: context.colors.accentWork,
                            ),
                          ),
                        ),
                      ],
                    ),
                    IconButton(
                      icon: const Icon(Icons.close_rounded, size: 20),
                      onPressed: () => Navigator.pop(ctx),
                      visualDensity: VisualDensity.compact,
                    ),
                  ],
                ),
              ),
              const Divider(height: 1),

              // ── 멤버 리스트 ─────────────────────────────────────────
              if (members.isEmpty)
                Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Center(
                    child: Text(
                      '참여 멤버 정보를 불러오는 중입니다.',
                      style: TextStyle(color: context.colors.textMuted),
                    ),
                  ),
                )
              else
                Flexible(
                  child: ListView.separated(
                    shrinkWrap: true,
                    itemCount: members.length,
                    separatorBuilder: (_, __) => Divider(color: context.colors.border, height: 1, indent: 64),
                    itemBuilder: (context, index) {
                      final member = members[index];
                      final isMe = member.pk == currentUserId;
                      final displayName = member.name.isNotEmpty
                          ? '${member.name} (${member.username})'
                          : member.username;

                      return ListTile(
                        leading: CircleAvatar(
                          radius: 18,
                          backgroundColor: isMe
                              ? context.colors.accentWork.withAlpha(40)
                              : context.colors.accentCorp.withAlpha(40),
                          child: Text(
                            (member.name.isNotEmpty ? member.name : member.username).substring(0, 1).toUpperCase(),
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.bold,
                              color: isMe ? context.colors.accentWork : context.colors.accentCorp,
                            ),
                          ),
                        ),
                        title: Row(
                          children: [
                            Flexible(
                              child: Text(
                                displayName,
                                style: TextStyle(
                                  fontSize: 14,
                                  fontWeight: isMe ? FontWeight.bold : FontWeight.w500,
                                  color: context.colors.textPrimary,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            if (isMe) ...[
                              const SizedBox(width: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                                decoration: BoxDecoration(
                                  color: Colors.blueAccent.withAlpha(30),
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: const Text(
                                  '나',
                                  style: TextStyle(fontSize: 10, color: Colors.blueAccent, fontWeight: FontWeight.bold),
                                ),
                              ),
                            ],
                          ],
                        ),
                        subtitle: member.email != null && member.email!.isNotEmpty
                            ? Text(
                                member.email!,
                                style: TextStyle(fontSize: 11.5, color: context.colors.textMuted),
                              )
                            : null,
                        trailing: (!isMe)
                            ? IconButton(
                                icon: const Icon(Icons.chat_outlined, size: 18),
                                color: context.colors.accentWork,
                                tooltip: '1:1 대화하기',
                                onPressed: () async {
                                  Navigator.pop(ctx);
                                  try {
                                    final newRoom = await ref.read(chatRepositoryProvider).getOrCreateDm(member.pk);
                                    ref.invalidate(chatRoomsProvider);
                                    if (!mounted) return;
                                    context.push('/chat/${newRoom.id}', extra: newRoom);
                                  } catch (e) {
                                    if (!mounted) return;
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(content: Text('대화방 생성 실패: $e')),
                                    );
                                  }
                                },
                              )
                            : null,
                      );
                    },
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildReplyTargetBar(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      color: context.isDarkMode ? const Color(0xFF1E2230) : const Color(0xFFF1F5F9),
      child: Row(
        children: [
          const Icon(Icons.reply_rounded, size: 16, color: Colors.blueAccent),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '${_replyTarget!.sender?.username ?? "상대방"}님에게 답장',
                  style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.blueAccent),
                ),
                Text(
                  _replyTarget!.content.isNotEmpty ? _replyTarget!.content : (_replyTarget!.fileName.isNotEmpty ? _replyTarget!.fileName : '첨부 내용'),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 11, color: context.colors.textMuted),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close_rounded, size: 18),
            onPressed: () => setState(() => _replyTarget = null),
            visualDensity: VisualDensity.compact,
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
          ),
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
                child: GestureDetector(
                  // 🎯 카카오톡 스타일 더블탭 시 답장 모드 진입
                  onDoubleTap: () => setState(() => _replyTarget = msg),
                  // 🎯 롱프레스 시 복사 / 전달 / 답장 바텀시트
                  onLongPress: () => _showMessageActionMenu(msg),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: isMe
                          ? (context.isDarkMode
                              ? const Color(0xFF2B3A55) // 다크: 슬레이트 네이비
                              : const Color(0xFFE2EEFC)) // 라이트: 소프트 파스텔 연청색
                          : context.colors.bgCard,
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(14),
                        topRight: const Radius.circular(14),
                        bottomLeft: Radius.circular(isMe ? 14 : 2),
                        bottomRight: Radius.circular(isMe ? 2 : 14),
                      ),
                      border: isMe
                          ? (context.isDarkMode
                              ? Border.all(color: const Color(0xFF3D4F72), width: 0.8)
                              : Border.all(color: const Color(0xFFC7DEFA), width: 0.8))
                          : Border.all(color: context.colors.border, width: 0.8),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withAlpha(isMe ? 6 : 8),
                          blurRadius: 3,
                          offset: const Offset(0, 1),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // ↩️ 답장 원본 인용 프리뷰 박스
                        if (msg.replyToDetail != null) ...[
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            margin: const EdgeInsets.only(bottom: 6),
                            decoration: BoxDecoration(
                              color: isMe
                                  ? (context.isDarkMode ? Colors.black26 : Colors.white.withAlpha(180))
                                  : (context.isDarkMode ? Colors.white10 : Colors.black.withAlpha(12)),
                              borderRadius: BorderRadius.circular(4),
                              border: Border(
                                left: BorderSide(color: isMe ? Colors.blueAccent : context.colors.accentWork, width: 3),
                              ),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  msg.replyToDetail!.senderName,
                                  style: TextStyle(
                                    fontSize: 10.5,
                                    fontWeight: FontWeight.bold,
                                    color: isMe ? (context.isDarkMode ? Colors.lightBlueAccent : const Color(0xFF1D4ED8)) : context.colors.accentWork,
                                  ),
                                ),
                                Text(
                                  msg.replyToDetail!.content,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    fontSize: 10.5,
                                    color: context.isDarkMode ? Colors.white70 : Colors.black87,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                        _buildMessageContent(context, msg, isMe),
                      ],
                    ),
                  ),
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
    final myTextColor = context.isDarkMode ? Colors.white : const Color(0xFF0F2E5C);
    final mySubTextColor = context.isDarkMode ? Colors.white.withAlpha(200) : const Color(0xFF3B629B);

    // 📷 이미지 메시지 렌더링
    if (msg.messageType == ChatMessageType.image && msg.file != null) {
      final imgUrl = msg.file!.startsWith('http') ? msg.file! : '$appBaseUrl${msg.file}';
      return ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: CachedNetworkImage(
          imageUrl: imgUrl,
          width: 200,
          fit: BoxFit.cover,
          placeholder: (_, __) => Container(
            height: 140,
            width: 200,
            color: Colors.black12,
            child: const Center(child: CircularProgressIndicator(strokeWidth: 2)),
          ),
          errorWidget: (_, __, ___) => const Icon(Icons.broken_image_rounded, size: 48),
        ),
      );
    }

    // 📎 일반 파일 / 도면 첨부 렌더링
    if (msg.messageType == ChatMessageType.file) {
      final fileUrl = msg.file != null ? (msg.file!.startsWith('http') ? msg.file! : '$appBaseUrl${msg.file}') : '';
      return InkWell(
        onTap: () {
          if (fileUrl.isNotEmpty) launchUrl(Uri.parse(fileUrl), mode: LaunchMode.externalApplication);
        },
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.insert_drive_file_rounded, size: 24, color: isMe ? myTextColor : context.colors.accentWork),
            const SizedBox(width: 8),
            Flexible(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    msg.fileName.isNotEmpty ? msg.fileName : '첨부파일',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12.5, color: isMe ? myTextColor : context.colors.textPrimary),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  if (msg.fileSize > 0)
                    Text(
                      '${(msg.fileSize / 1024).toStringAsFixed(1)} KB',
                      style: TextStyle(fontSize: 10, color: isMe ? mySubTextColor : context.colors.textMuted),
                    ),
                ],
              ),
            ),
          ],
        ),
      );
    }

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
                color: isMe ? myTextColor : context.colors.accentWork,
              ),
              const SizedBox(width: 6),
              Text(
                msg.refTitle.isNotEmpty ? msg.refTitle : msg.content,
                style: TextStyle(
                  color: isMe ? myTextColor : context.colors.textPrimary,
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
                color: isMe ? mySubTextColor : context.colors.textMuted,
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
        color: isMe
            ? myTextColor
            : (context.isDarkMode ? Colors.white : const Color(0xFF1E293B)),
        fontSize: 14,
        height: 1.35,
      ),
    );
  }

  Widget _buildInputBar(BuildContext context) {
    return Container(
      color: context.colors.bgSurface,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
      child: SafeArea(
        top: false,
        child: Row(
          children: [
            IconButton(
              icon: Icon(Icons.add_circle_outline_rounded, color: context.colors.accentWork, size: 26),
              onPressed: _showAttachmentSheet,
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
                    hintText: _replyTarget != null ? '답장 입력 중...' : '메시지를 입력하세요...',
                    hintStyle: TextStyle(color: context.colors.textMuted, fontSize: 13),
                    border: InputBorder.none,
                    isDense: true,
                    contentPadding: const EdgeInsets.symmetric(vertical: 10),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 6),
            IconButton(
              icon: Icon(Icons.send_rounded, color: context.colors.accentWork, size: 24),
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
