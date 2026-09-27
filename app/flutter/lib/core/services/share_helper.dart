import 'dart:ui';
import 'package:share_plus/share_plus.dart';

/// Helper wrapper for SharePlus to migrate from deprecated Share.shareXFiles
class AppShareHelper {
  AppShareHelper._();

  /// Shares files using [SharePlus.instance.share]
  static Future<ShareResult> shareXFiles(
    List<XFile> files, {
    String? subject,
    String? text,
    Rect? sharePositionOrigin,
  }) async {
    return SharePlus.instance.share(
      ShareParams(
        files: files,
        subject: subject,
        text: text,
        sharePositionOrigin: sharePositionOrigin,
      ),
    );
  }
}
