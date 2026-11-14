import 'package:material_ui/material_ui.dart';
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
    final willComplete = ratio == 100 && widget.initialRatio < 100;
    final willReopen = ratio < 100 && widget.initialRatio == 100;

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

          // 슬라이더 (5% 단위)
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
              divisions: 20,
              onChanged: (v) => setState(() => _ratio = v),
            ),
          ),

          // 빠른 선택 칩 (0%, 25%, 50%, 75%, 100%)
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [0, 25, 50, 75, 100].map((preset) {
              final isSelected = ratio == preset;
              return InkWell(
                borderRadius: BorderRadius.circular(6),
                onTap: () => setState(() => _ratio = preset.toDouble()),
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: isSelected
                        ? (preset == 100
                            ? context.colors.success
                            : context.colors.accentWork)
                        : context.colors.bgInput,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(
                      color: isSelected
                          ? Colors.transparent
                          : context.colors.borderSubtle,
                    ),
                  ),
                  child: Text(
                    '$preset%',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight:
                          isSelected ? FontWeight.bold : FontWeight.normal,
                      color: isSelected ? Colors.white : context.colors.textMuted,
                    ),
                  ),
                ),
              );
            }).toList(),
          ),

          if (willComplete || willReopen) ...[
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: color.withAlpha(20),
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: color.withAlpha(60), width: 0.8),
              ),
              child: Row(
                children: [
                  Icon(
                    willComplete
                        ? Icons.check_circle_outline_rounded
                        : Icons.autorenew_rounded,
                    size: 16,
                    color: color,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      willComplete
                          ? '100% 저장 시 업무 상태가 [완료]로 함께 변경됩니다.'
                          : '100% 미만으로 저장 시 업무 상태가 [진행]으로 전환됩니다.',
                      style: AppTextStyles.caption.copyWith(
                        color: color,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 20),

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
