import 'package:flutter/material.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';

enum ApprovalActionModalType {
  approve,
  reject,
  comment,
  submit,
  cancel,
}

class ApprovalActionBottomSheet extends StatefulWidget {
  final ApprovalActionModalType type;
  final String title;
  final Future<void> Function(String? comment) onConfirm;

  const ApprovalActionBottomSheet({
    super.key,
    required this.type,
    required this.title,
    required this.onConfirm,
  });

  static Future<void> show(
    BuildContext context, {
    required ApprovalActionModalType type,
    required String title,
    required Future<void> Function(String? comment) onConfirm,
  }) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => ApprovalActionBottomSheet(
        type: type,
        title: title,
        onConfirm: onConfirm,
      ),
    );
  }

  @override
  State<ApprovalActionBottomSheet> createState() => _ApprovalActionBottomSheetState();
}

class _ApprovalActionBottomSheetState extends State<ApprovalActionBottomSheet> {
  final _commentController = TextEditingController();
  bool _isLoading = false;
  String? _errorText;

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  bool get _isCommentRequired => widget.type == ApprovalActionModalType.reject;

  String get _actionTitle {
    switch (widget.type) {
      case ApprovalActionModalType.approve:
        return '결재 승인';
      case ApprovalActionModalType.reject:
        return '결재 반려';
      case ApprovalActionModalType.comment:
        return '결재 의견 등록';
      case ApprovalActionModalType.submit:
        return '결재 상신';
      case ApprovalActionModalType.cancel:
        return '기안 회수';
    }
  }

  Color _getActionColor(BuildContext context) {
    switch (widget.type) {
      case ApprovalActionModalType.approve:
        return context.colors.success;
      case ApprovalActionModalType.reject:
        return context.colors.error;
      case ApprovalActionModalType.comment:
        return context.colors.info;
      case ApprovalActionModalType.submit:
        return context.colors.accentApproval;
      case ApprovalActionModalType.cancel:
        return Colors.blueGrey;
    }
  }

  Future<void> _handleConfirm() async {
    final comment = _commentController.text.trim();
    if (_isCommentRequired && comment.isEmpty) {
      setState(() {
        _errorText = '반려 사유를 반드시 입력해 주세요.';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _errorText = null;
    });

    try {
      await widget.onConfirm(comment.isNotEmpty ? comment : null);
      if (mounted) {
        Navigator.of(context).pop();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorText = '처리 중 오류가 발생했습니다: $e';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;
    final actionColor = _getActionColor(context);

    return Container(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: 20 + bottomInset,
      ),
      decoration: BoxDecoration(
        color: context.colors.bgPrimary,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // ── 상단 드래그 핸들 ──────────────────────────────────────────
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

          // ── 모달 타이틀 & 문서명 ─────────────────────────────────────
          Row(
            children: [
              Container(
                width: 8,
                height: 20,
                color: actionColor,
              ),
              const SizedBox(width: 8),
              Text(
                _actionTitle,
                style: AppTextStyles.titleMd.copyWith(
                  fontWeight: FontWeight.w800,
                  color: context.colors.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            widget.title,
            style: TextStyle(
              fontSize: 13,
              color: context.colors.textMuted,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 16),

          // ── 의견/사유 입력창 (승인, 반려, 의견 모달인 경우) ──────────────
          if (widget.type != ApprovalActionModalType.submit &&
              widget.type != ApprovalActionModalType.cancel) ...[
            TextField(
              controller: _commentController,
              maxLines: 3,
              style: TextStyle(fontSize: 13.5, color: context.colors.textPrimary),
              decoration: InputDecoration(
                hintText: _isCommentRequired
                    ? '반려 사유를 입력하세요 (필수)'
                    : '결재 의견을 입력하세요 (선택 사항)',
                hintStyle: TextStyle(fontSize: 13, color: context.colors.textMuted),
                filled: true,
                fillColor: context.colors.bgCard,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.zero,
                  borderSide: BorderSide(color: context.colors.border, width: 0.8),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.zero,
                  borderSide: BorderSide(color: context.colors.border, width: 0.8),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.zero,
                  borderSide: BorderSide(color: actionColor, width: 1.2),
                ),
              ),
            ),
            if (_errorText != null) ...[
              const SizedBox(height: 6),
              Text(
                _errorText!,
                style: TextStyle(fontSize: 11.5, color: context.colors.error),
              ),
            ],
            const SizedBox(height: 16),
          ] else ...[
            // 상신 / 회수 확인 메시지
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.zero,
                border: Border.all(color: context.colors.borderSubtle, width: 0.8),
              ),
              child: Text(
                widget.type == ApprovalActionModalType.submit
                    ? '해당 문서를 다음 결재선으로 상신하시겠습니까?'
                    : '상신된 결재 문서를 회수하시겠습니까?\n회수 시 결재 진행이 취소되고 임시저장 상태로 변경됩니다.',
                style: TextStyle(
                  fontSize: 12.5,
                  color: context.colors.textSecond,
                  height: 1.4,
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],

          // ── 하단 버튼 (취소 / 실행) ───────────────────────────────────
          Row(
            children: [
              Expanded(
                child: SizedBox(
                  height: 44,
                  child: OutlinedButton(
                    onPressed: _isLoading ? null : () => Navigator.of(context).pop(),
                    style: OutlinedButton.styleFrom(
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      side: BorderSide(color: context.colors.border),
                    ),
                    child: Text(
                      '취소',
                      style: TextStyle(color: context.colors.textSecond),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: SizedBox(
                  height: 44,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _handleConfirm,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: actionColor,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      elevation: 0,
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : Text(
                            _actionTitle,
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
