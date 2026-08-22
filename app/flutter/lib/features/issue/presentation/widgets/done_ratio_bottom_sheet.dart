import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../providers/issue_provider.dart';

/// 진척률 슬라이더 바텀 시트
/// - 0~100%, 10 단위 스냅
/// - 저장 버튼 탭 → Optimistic Update
Future<void> showDoneRatioBottomSheet({
  required BuildContext context,
  required WidgetRef ref,
  required int issueId,
  required int currentRatio,
}) {
  return showModalBottomSheet(
    context: context,
    backgroundColor: context.colors.bgCard,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
    ),
    isScrollControlled: true,
    builder: (ctx) => _DoneRatioSheet(
      ref: ref,
      issueId: issueId,
      initialRatio: currentRatio,
    ),
  );
}

class _DoneRatioSheet extends StatefulWidget {
  final WidgetRef ref;
  final int issueId;
  final int initialRatio;

  const _DoneRatioSheet({
    required this.ref,
    required this.issueId,
    required this.initialRatio,
  });

  @override
  State<_DoneRatioSheet> createState() => _DoneRatioSheetState();
}

class _DoneRatioSheetState extends State<_DoneRatioSheet> {
  late double _ratio;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _ratio = widget.initialRatio.toDouble();
  }

  Future<void> _save() async {
    setState(() => _isSaving = true);
    try {
      await widget.ref
          .read(issueDetailProvider(widget.issueId).notifier)
          .updateDoneRatio(_ratio.round());
      if (mounted) Navigator.pop(context);
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('진척률 저장에 실패했습니다.'),
            backgroundColor: context.colors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final ratio = _ratio.round();
    final color = ratio == 100 ? context.colors.success : context.colors.accentWork;

    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 20, 24, 32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 핸들
          Center(
            child: Container(
              width: 40,
              height: 4,
              margin: const EdgeInsets.only(bottom: 20),
              decoration: BoxDecoration(
                color: context.colors.border,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),

          Text('진척률 수정', style: AppTextStyles.h3.copyWith(color: context.colors.textPrimary)),
          const SizedBox(height: 4),
          Text('#${widget.issueId} 업무의 진행률을 설정합니다.',
              style: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted)),
          const SizedBox(height: 24),

          // 현재 진척률 표시
          Center(
            child: Text(
              '$ratio%',
              style: AppTextStyles.h1.copyWith(color: color, fontSize: 48),
            ),
          ),
          const SizedBox(height: 8),

          // 진척률 프로그레스바
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: _ratio / 100.0,
              minHeight: 8,
              backgroundColor: context.colors.bgSurface,
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
          const SizedBox(height: 8),

          // 슬라이더
          SliderTheme(
            data: SliderThemeData(
              activeTrackColor: color,
              thumbColor: color,
              inactiveTrackColor: context.colors.bgSurface,
              overlayColor: color.withAlpha(30),
              trackHeight: 4,
              thumbShape:
                  const RoundSliderThumbShape(enabledThumbRadius: 12),
            ),
            child: Slider(
              value: _ratio,
              min: 0,
              max: 100,
              divisions: 10,
              onChanged: (v) => setState(() => _ratio = v),
            ),
          ),

          // 0 / 50 / 100 라벨
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: ['0%', '50%', '100%']
                .map((l) => Text(l, style: AppTextStyles.caption.copyWith(color: context.colors.textMuted)))
                .toList(),
          ),
          const SizedBox(height: 24),

          // 저장 버튼
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _isSaving ? null : _save,
              style: ElevatedButton.styleFrom(
                backgroundColor: color,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8)),
              ),
              child: _isSaving
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white),
                    )
                  : Text('$ratio% 저장', style: AppTextStyles.titleMd),
            ),
          ),
        ],
      ),
    );
  }
}
