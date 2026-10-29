import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/permissions.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../../../core/providers/project_provider.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/models/site_models.dart';
import '../../data/site_repository.dart';
import '../../providers/site_provider.dart';

/// 💬 토지 소유자 상담 및 협의 기록 관리 바텀시트
class SiteOwnerConsultationBottomSheet extends ConsumerStatefulWidget {
  final SiteOwnerItemModel owner;

  const SiteOwnerConsultationBottomSheet({super.key, required this.owner});

  @override
  ConsumerState<SiteOwnerConsultationBottomSheet> createState() => _SiteOwnerConsultationBottomSheetState();
}

class _SiteOwnerConsultationBottomSheetState extends ConsumerState<SiteOwnerConsultationBottomSheet> {
  late Future<List<SiteOwnerConsultationLogModel>> _logsFuture;

  @override
  void initState() {
    super.initState();
    _loadLogs();
  }

  void _loadLogs() {
    _logsFuture = ref.read(siteRepositoryProvider).fetchOwnerConsultationLogs(siteOwnerId: widget.owner.pk);
  }

  void _reloadAndInvalidate() {
    ref.invalidate(siteOwnerListProvider);
    if (mounted) {
      setState(() {
        _loadLogs();
      });
    }
  }

  void _showAddOrEditDialog({SiteOwnerConsultationLogModel? initialLog}) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => _SiteOwnerConsultationDialog(
        ownerId: widget.owner.pk,
        ownerName: widget.owner.owner,
        initialLog: initialLog,
        onSuccess: _reloadAndInvalidate,
      ),
    );
  }

  Future<void> _confirmDeleteLog(SiteOwnerConsultationLogModel logItem) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: context.colors.bgCard,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        title: Text(
          '상담일지 삭제',
          style: AppTextStyles.titleSm.copyWith(
            color: context.colors.textPrimary,
            fontWeight: FontWeight.bold,
          ),
        ),
        content: Text(
          '선택한 상담 기록(${logItem.title.isNotEmpty ? logItem.title : logItem.consultationDate})을 삭제하시겠습니까?',
          style: AppTextStyles.bodySm.copyWith(color: context.colors.textSecond),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFEF4444),
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('삭제', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    final errorMsg = await ref.read(siteRepositoryProvider).deleteOwnerConsultationLog(logId: logItem.pk);
    if (!mounted) return;

    if (errorMsg == null) {
      _reloadAndInvalidate();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('상담일지가 삭제되었습니다.'), behavior: SnackBarBehavior.floating),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('삭제 실패: $errorMsg'),
          backgroundColor: context.colors.error,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final selectedProject = ref.watch(selectedRealEstateProjectProvider);
    final projectSlug = selectedProject?.slug;
    final canCreate = ref.can(Perm.siteCreate, projectSlug: projectSlug);
    final canUpdate = ref.can(Perm.siteUpdate, projectSlug: projectSlug);
    final canDelete = ref.can(Perm.siteDelete, projectSlug: projectSlug);

    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
        border: Border(top: BorderSide(color: context.colors.border, width: 0.8)),
      ),
      child: SafeArea(
        child: Column(
          children: [
            // 상단 헤더
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: context.colors.bgSurface,
              child: Row(
                children: [
                  Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      color: const Color(0xFFF59E0B).withAlpha(20),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: const Icon(Icons.edit_calendar_outlined, size: 18, color: Color(0xFFF59E0B)),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              '소유자 협의 / 상담 기록',
                              style: AppTextStyles.titleSm.copyWith(
                                color: context.colors.textPrimary,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(width: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                              decoration: BoxDecoration(
                                color: const Color(0xFFF59E0B).withAlpha(20),
                                border: Border.all(color: const Color(0xFFF59E0B).withAlpha(100), width: 0.6),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                widget.owner.owner,
                                style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFFF59E0B)),
                              ),
                            ),
                          ],
                        ),
                        Text(
                          '소유 필지: ${widget.owner.displaySiteSummary}',
                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, size: 18),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),
            Divider(color: context.colors.border, height: 1),

            // 신규 등록 액션바
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Row(
                children: [
                  const Text('협의 및 통화 이력', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  const Spacer(),
                  if (canCreate)
                    ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFF59E0B),
                        foregroundColor: Colors.white,
                        elevation: 0,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      ),
                      onPressed: () => _showAddOrEditDialog(),
                      icon: const Icon(Icons.add, size: 15),
                      label: const Text('상담일지 작성', style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.bold)),
                    ),
                ],
              ),
            ),

            // 목록 영역
            Expanded(
              child: FutureBuilder<List<SiteOwnerConsultationLogModel>>(
                future: _logsFuture,
                builder: (ctx, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return const Center(child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFFF59E0B)));
                  }

                  if (snapshot.hasError) {
                    return Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text('상담 기록 로드 실패: ${snapshot.error}', style: TextStyle(color: context.colors.error, fontSize: 12)),
                          const SizedBox(height: 8),
                          TextButton.icon(
                            onPressed: () => setState(_loadLogs),
                            icon: const Icon(Icons.refresh_rounded, size: 16),
                            label: const Text('다시 시도'),
                          ),
                        ],
                      ),
                    );
                  }

                  final logs = snapshot.data ?? [];
                  if (logs.isEmpty) {
                    return Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.speaker_notes_off_outlined, size: 40, color: context.colors.textMuted.withAlpha(120)),
                          const SizedBox(height: 10),
                          Text('등록된 상담 및 협의 기록이 없습니다.', style: AppTextStyles.bodySm.copyWith(color: context.colors.textMuted)),
                          if (canCreate) ...[
                            const SizedBox(height: 8),
                            TextButton.icon(
                              onPressed: () => _showAddOrEditDialog(),
                              icon: const Icon(Icons.add, size: 16, color: Color(0xFFF59E0B)),
                              label: const Text('첫 상담일지 작성하기', style: TextStyle(color: Color(0xFFF59E0B))),
                            ),
                          ],
                        ],
                      ),
                    );
                  }

                  return ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: logs.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (ctx, index) {
                      final item = logs[index];
                      return Container(
                        decoration: BoxDecoration(
                          color: context.colors.bgSurface,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: context.colors.border, width: 0.8),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // 카드 헤더
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                              color: context.colors.bgCard,
                              child: Row(
                                children: [
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFFF59E0B).withAlpha(20),
                                      border: Border.all(color: const Color(0xFFF59E0B).withAlpha(80), width: 0.6),
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                    child: Text(
                                      item.channelKorean,
                                      style: const TextStyle(
                                        fontSize: 10,
                                        fontWeight: FontWeight.bold,
                                        color: Color(0xFFF59E0B),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      item.title.isNotEmpty ? item.title : '상담 협의 기록',
                                      style: AppTextStyles.bodySm.copyWith(
                                        color: context.colors.textPrimary,
                                        fontWeight: FontWeight.bold,
                                      ),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                  Text(
                                    item.consultationDate,
                                    style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 11),
                                  ),
                                  if (canUpdate) ...[
                                    const SizedBox(width: 6),
                                    InkWell(
                                      onTap: () => _showAddOrEditDialog(initialLog: item),
                                      child: Padding(
                                        padding: const EdgeInsets.all(2),
                                        child: Icon(Icons.edit_outlined, size: 15, color: context.colors.textSecond),
                                      ),
                                    ),
                                  ],
                                  if (canDelete) ...[
                                    const SizedBox(width: 6),
                                    InkWell(
                                      onTap: () => _confirmDeleteLog(item),
                                      child: const Padding(
                                        padding: EdgeInsets.all(2),
                                        child: Icon(Icons.delete_outline_rounded, size: 15, color: Color(0xFFEF4444)),
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            ),
                            Divider(color: context.colors.border, height: 1),

                            // 상담 본문
                            Padding(
                              padding: const EdgeInsets.all(12),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    item.content,
                                    style: AppTextStyles.bodySecond.copyWith(
                                      color: context.colors.textPrimary,
                                      height: 1.4,
                                    ),
                                  ),
                                  if (item.followUpRequired) ...[
                                    const SizedBox(height: 8),
                                    Container(
                                      width: double.infinity,
                                      padding: const EdgeInsets.all(8),
                                      color: const Color(0xFFEF4444).withAlpha(15),
                                      child: Row(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          const Icon(Icons.error_outline, size: 14, color: Color(0xFFEF4444)),
                                          const SizedBox(width: 6),
                                          Expanded(
                                            child: Text(
                                              '후속조치: ${item.followUpNote ?? "조치 예정"}',
                                              style: const TextStyle(fontSize: 11, color: Color(0xFFDC2626), fontWeight: FontWeight.w500),
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                  const SizedBox(height: 6),
                                  Row(
                                    children: [
                                      if (item.consultantName != null)
                                        Text(
                                          '담당자: ${item.consultantName}',
                                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 10.5),
                                        ),
                                      const Spacer(),
                                      if (item.created != null)
                                        Text(
                                          '등록: ${item.created!.split("T").first}',
                                          style: AppTextStyles.caption.copyWith(color: context.colors.textMuted, fontSize: 10.5),
                                        ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// ➕ 소유자 상담 기록 등록 / 수정 다이얼로그
class _SiteOwnerConsultationDialog extends ConsumerStatefulWidget {
  final int ownerId;
  final String ownerName;
  final SiteOwnerConsultationLogModel? initialLog;
  final VoidCallback onSuccess;

  const _SiteOwnerConsultationDialog({
    required this.ownerId,
    required this.ownerName,
    this.initialLog,
    required this.onSuccess,
  });

  @override
  ConsumerState<_SiteOwnerConsultationDialog> createState() => _SiteOwnerConsultationDialogState();
}

class _SiteOwnerConsultationDialogState extends ConsumerState<_SiteOwnerConsultationDialog> {
  late final TextEditingController _titleController;
  late final TextEditingController _contentController;
  late final TextEditingController _followUpController;

  late String _channel;
  late String _date;
  late bool _followUpRequired;
  bool _isLoading = false;

  bool get _isEditing => widget.initialLog != null;

  @override
  void initState() {
    super.initState();
    final log = widget.initialLog;
    _titleController = TextEditingController(text: log?.title ?? '');
    _contentController = TextEditingController(text: log?.content ?? '');
    _followUpController = TextEditingController(text: log?.followUpNote ?? '');
    const validChannels = {'phone', 'visit', 'kakao', 'sms', 'email', 'other'};
    _channel = (log != null && validChannels.contains(log.channel)) ? log.channel : 'phone';
    _date = (log != null && log.consultationDate.isNotEmpty)
        ? log.consultationDate
        : DateFormat('yyyy-MM-dd').format(DateTime.now());
    _followUpRequired = log?.followUpRequired ?? false;
  }

  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    _followUpController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_titleController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('상담 제목을 입력하세요.'), behavior: SnackBarBehavior.floating),
      );
      return;
    }
    if (_contentController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('상담 내용을 입력하세요.'), behavior: SnackBarBehavior.floating),
      );
      return;
    }

    setState(() => _isLoading = true);

    final repository = ref.read(siteRepositoryProvider);
    final String? errorMsg;

    if (_isEditing) {
      errorMsg = await repository.updateOwnerConsultationLog(
        logId: widget.initialLog!.pk,
        siteOwnerId: widget.ownerId,
        consultationDate: _date,
        channel: _channel,
        title: _titleController.text.trim(),
        content: _contentController.text.trim(),
        followUpRequired: _followUpRequired,
        followUpNote: _followUpRequired ? _followUpController.text.trim() : '',
      );
    } else {
      errorMsg = await repository.createOwnerConsultationLog(
        siteOwnerId: widget.ownerId,
        consultationDate: _date,
        channel: _channel,
        title: _titleController.text.trim(),
        content: _contentController.text.trim(),
        followUpRequired: _followUpRequired,
        followUpNote: _followUpRequired ? _followUpController.text.trim() : null,
      );
    }

    if (!mounted) return;
    setState(() => _isLoading = false);

    if (errorMsg == null) {
      widget.onSuccess();
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(_isEditing ? '상담일지가 수정되었습니다.' : '상담일지가 등록되었습니다.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('상담일지 ${_isEditing ? "수정" : "등록"} 실패: $errorMsg'),
          backgroundColor: context.colors.error,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      scrollable: true,
      backgroundColor: context.colors.bgCard,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: context.colors.border, width: 0.8),
      ),
      titlePadding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16),
      actionsPadding: const EdgeInsets.all(12),
      title: Row(
        children: [
          const Icon(Icons.edit_note, size: 22, color: Color(0xFFF59E0B)),
          const SizedBox(width: 8),
          Text(
            _isEditing ? '소유자 상담일지 수정' : '소유자 상담일지 작성',
            style: AppTextStyles.titleSm.copyWith(
              color: context.colors.textPrimary,
              fontWeight: FontWeight.bold,
            ),
          ),
          const Spacer(),
          Text(
            widget.ownerName,
            style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
          ),
        ],
      ),
      content: SizedBox(
        width: MediaQuery.of(context).size.width * 0.95,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Divider(color: context.colors.border, height: 1),
            const SizedBox(height: 12),

            // 1. 상담일자 & 상담채널
            Row(
              children: [
                Expanded(
                  child: InkWell(
                    onTap: () async {
                      final initial = DateTime.tryParse(_date) ?? DateTime.now();
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: initial,
                        firstDate: DateTime(2000),
                        lastDate: DateTime(2100),
                      );
                      if (picked != null) {
                        setState(() => _date = DateFormat('yyyy-MM-dd').format(picked));
                      }
                    },
                    child: InputDecorator(
                      decoration: const InputDecoration(
                        labelText: '상담일자',
                        isDense: true,
                        border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(6))),
                      ),
                      child: Text(_date, style: const TextStyle(fontSize: 13)),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _channel,
                    decoration: const InputDecoration(
                      labelText: '상담채널',
                      isDense: true,
                      border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(6))),
                    ),
                    items: const [
                      DropdownMenuItem(value: 'phone', child: Text('전화')),
                      DropdownMenuItem(value: 'visit', child: Text('방문')),
                      DropdownMenuItem(value: 'kakao', child: Text('카카오톡')),
                      DropdownMenuItem(value: 'sms', child: Text('문자')),
                      DropdownMenuItem(value: 'email', child: Text('이메일')),
                      DropdownMenuItem(value: 'other', child: Text('기타')),
                    ],
                    onChanged: (val) => setState(() => _channel = val ?? 'phone'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // 2. 제목
            TextField(
              controller: _titleController,
              style: const TextStyle(fontSize: 13),
              decoration: const InputDecoration(
                labelText: '상담 제목 (요약)',
                hintText: '예: 매매 희망단가 및 양도세 문의 협의',
                isDense: true,
                border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(6))),
              ),
            ),
            const SizedBox(height: 12),

            // 3. 내용
            TextField(
              controller: _contentController,
              maxLines: 4,
              style: const TextStyle(fontSize: 13),
              decoration: const InputDecoration(
                labelText: '상세 상담 및 협의 내용',
                hintText: '소유자와의 통화/면담 세부 협의 내용을 입력하세요.',
                isDense: true,
                border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(6))),
              ),
            ),
            const SizedBox(height: 10),

            // 4. 후속조치 체크
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              dense: true,
              title: const Text('후속 조치 필요', style: TextStyle(fontSize: 12)),
              value: _followUpRequired,
              onChanged: (val) => setState(() => _followUpRequired = val ?? false),
            ),
            if (_followUpRequired)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: TextField(
                  controller: _followUpController,
                  style: const TextStyle(fontSize: 12.5),
                  decoration: const InputDecoration(
                    labelText: '후속조치 메모',
                    hintText: '예: 예상 양도세 산출표 작성 후 다음 주 재통화 예정',
                    isDense: true,
                    border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(6))),
                  ),
                ),
              ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isLoading ? null : () => Navigator.pop(context),
          child: Text('취소', style: TextStyle(color: context.colors.textMuted)),
        ),
        ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFFF59E0B),
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          ),
          onPressed: _isLoading ? null : _submit,
          child: _isLoading
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
              : Text(_isEditing ? '수정 완료' : '등록 완료', style: const TextStyle(fontWeight: FontWeight.bold)),
        ),
      ],
    );
  }
}
