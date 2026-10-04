import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/error_view.dart';
import '../../data/chat_repository.dart';
import '../../data/models/chat_model.dart';

/// 📂 대화방 영구 보존 파일/미디어/링크 모아보기 서랍 바텀시트
class ChatFilesSheet extends ConsumerStatefulWidget {
  final int roomId;
  final String roomTitle;
  final void Function(int messageId)? onJumpToMessage;

  const ChatFilesSheet({
    super.key,
    required this.roomId,
    required this.roomTitle,
    this.onJumpToMessage,
  });

  static Future<void> show(
    BuildContext context, {
    required int roomId,
    required String roomTitle,
    void Function(int messageId)? onJumpToMessage,
  }) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => ChatFilesSheet(
        roomId: roomId,
        roomTitle: roomTitle,
        onJumpToMessage: onJumpToMessage,
      ),
    );
  }

  @override
  ConsumerState<ChatFilesSheet> createState() => _ChatFilesSheetState();
}

class _ChatFilesSheetState extends ConsumerState<ChatFilesSheet>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  // 0: 사진/동영상(media), 1: 문서/파일(doc), 2: 공유 링크(link)
  final _tabs = ['media', 'doc', 'link'];

  final Map<String, List<ChatMessageModel>> _items = {
    'media': [],
    'doc': [],
    'link': [],
  };
  final Map<String, bool> _isLoading = {
    'media': false,
    'doc': false,
    'link': false,
  };
  final Map<String, String?> _errors = {
    'media': null,
    'doc': null,
    'link': null,
  };

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadTabItems('media');
    _tabController.addListener(() {
      if (_tabController.indexIsChanging) {
        final currentTab = _tabs[_tabController.index];
        if (_items[currentTab]!.isEmpty && !_isLoading[currentTab]!) {
          _loadTabItems(currentTab);
        }
      }
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadTabItems(String tab) async {
    setState(() {
      _isLoading[tab] = true;
      _errors[tab] = null;
    });

    try {
      final repo = ref.read(chatRepositoryProvider);
      final res = await repo.fetchChatFiles(
        roomId: widget.roomId,
        tab: tab,
        page: 1,
        pageSize: 50,
      );
      if (mounted) {
        setState(() {
          _items[tab] = res['results'] as List<ChatMessageModel>;
          _isLoading[tab] = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errors[tab] = '목록을 불러오지 못했습니다: $e';
          _isLoading[tab] = false;
        });
      }
    }
  }

  String _formatFileSize(int bytes) {
    if (bytes <= 0) return '';
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  IconData _getFileIcon(String fileName) {
    final ext = fileName.split('.').last.toLowerCase();
    switch (ext) {
      case 'pdf':
        return Icons.picture_as_pdf_rounded;
      case 'xls':
      case 'xlsx':
      case 'csv':
        return Icons.table_chart_rounded;
      case 'doc':
      case 'docx':
      case 'hwp':
      case 'hwpx':
        return Icons.description_rounded;
      case 'ppt':
      case 'pptx':
        return Icons.slideshow_rounded;
      case 'zip':
      case 'rar':
      case '7z':
        return Icons.folder_zip_rounded;
      case 'dwg':
      case 'dxf':
        return Icons.architecture_rounded;
      default:
        return Icons.insert_drive_file_rounded;
    }
  }

  Color _getFileColor(String fileName) {
    final ext = fileName.split('.').last.toLowerCase();
    switch (ext) {
      case 'pdf':
        return Colors.redAccent;
      case 'xls':
      case 'xlsx':
      case 'csv':
        return Colors.green;
      case 'doc':
      case 'docx':
      case 'hwp':
      case 'hwpx':
        return Colors.blue;
      case 'ppt':
      case 'pptx':
        return Colors.orange;
      case 'dwg':
      case 'dxf':
        return Colors.teal;
      default:
        return Colors.blueGrey;
    }
  }

  @override
  Widget build(BuildContext context) {
    final dateFormat = DateFormat('yyyy.MM.dd HH:mm');

    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
        border: Border(top: BorderSide(color: context.colors.border, width: 0.8)),
      ),
      child: SafeArea(
        child: Column(
          children: [
            // ── 상단 헤더 ──────────────────────────────────────────
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: context.colors.bgSurface,
              child: Row(
                children: [
                  Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      color: context.colors.accentWork.withAlpha(25),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Icon(Icons.folder_shared_outlined, size: 18, color: context.colors.accentWork),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '대화방 보관함 (영구 보존)',
                          style: AppTextStyles.titleSm.copyWith(
                            fontWeight: FontWeight.bold,
                            color: context.colors.textPrimary,
                          ),
                        ),
                        Text(
                          widget.roomTitle,
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, size: 20),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),
            Divider(color: context.colors.border, height: 1),

            // ── 탭 바 ──────────────────────────────────────────────
            Container(
              color: context.colors.bgSurface,
              child: TabBar(
                controller: _tabController,
                indicatorColor: context.colors.accentWork,
                indicatorWeight: 2.5,
                labelColor: context.colors.accentWork,
                unselectedLabelColor: context.colors.textMuted,
                labelStyle: AppTextStyles.titleSm.copyWith(fontWeight: FontWeight.bold, fontSize: 13),
                tabs: const [
                  Tab(text: '🖼️ 사진/미디어'),
                  Tab(text: '📑 문서/파일'),
                  Tab(text: '🔗 공유 링크'),
                ],
              ),
            ),
            Divider(color: context.colors.border, height: 1),

            // ── 탭 내용 ────────────────────────────────────────────
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  // 1. 미디어 탭
                  _buildMediaGrid(dateFormat),

                  // 2. 파일 탭
                  _buildFileList(dateFormat),

                  // 3. 링크 탭
                  _buildLinkList(dateFormat),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMediaGrid(DateFormat dateFormat) {
    if (_isLoading['media'] == true) {
      return const Center(child: CircularProgressIndicator(strokeWidth: 2));
    }
    if (_errors['media'] != null) {
      return ErrorView(
        message: _errors['media']!,
        onRetry: () => _loadTabItems('media'),
      );
    }
    final list = _items['media'] ?? [];
    if (list.isEmpty) {
      return _buildEmptyState('공유된 사진이나 이미지가 없습니다.');
    }

    return GridView.builder(
      padding: const EdgeInsets.all(12),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        crossAxisSpacing: 8,
        mainAxisSpacing: 8,
      ),
      itemCount: list.length,
      itemBuilder: (context, index) {
        final msg = list[index];
        final url = msg.fileUrl;

        return InkWell(
          borderRadius: BorderRadius.circular(6),
          onTap: () {
            if (widget.onJumpToMessage != null) {
              Navigator.pop(context);
              widget.onJumpToMessage!(msg.id);
            }
          },
          child: Container(
            clipBehavior: Clip.antiAlias,
            decoration: BoxDecoration(
              color: context.colors.bgSurface,
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: context.colors.border, width: 0.8),
            ),
            child: url.isNotEmpty
                ? Image.network(
                    url,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => const Icon(Icons.broken_image_rounded, size: 28),
                  )
                : const Icon(Icons.image_rounded, size: 28),
          ),
        );
      },
    );
  }

  Widget _buildFileList(DateFormat dateFormat) {
    if (_isLoading['doc'] == true) {
      return const Center(child: CircularProgressIndicator(strokeWidth: 2));
    }
    if (_errors['doc'] != null) {
      return ErrorView(
        message: _errors['doc']!,
        onRetry: () => _loadTabItems('doc'),
      );
    }
    final list = _items['doc'] ?? [];
    if (list.isEmpty) {
      return _buildEmptyState('공유된 문서나 첨부파일이 없습니다.');
    }

    return ListView.separated(
      padding: const EdgeInsets.all(12),
      itemCount: list.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (context, index) {
        final msg = list[index];
        final fileName = msg.fileName.isNotEmpty ? msg.fileName : '첨부파일';
        final fileSizeStr = _formatFileSize(msg.fileSize);
        final iconColor = _getFileColor(fileName);
        final fileIcon = _getFileIcon(fileName);

        return Material(
          color: context.colors.bgSurface,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(6),
            side: BorderSide(color: context.colors.border, width: 0.8),
          ),
          child: InkWell(
            borderRadius: BorderRadius.circular(6),
            onTap: () {
              if (widget.onJumpToMessage != null) {
                Navigator.pop(context);
                widget.onJumpToMessage!(msg.id);
              }
            },
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              child: Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: iconColor.withAlpha(25),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Icon(fileIcon, color: iconColor, size: 20),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          fileName,
                          style: AppTextStyles.bodyMd.copyWith(
                            fontWeight: FontWeight.bold,
                            color: context.colors.textPrimary,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '${msg.senderName} · $fileSizeStr · ${dateFormat.format(msg.created)}',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  if (msg.fileUrl.isNotEmpty)
                    IconButton(
                      icon: Icon(Icons.download_rounded, color: context.colors.accentWork, size: 20),
                      tooltip: '다운로드',
                      onPressed: () async {
                        final uri = Uri.tryParse(msg.fileUrl);
                        if (uri != null) {
                          await launchUrl(uri, mode: LaunchMode.externalApplication);
                        }
                      },
                    ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildLinkList(DateFormat dateFormat) {
    if (_isLoading['link'] == true) {
      return const Center(child: CircularProgressIndicator(strokeWidth: 2));
    }
    if (_errors['link'] != null) {
      return ErrorView(
        message: _errors['link']!,
        onRetry: () => _loadTabItems('link'),
      );
    }
    final list = _items['link'] ?? [];
    if (list.isEmpty) {
      return _buildEmptyState('공유된 업무 카드나 링크가 없습니다.');
    }

    return ListView.separated(
      padding: const EdgeInsets.all(12),
      itemCount: list.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (context, index) {
        final msg = list[index];
        final isRichCard = msg.refId != null && msg.refId! > 0;
        final title = isRichCard
            ? '[${msg.messageType.name.toUpperCase()}] ${msg.refTitle}'
            : (msg.content.isNotEmpty ? msg.content : '링크');

        return Material(
          color: context.colors.bgSurface,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(6),
            side: BorderSide(color: context.colors.border, width: 0.8),
          ),
          child: InkWell(
            borderRadius: BorderRadius.circular(6),
            onTap: () {
              if (widget.onJumpToMessage != null) {
                Navigator.pop(context);
                widget.onJumpToMessage!(msg.id);
              }
            },
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              child: Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: (isRichCard ? Colors.teal : Colors.blue).withAlpha(25),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Icon(
                      isRichCard ? Icons.link_rounded : Icons.open_in_new_rounded,
                      color: isRichCard ? Colors.teal : Colors.blue,
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          title,
                          style: AppTextStyles.bodyMd.copyWith(
                            fontWeight: FontWeight.bold,
                            color: context.colors.textPrimary,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '${msg.senderName} · ${dateFormat.format(msg.created)}',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildEmptyState(String message) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.inventory_2_outlined, size: 40, color: context.colors.textMuted),
          const SizedBox(height: 8),
          Text(
            message,
            style: AppTextStyles.bodyMd.copyWith(color: context.colors.textMuted),
          ),
        ],
      ),
    );
  }
}
