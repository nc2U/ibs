import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:open_filex/open_filex.dart';
import 'package:share_plus/share_plus.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../data/approval_repository.dart';
import '../../data/models/approval_model.dart';

/// 결재 문서 PDF를 다운로드하여 즉시 시스템 뷰어로 열고 인쇄/공유하는 헬퍼
Future<void> exportApprovalPdf(
  BuildContext context,
  WidgetRef ref,
  ApprovalDocumentModel document,
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
                  strokeWidth: 2,
                  color: Colors.white,
                ),
              ),
              SizedBox(width: 10),
              Text('전자결재 PDF 생성 및 여는 중...'),
            ],
          ),
          duration: Duration(seconds: 2),
        ),
      );
    }

    final repo = ref.read(approvalRepositoryProvider);
    final filePath = await repo.downloadDocumentPdf(
      document.id,
      document.title,
      pdfUrl: document.pdfUrl,
    );

    if (context.mounted) {
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
    }

    ResultType? openType;
    try {
      final openResult = await OpenFilex.open(filePath);
      openType = openResult.type;
    } catch (_) {
      openType = ResultType.error;
    }

    if (openType != ResultType.done) {
      if (!context.mounted) return;
      final box = context.findRenderObject() as RenderBox?;
      final origin = box != null ? box.localToGlobal(Offset.zero) & box.size : null;

      await Share.shareXFiles(
        [XFile(filePath)],
        subject: '전자결재: ${document.title}',
        sharePositionOrigin: origin,
      );
    }
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('PDF 다운로드/열기 실패: $e'),
          backgroundColor: context.colors.error,
        ),
      );
    }
  }
}
