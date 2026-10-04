import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:open_filex/open_filex.dart';
import 'package:share_plus/share_plus.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/services/share_helper.dart';
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
    final sanitizedTitle = meeting.title.replaceAll(RegExp(r'[\\/:*?"<>|]'), '_');

    // 1. Web 환경: 브라우저 Blob 다운로드 및 공유 연동 (로컬 파일시스템 미지원 환경 대응)
    if (kIsWeb) {
      final bytes = await repo.downloadMeetingPdfBytes(meeting.pk);
      if (!context.mounted) return;
      final box = context.findRenderObject() as RenderBox?;
      final origin =
          box != null ? box.localToGlobal(Offset.zero) & box.size : null;

      final xfile = XFile.fromData(
        Uint8List.fromList(bytes),
        mimeType: 'application/pdf',
        name: '회의록_${sanitizedTitle}_#${meeting.pk}.pdf',
      );

      await AppShareHelper.shareXFiles(
        [xfile],
        subject: '회의록: ${meeting.title}',
        sharePositionOrigin: origin,
      );
      return;
    }

    // 2. 모바일/데스크톱 환경: 로컬 임시 파일 저장 후 네이티브 뷰어로 열기
    final filePath = await repo.downloadMeetingPdf(meeting.pk, meeting.title);

    // PDF 파일을 시스템 네이티브 뷰어(iOS QuickLook, Android PDF 앱 등)로 즉시 열어 내용 확인
    ResultType? openType;
    try {
      final openResult = await OpenFilex.open(filePath);
      openType = openResult.type;
    } catch (_) {
      openType = ResultType.error;
    }

    // PDF 뷰어 앱이 설치되어 있지 않거나 열기 실패 시 시스템 공유 시트(Share)로 자동 폴백
    if (openType != ResultType.done) {
      if (!context.mounted) return;
      final box = context.findRenderObject() as RenderBox?;
      final origin =
          box != null ? box.localToGlobal(Offset.zero) & box.size : null;

      await AppShareHelper.shareXFiles(
        [XFile(filePath)],
        subject: '회의록: ${meeting.title}',
        sharePositionOrigin: origin,
      );
    }
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('PDF 처리 실패: $e'),
          backgroundColor: AppColors.error,
        ),
      );
    }
  }
}
