import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:open_filex/open_filex.dart';
import 'package:share_plus/share_plus.dart';
import '../../../../core/constants/app_colors.dart';
import '../../data/meeting_repository.dart';
import '../../data/models/meeting_model.dart';

/// 회의록 PDF를 다운로드하여 즉시 화면에 열어 내용을 확인하고(인쇄/공유 가능) 필요 시 시스템 공유 시트로 연동하는 공용 헬퍼
Future<void> exportMeetingPdf(
  BuildContext context,
  WidgetRef ref,
  MeetingModel meeting,
) async {
  try {
    if (context.mounted) {
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Row(
            children: [
              SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(
                    strokeWidth: 2, color: Colors.white),
              ),
              SizedBox(width: 10),
              Text('회의록 PDF 생성 및 여는 중...'),
            ],
          ),
          duration: Duration(seconds: 2),
        ),
      );
    }

    final repo = ref.read(meetingRepositoryProvider);
    final filePath = await repo.downloadMeetingPdf(meeting.pk, meeting.title);

    if (!context.mounted) return;

    // 1. PDF 파일을 시스템 네이티브 뷰어(iOS QuickLook 등)로 즉시 열어 내용 확인
    // (iOS QuickLook 뷰어 상단에 네이티브 공유 및 AirPrint 인쇄 버튼이 기본 포함되어 있음)
    final openResult = await OpenFilex.open(filePath);

    if (openResult.type != ResultType.done) {
      if (!context.mounted) return;
      // 뷰어가 열리지 않는 예외 상황 시 공유 시트로 대체
      final box = context.findRenderObject() as RenderBox?;
      final origin =
          box != null ? box.localToGlobal(Offset.zero) & box.size : null;

      await Share.shareXFiles(
        [XFile(filePath)],
        subject: '회의록: ${meeting.title}',
        sharePositionOrigin: origin,
      );
    }
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('PDF 열기 실패: $e'),
          backgroundColor: AppColors.error,
        ),
      );
    }
  }
}
