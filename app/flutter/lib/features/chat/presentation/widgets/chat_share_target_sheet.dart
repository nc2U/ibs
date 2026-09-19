import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/models/user_model.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/providers/share_payload_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/error_view.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../../../../core/widgets/user_avatar.dart';
import '../../data/chat_repository.dart';
import '../../data/models/chat_model.dart';
import '../../providers/chat_provider.dart';

/// 외부 앱에서 공유된 파일/링크를 메신저 대화방 또는 특정 임직원에게 전송하는 바텀시트
class ChatShareTargetSheet extends ConsumerStatefulWidget {
  final SharePayload payload;

  const ChatShareTargetSheet({
    super.key,
    required this.payload,
  });

  static Future<void> show(BuildContext context, SharePayload payload) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useRootNavigator: true,
      backgroundColor: Colors.transparent,
      builder: (_) => ChatShareTargetSheet(payload: payload),
    );
  }

  @override
  ConsumerState<ChatShareTargetSheet> createState() => _ChatShareTargetSheetState();
}

class _ChatShareTargetSheetState extends ConsumerState<ChatShareTargetSheet>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';
  bool _isSending = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  String _formatFileSize(int bytes) {
    if (bytes <= 0) return '';
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  IconData _getFileIcon(String fileName) {
    final ext = fileName.split('.').last.toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'heic'].contains(ext)) {
      return Icons.image_rounded;
    }
    if (ext == 'pdf') return Icons.picture_as_pdf_rounded;
    if (['zip', 'rar', '7z', 'tar', 'gz'].contains(ext)) {
      return Icons.folder_zip_rounded;
    }
    if (['xls', 'xlsx', 'csv'].contains(ext)) return Icons.table_chart_rounded;
    if (['doc', 'docx', 'hwp', 'hwpx'].contains(ext)) return Icons.description_rounded;
    if (['ppt', 'pptx'].contains(ext)) return Icons.slideshow_rounded;
    if (['mp4', 'mov', 'avi', 'mkv'].contains(ext)) return Icons.movie_rounded;
    if (['mp3', 'wav', 'm4a'].contains(ext)) return Icons.audiotrack_rounded;
    return Icons.insert_drive_file_rounded;
  }

  /// 대상 선택 후 코멘트 입력 및 전송 확인 모달
  Future<void> _handleTargetSelected({
    ChatRoomModel? room,
    UserModel? user,
    bool isSelf = false,
  }) async {
    final currentUser = ref.read(currentUserProvider).valueOrNull;
    final currentUserId = currentUser?.pk ?? 0;

    String targetTitle = '';
    Widget targetAvatar;

    if (isSelf) {
      targetTitle = '나와의 채팅 (나만의 보관함)';
      targetAvatar = CircleAvatar(
        radius: 18,
        backgroundColor: context.colors.accentWork.withAlpha(40),
        child: Icon(Icons.bookmark_rounded, color: context.colors.accentWork, size: 20),
      );
    } else if (room != null) {
      targetTitle = room.getDisplayName(currentUserId);
      targetAvatar = room.roomType == ChatRoomType.channel
          ? CircleAvatar(
              radius: 18,
              backgroundColor: context.colors.accentProject.withAlpha(40),
              child: Icon(Icons.tag_rounded, color: context.colors.accentProject, size: 20),
            )
          : CircleAvatar(
              radius: 18,
              backgroundColor: context.colors.accentWork.withAlpha(40),
              child: Icon(Icons.forum_rounded, color: context.colors.accentWork, size: 20),
            );
    } else if (user != null) {
      targetTitle = user.displayName;
      targetAvatar = UserAvatar(user: user, radius: 18);
    } else {
      return;
    }

    final commentController = TextEditingController();

    final bool? confirmed = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (sheetCtx) {
        return StatefulBuilder(
          builder: (ctx, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                bottom: MediaQuery.of(ctx).viewInsets.bottom,
              ),
              child: Container(
                decoration: BoxDecoration(
                  color: context.colors.bgSurface,
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
                ),
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Center(
                      child: Container(
                        width: 36,
                        height: 4,
                        decoration: BoxDecoration(
                          color: context.colors.border,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        targetAvatar,
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '전송 대상',
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.textMuted,
                                ),
                              ),
                              Text(
                                targetTitle,
                                style: AppTextStyles.titleSm.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: context.colors.textPrimary,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: context.colors.bgPrimary,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: context.colors.border, width: 0.8),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.attachment_rounded, size: 16, color: context.colors.accentWork),
                              const SizedBox(width: 6),
                              Text(
                                '공유 항목 (${widget.payload.files.length}개 파일, ${widget.payload.links.length}개 링크)',
                                style: AppTextStyles.caption.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: context.colors.textPrimary,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          if (widget.payload.files.isNotEmpty)
                            ...widget.payload.files.take(3).map((f) => Padding(
                                  padding: const EdgeInsets.only(bottom: 4),
                                  child: Row(
                                    children: [
                                      Icon(_getFileIcon(f.name), size: 15, color: context.colors.textMuted),
                                      const SizedBox(width: 6),
                                      Expanded(
                                        child: Text(
                                          f.name,
                                          style: AppTextStyles.bodySm.copyWith(
                                            color: context.colors.textPrimary,
                                          ),
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ),
                                      if (f.size > 0)
                                        Text(
                                          _formatFileSize(f.size),
                                          style: AppTextStyles.caption.copyWith(
                                            color: context.colors.textMuted,
                                          ),
                                        ),
                                    ],
                                  ),
                                )),
                          if (widget.payload.files.length > 3)
                            Text(
                              '... 외 ${widget.payload.files.length - 3}개 파일',
                              style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                            ),
                          if (widget.payload.links.isNotEmpty)
                            ...widget.payload.links.take(2).map((link) => Padding(
                                  padding: const EdgeInsets.only(bottom: 4),
                                  child: Row(
                                    children: [
                                      Icon(Icons.link_rounded, size: 15, color: context.colors.accentWork),
                                      const SizedBox(width: 6),
                                      Expanded(
                                        child: Text(
                                          link,
                                          style: AppTextStyles.caption.copyWith(
                                            color: context.colors.accentWork,
                                          ),
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ),
                                    ],
                                  ),
                                )),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: commentController,
                      maxLines: 2,
                      style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
                      decoration: InputDecoration(
                        hintText: '메시지를 함께 입력하세요 (선택 사항)',
                        hintStyle: AppTextStyles.bodySm.copyWith(color: context.colors.textMuted),
                        filled: true,
                        fillColor: context.colors.bgPrimary,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide(color: context.colors.border, width: 0.8),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide(color: context.colors.border, width: 0.8),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide(color: context.colors.accentWork, width: 1.5),
                        ),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      ),
                    ),
                    const SizedBox(height: 20),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () => Navigator.pop(sheetCtx, false),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: context.colors.textMuted,
                              side: BorderSide(color: context.colors.border),
                              padding: const EdgeInsets.symmetric(vertical: 13),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                            ),
                            child: const Text('취소'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          flex: 2,
                          child: ElevatedButton(
                            onPressed: () => Navigator.pop(sheetCtx, true),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: context.colors.accentWork,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 13),
                              elevation: 0,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                            ),
                            child: const Text(
                              '전송하기',
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );

    if (confirmed != true || !mounted) {
      commentController.dispose();
      return;
    }

    final comment = commentController.text.trim();
    commentController.dispose();

    await _executeSend(
      room: room,
      user: user,
      isSelf: isSelf,
      comment: comment,
    );
  }

  /// 실제 파일/메시지 전송 실행
  Future<void> _executeSend({
    ChatRoomModel? room,
    UserModel? user,
    required bool isSelf,
    required String comment,
  }) async {
    setState(() => _isSending = true);

    try {
      final repo = ref.read(chatRepositoryProvider);
      ChatRoomModel targetRoom;

      // 1. 방 획득/생성
      if (isSelf) {
        targetRoom = await repo.getOrCreateSelf();
      } else if (room != null) {
        targetRoom = room;
      } else if (user != null) {
        targetRoom = await repo.getOrCreateDm(user.pk);
      } else {
        throw Exception('전송 대상이 지정되지 않았습니다.');
      }

      // 2. 파일 전송
      if (widget.payload.files.isNotEmpty) {
        for (int i = 0; i < widget.payload.files.length; i++) {
          final pFile = widget.payload.files[i];
          if (pFile.path == null) continue;
          final file = File(pFile.path!);
          if (!file.existsSync()) continue;

          final ext = pFile.name.split('.').last.toLowerCase();
          final isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'heic'].contains(ext);

          // 첫 파일에 코멘트 실어서 전송
          final content = (i == 0 && comment.isNotEmpty) ? comment : null;

          await repo.sendFileMessage(
            roomId: targetRoom.id,
            file: file,
            messageType: isImage ? 'image' : 'file',
            content: content,
          );
        }
      }

      // 3. 링크 전송
      if (widget.payload.links.isNotEmpty) {
        for (final link in widget.payload.links) {
          final msgContent = (widget.payload.files.isEmpty && comment.isNotEmpty)
              ? '$link\n$comment'
              : link;
          await repo.sendTextMessage(
            roomId: targetRoom.id,
            content: msgContent,
          );
        }
      }

      // 파일과 링크가 모두 없고 코멘트만 있던 경우 대비
      if (widget.payload.files.isEmpty && widget.payload.links.isEmpty && comment.isNotEmpty) {
        await repo.sendTextMessage(
          roomId: targetRoom.id,
          content: comment,
        );
      }

      // 4. 완료 처리
      ref.read(pendingSharePayloadProvider.notifier).clear();
      ref.invalidate(chatRoomsProvider);
      ref.invalidate(totalUnreadChatCountProvider);

      if (mounted) {
        Navigator.pop(context); // ChatShareTargetSheet 닫기
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('메신저로 공유되었습니다.'),
            duration: Duration(seconds: 2),
          ),
        );
        context.push('/chat/${targetRoom.id}', extra: targetRoom);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('전송 실패: $e'),
            backgroundColor: context.colors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final currentUser = ref.watch(currentUserProvider).valueOrNull;
    final currentUserId = currentUser?.pk ?? 0;

    return PopScope(
      onPopInvokedWithResult: (didPop, result) {
        if (didPop) {
          ref.read(pendingSharePayloadProvider.notifier).clear();
        }
      },
      child: Container(
        height: MediaQuery.of(context).size.height * 0.88,
        decoration: BoxDecoration(
          color: context.colors.bgPrimary,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: Stack(
          children: [
            Column(
              children: [
                // ── 상단 드래그 핸들 & 헤더 ────────────────────────────
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 8, 4),
                  child: Row(
                    children: [
                      Icon(Icons.send_rounded, color: context.colors.accentWork, size: 20),
                      const SizedBox(width: 8),
                      Text(
                        '메신저로 공유',
                        style: AppTextStyles.titleMd.copyWith(
                          fontWeight: FontWeight.bold,
                          color: context.colors.textPrimary,
                        ),
                      ),
                      const Spacer(),
                      IconButton(
                        icon: Icon(Icons.close_rounded, color: context.colors.textMuted),
                        onPressed: () {
                          ref.read(pendingSharePayloadProvider.notifier).clear();
                          Navigator.pop(context);
                        },
                      ),
                    ],
                  ),
                ),

                // ── 공유 항목 요약 바 ─────────────────────────────────
                Container(
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: context.colors.bgSurface,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: context.colors.border, width: 0.8),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.attachment_rounded, size: 16, color: context.colors.accentWork),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          widget.payload.files.isNotEmpty
                              ? '${widget.payload.files.first.name} 외 ${widget.payload.files.length - 1}개 파일'
                              : (widget.payload.links.isNotEmpty
                                  ? widget.payload.links.first
                                  : '공유 항목'),
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textPrimary,
                            fontWeight: FontWeight.w600,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: context.colors.accentWork.withAlpha(25),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          widget.payload.files.isNotEmpty
                              ? '${widget.payload.files.length}개'
                              : '링크',
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.accentWork,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                // ── 검색 필드 ──────────────────────────────────────────
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
                  child: TextField(
                    controller: _searchController,
                    onChanged: (val) => setState(() => _searchQuery = val.trim().toLowerCase()),
                    style: AppTextStyles.bodySm.copyWith(color: context.colors.textPrimary),
                    decoration: InputDecoration(
                      hintText: '대화방 이름 또는 임직원 검색',
                      hintStyle: AppTextStyles.bodySm.copyWith(color: context.colors.textMuted),
                      prefixIcon: Icon(Icons.search_rounded, color: context.colors.textMuted, size: 20),
                      suffixIcon: _searchQuery.isNotEmpty
                          ? IconButton(
                              icon: Icon(Icons.clear_rounded, color: context.colors.textMuted, size: 18),
                              onPressed: () {
                                _searchController.clear();
                                setState(() => _searchQuery = '');
                              },
                            )
                          : null,
                      filled: true,
                      fillColor: context.colors.bgSurface,
                      isDense: true,
                      contentPadding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: BorderSide(color: context.colors.border, width: 0.8),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: BorderSide(color: context.colors.border, width: 0.8),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: BorderSide(color: context.colors.accentWork, width: 1.5),
                      ),
                    ),
                  ),
                ),

                // ── 나와의 채팅 고정 카드 (카카오톡 최상단 고정 스타일) ────
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  child: Material(
                    color: context.colors.bgSurface,
                    borderRadius: BorderRadius.circular(12),
                    elevation: 0,
                    child: InkWell(
                      borderRadius: BorderRadius.circular(12),
                      onTap: () => _handleTargetSelected(isSelf: true),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color: context.colors.accentWork.withAlpha(50),
                            width: 1,
                          ),
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 40,
                              height: 40,
                              decoration: BoxDecoration(
                                color: context.colors.accentWork.withAlpha(30),
                                shape: BoxShape.circle,
                              ),
                              child: Icon(
                                Icons.bookmark_rounded,
                                color: context.colors.accentWork,
                                size: 22,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Text(
                                        '나와의 채팅',
                                        style: AppTextStyles.titleSm.copyWith(
                                          fontWeight: FontWeight.bold,
                                          color: context.colors.textPrimary,
                                        ),
                                      ),
                                      const SizedBox(width: 6),
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                        decoration: BoxDecoration(
                                          color: context.colors.accentWork.withAlpha(25),
                                          borderRadius: BorderRadius.circular(4),
                                        ),
                                        child: Text(
                                          '개인 보관함',
                                          style: AppTextStyles.caption.copyWith(
                                            color: context.colors.accentWork,
                                            fontSize: 10,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    '나만의 메모, 도면 및 파일 보관함으로 즉시 전송',
                                    style: AppTextStyles.caption.copyWith(
                                      color: context.colors.textMuted,
                                    ),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ],
                              ),
                            ),
                            Icon(
                              Icons.arrow_forward_ios_rounded,
                              color: context.colors.textMuted,
                              size: 14,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),

                // ── 탭바 ──────────────────────────────────────────────
                Container(
                  margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                  decoration: BoxDecoration(
                    border: Border(bottom: BorderSide(color: context.colors.border, width: 0.8)),
                  ),
                  child: TabBar(
                    controller: _tabController,
                    indicatorColor: context.colors.accentWork,
                    indicatorWeight: 2.5,
                    labelColor: context.colors.accentWork,
                    unselectedLabelColor: context.colors.textMuted,
                    labelStyle: AppTextStyles.titleSm.copyWith(fontWeight: FontWeight.bold),
                    tabs: const [
                      Tab(text: '💬 대화방 목록'),
                      Tab(text: '👥 사내 임직원'),
                    ],
                  ),
                ),

                // ── 탭 뷰 ─────────────────────────────────────────────
                Expanded(
                  child: TabBarView(
                    controller: _tabController,
                    children: [
                      // 탭 1: 대화방 목록
                      _buildChatRoomsTab(currentUserId),
                      // 탭 2: 임직원 목록
                      _buildMembersTab(currentUserId),
                    ],
                  ),
                ),
              ],
            ),

            // 전송 중 로딩 오버레이
            if (_isSending)
              Container(
                color: Colors.black.withAlpha(100),
                child: Center(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                    decoration: BoxDecoration(
                      color: context.colors.bgSurface,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2.5,
                            color: context.colors.accentWork,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Text(
                          '파일 전송 중...',
                          style: AppTextStyles.bodyMd.copyWith(
                            fontWeight: FontWeight.bold,
                            color: context.colors.textPrimary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  /// 탭 1: 대화방 목록 빌더
  Widget _buildChatRoomsTab(int currentUserId) {
    final roomsAsync = ref.watch(chatRoomsProvider);

    return roomsAsync.when(
      loading: () => const LoadingShimmer(itemCount: 6, itemHeight: 56),
      error: (e, _) => ErrorView(
        message: '대화방 목록을 불러오지 못했습니다: $e',
        onRetry: () => ref.invalidate(chatRoomsProvider),
      ),
      data: (rooms) {
        // 나와의 채팅은 상단에 고정되어 있으므로 목록에서는 제외하고 필터링
        var filtered = rooms.where((r) => r.roomType != ChatRoomType.self).toList();

        if (_searchQuery.isNotEmpty) {
          filtered = filtered.where((r) {
            final name = r.getDisplayName(currentUserId).toLowerCase();
            final project = (r.projectName ?? '').toLowerCase();
            return name.contains(_searchQuery) || project.contains(_searchQuery);
          }).toList();
        }

        if (filtered.isEmpty) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Text(
                _searchQuery.isNotEmpty ? '검색된 대화방이 없습니다.' : '참여 중인 대화방이 없습니다.',
                style: AppTextStyles.bodySm.copyWith(color: context.colors.textMuted),
              ),
            ),
          );
        }

        return ListView.separated(
          padding: const EdgeInsets.symmetric(vertical: 8),
          itemCount: filtered.length,
          separatorBuilder: (_, __) => Divider(
            height: 1,
            indent: 68,
            color: context.colors.border.withAlpha(60),
          ),
          itemBuilder: (context, idx) {
            final room = filtered[idx];
            final displayName = room.getDisplayName(currentUserId);
            final isChannel = room.roomType == ChatRoomType.channel;

            return ListTile(
              leading: isChannel
                  ? CircleAvatar(
                      radius: 20,
                      backgroundColor: context.colors.accentProject.withAlpha(35),
                      child: Icon(Icons.tag_rounded, color: context.colors.accentProject, size: 20),
                    )
                  : CircleAvatar(
                      radius: 20,
                      backgroundColor: context.colors.accentWork.withAlpha(35),
                      child: Icon(Icons.person_rounded, color: context.colors.accentWork, size: 20),
                    ),
              title: Row(
                children: [
                  Expanded(
                    child: Text(
                      displayName,
                      style: AppTextStyles.bodyMd.copyWith(
                        fontWeight: FontWeight.w600,
                        color: context.colors.textPrimary,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  if (room.memberCount > 2)
                    Padding(
                      padding: const EdgeInsets.only(left: 4),
                      child: Text(
                        '${room.memberCount}',
                        style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                      ),
                    ),
                ],
              ),
              subtitle: Text(
                room.lastMessage?.content ?? (isChannel ? '워크스페이스 공용 채널' : '대화 기록 없음'),
                style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              onTap: () => _handleTargetSelected(room: room),
            );
          },
        );
      },
    );
  }

  /// 탭 2: 사내 임직원 목록 빌더
  Widget _buildMembersTab(int currentUserId) {
    final membersAsync = ref.watch(allMembersProvider);

    return membersAsync.when(
      loading: () => const LoadingShimmer(itemCount: 6, itemHeight: 56),
      error: (e, _) => ErrorView(
        message: '임직원 목록을 불러오지 못했습니다: $e',
        onRetry: () => ref.invalidate(allMembersProvider),
      ),
      data: (members) {
        // 본인 제외 및 검색 필터링
        var filtered = members.where((m) => m.pk != currentUserId).toList();

        if (_searchQuery.isNotEmpty) {
          filtered = filtered.where((m) {
            final name = (m.profile?.name ?? '').toLowerCase();
            final username = m.username.toLowerCase();
            return name.contains(_searchQuery) || username.contains(_searchQuery);
          }).toList();
        }

        if (filtered.isEmpty) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Text(
                _searchQuery.isNotEmpty ? '검색된 임직원이 없습니다.' : '임직원 목록이 없습니다.',
                style: AppTextStyles.bodySm.copyWith(color: context.colors.textMuted),
              ),
            ),
          );
        }

        return ListView.separated(
          padding: const EdgeInsets.symmetric(vertical: 8),
          itemCount: filtered.length,
          separatorBuilder: (_, __) => Divider(
            height: 1,
            indent: 68,
            color: context.colors.border.withAlpha(60),
          ),
          itemBuilder: (context, idx) {
            final member = filtered[idx];

            return ListTile(
              leading: UserAvatar(
                user: member,
                radius: 20,
              ),
              title: Text(
                member.displayName,
                style: AppTextStyles.bodyMd.copyWith(
                  fontWeight: FontWeight.w600,
                  color: context.colors.textPrimary,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              subtitle: Text(
                member.email ?? member.username,
                style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              trailing: Icon(
                Icons.chat_bubble_outline_rounded,
                color: context.colors.accentWork,
                size: 18,
              ),
              onTap: () => _handleTargetSelected(user: member),
            );
          },
        );
      },
    );
  }
}
