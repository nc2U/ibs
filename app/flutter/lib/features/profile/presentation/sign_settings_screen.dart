import 'dart:io';
import 'dart:ui' as ui;
import 'package:cached_network_image/cached_network_image.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';

import '../../../core/constants/app_text_styles.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/providers/dio_provider.dart';
import '../../../core/theme/app_colors_extension.dart';

/// 🖋️ 전자결재 인장 및 서명 관리 화면
class SignSettingsScreen extends ConsumerStatefulWidget {
  const SignSettingsScreen({super.key});

  @override
  ConsumerState<SignSettingsScreen> createState() => _SignSettingsScreenState();
}

class _SignSettingsScreenState extends ConsumerState<SignSettingsScreen> {
  String _signType = 'STAMP'; // 'STAMP' (도장) 또는 'SIGN' (사인)
  String? _serverSignImageUrl;
  File? _newSignImageFile;
  bool _isLoading = true;
  bool _isSaving = false;

  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _loadInitialSign();
  }

  void _loadInitialSign() {
    final user = ref.read(currentUserProvider).valueOrNull;
    final profile = user?.profile;
    if (profile != null) {
      _signType = profile.signType;
      _serverSignImageUrl = profile.signImage;
    }
    setState(() => _isLoading = false);
  }

  /// 갤러리/사진첩에서 이미지 선택
  Future<void> _pickImageFromGallery() async {
    try {
      final picked = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 600,
        maxHeight: 600,
        imageQuality: 90,
      );
      if (picked != null) {
        setState(() {
          _newSignImageFile = File(picked.path);
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('이미지 선택 중 오류가 발생했습니다: $e'),
            backgroundColor: context.colors.error,
          ),
        );
      }
    }
  }

  /// 직접 터치로 서명 그리기 다이얼로그 호출
  Future<void> _openDrawPadModal() async {
    final resultFile = await showModalBottomSheet<File?>(
      context: context,
      isScrollControlled: true,
      enableDrag: false, // 서명 터치 제스처 시 바텀시트가 드래그되어 닫히거나 흔들리는 문제 방지
      backgroundColor: Colors.transparent,
      builder: (_) => const _SignPadBottomSheet(),
    );

    if (resultFile != null && mounted) {
      setState(() {
        _newSignImageFile = resultFile;
        _signType = 'SIGN'; // 직접 서명한 경우 기본 타입을 서명으로 맞춤
      });
    }
  }

  /// 서버로 저장 (multipart/form-data)
  Future<void> _saveSign() async {
    final user = ref.read(currentUserProvider).valueOrNull;
    final profilePk = user?.profile?.pk;
    if (user == null || profilePk == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('프로필 정보가 유효하지 않습니다.'),
          backgroundColor: context.colors.error,
        ),
      );
      return;
    }

    setState(() => _isSaving = true);
    final dio = ref.read(dioProvider);

    try {
      final mapData = <String, dynamic>{
        'sign_type': _signType,
      };

      if (_newSignImageFile != null) {
        final fileName = _newSignImageFile!.path.split('/').last;
        mapData['sign_image'] = await MultipartFile.fromFile(
          _newSignImageFile!.path,
          filename: fileName,
        );
      }

      final formData = FormData.fromMap(mapData);

      await dio.patch(
        '/api/v1/profile/$profilePk/',
        data: formData,
      );

      // 사용자 정보 갱신
      ref.invalidate(currentUserProvider);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('결재 인장/서명이 성공적으로 저장되었습니다.'),
            behavior: SnackBarBehavior.floating,
            backgroundColor: Color(0xFF10B981),
          ),
        );
        Navigator.pop(context);
      }
    } on DioException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('저장 실패: ${e.response?.data ?? e.message}'),
            behavior: SnackBarBehavior.floating,
            backgroundColor: context.colors.error,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('오류 발생: $e'),
            behavior: SnackBarBehavior.floating,
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
    if (_isLoading) {
      return Scaffold(
        backgroundColor: context.colors.bgPrimary,
        appBar: AppBar(title: const Text('결재 인장 / 서명 관리')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    final hasImage = _newSignImageFile != null ||
        (_serverSignImageUrl != null && _serverSignImageUrl!.isNotEmpty);

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      appBar: AppBar(
        backgroundColor: context.colors.bgPrimary,
        elevation: 0,
        title: Text(
          '결재 인장 / 서명 관리',
          style: AppTextStyles.titleLg.copyWith(
            fontWeight: FontWeight.bold,
            color: context.colors.textPrimary,
          ),
        ),
        actions: [
          TextButton(
            onPressed: _isSaving ? null : _saveSign,
            child: _isSaving
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Text(
                    '저장',
                    style: AppTextStyles.bodyMd.copyWith(
                      fontWeight: FontWeight.bold,
                      color: context.colors.accentApproval,
                    ),
                  ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── 상단 안내 카드 ──────────────────────────────────────────
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    Icons.info_outline_rounded,
                    color: context.colors.accentApproval,
                    size: 20,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '전자결재 날인 안내',
                          style: AppTextStyles.bodyMd.copyWith(
                            fontWeight: FontWeight.bold,
                            color: context.colors.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '등록된 인장 또는 서명은 전자결재 승인 시 최종 문서의 결재란에 자동 날인됩니다.\n미등록 시에는 시스템 기본 규격 도장으로 자동 처리됩니다.',
                          style: AppTextStyles.caption.copyWith(
                            color: context.colors.textMuted,
                            height: 1.4,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // ── 날인 방식 선택 (도장 vs 서명) ─────────────────────────────
            Text(
              '날인 구분',
              style: AppTextStyles.titleSm.copyWith(
                fontWeight: FontWeight.bold,
                color: context.colors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              decoration: BoxDecoration(
                color: context.colors.bgCard,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: context.colors.border, width: 0.8),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: InkWell(
                      onTap: () => setState(() => _signType = 'STAMP'),
                      borderRadius: const BorderRadius.horizontal(left: Radius.circular(8)),
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        decoration: BoxDecoration(
                          color: _signType == 'STAMP'
                              ? context.colors.accentApproval.withValues(alpha: 0.15)
                              : Colors.transparent,
                          borderRadius: const BorderRadius.horizontal(left: Radius.circular(8)),
                          border: _signType == 'STAMP'
                              ? Border.all(color: context.colors.accentApproval, width: 1.2)
                              : null,
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.verified_outlined,
                              size: 18,
                              color: _signType == 'STAMP'
                                  ? context.colors.accentApproval
                                  : context.colors.textMuted,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              '도장 (인장)',
                              style: AppTextStyles.bodyMd.copyWith(
                                fontWeight: _signType == 'STAMP'
                                    ? FontWeight.bold
                                    : FontWeight.normal,
                                color: _signType == 'STAMP'
                                    ? context.colors.accentApproval
                                    : context.colors.textSecond,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  Container(width: 1, height: 40, color: context.colors.border),
                  Expanded(
                    child: InkWell(
                      onTap: () => setState(() => _signType = 'SIGN'),
                      borderRadius: const BorderRadius.horizontal(right: Radius.circular(8)),
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        decoration: BoxDecoration(
                          color: _signType == 'SIGN'
                              ? context.colors.accentApproval.withValues(alpha: 0.15)
                              : Colors.transparent,
                          borderRadius: const BorderRadius.horizontal(right: Radius.circular(8)),
                          border: _signType == 'SIGN'
                              ? Border.all(color: context.colors.accentApproval, width: 1.2)
                              : null,
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.draw_outlined,
                              size: 18,
                              color: _signType == 'SIGN'
                                  ? context.colors.accentApproval
                                  : context.colors.textMuted,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              '사인 (서명)',
                              style: AppTextStyles.bodyMd.copyWith(
                                fontWeight: _signType == 'SIGN'
                                    ? FontWeight.bold
                                    : FontWeight.normal,
                                color: _signType == 'SIGN'
                                    ? context.colors.accentApproval
                                    : context.colors.textSecond,
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
            const SizedBox(height: 24),

            // ── 인장/서명 미리보기 박스 ──────────────────────────────────
            Text(
              '인장 / 서명 미리보기',
              style: AppTextStyles.titleSm.copyWith(
                fontWeight: FontWeight.bold,
                color: context.colors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Center(
              child: Container(
                width: 180,
                height: 180,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: hasImage ? context.colors.accentApproval : context.colors.border,
                    width: 1.5,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.08),
                      blurRadius: 8,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      // 격자 배경 (투명 이미지 확인용)
                      CustomPaint(
                        size: const Size(180, 180),
                        painter: _CheckerboardPainter(),
                      ),
                      if (_newSignImageFile != null)
                        Image.file(
                          _newSignImageFile!,
                          width: 150,
                          height: 150,
                          fit: BoxFit.contain,
                        )
                      else if (_serverSignImageUrl != null && _serverSignImageUrl!.isNotEmpty)
                        CachedNetworkImage(
                          imageUrl: _serverSignImageUrl!,
                          width: 150,
                          height: 150,
                          fit: BoxFit.contain,
                          placeholder: (_, __) => const Center(
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                          errorWidget: (_, __, ___) => const Center(
                            child: Icon(Icons.broken_image, color: Colors.grey, size: 36),
                          ),
                        )
                      else
                        Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              _signType == 'STAMP' ? Icons.verified_outlined : Icons.draw_outlined,
                              size: 44,
                              color: Colors.grey.shade400,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              '등록된 인장/서명 없음',
                              style: AppTextStyles.caption.copyWith(
                                color: Colors.grey.shade600,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              '(기본 도장으로 날인됨)',
                              style: AppTextStyles.caption.copyWith(
                                color: Colors.grey.shade400,
                                fontSize: 11,
                              ),
                            ),
                          ],
                        ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 24),

            // ── 서명 등록 액션 버튼 그룹 ─────────────────────────────────
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: context.colors.textPrimary,
                      side: BorderSide(color: context.colors.border),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    onPressed: _pickImageFromGallery,
                    icon: const Icon(Icons.photo_library_outlined, size: 18),
                    label: const Text('이미지 업로드'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: context.colors.accentApproval,
                      foregroundColor: Colors.white,
                      elevation: 0,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    onPressed: _openDrawPadModal,
                    icon: const Icon(Icons.edit_outlined, size: 18),
                    label: const Text('직접 서명 그리기'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // ── 안내 텍스트 ──────────────────────────────────────────────
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: context.colors.bgSurface,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '💡 서명 등록 팁',
                    style: AppTextStyles.caption.copyWith(
                      fontWeight: FontWeight.bold,
                      color: context.colors.textSecond,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '• 모바일에서는 [직접 서명 그리기]를 통해 터치로 서명하는 것이 가장 편리합니다.\n'
                    '• 실물 도장 이미지를 업로드하실 경우, 배경이 투명한 PNG 형식의 원형/정사각형 이미지를 권장합니다.',
                    style: AppTextStyles.caption.copyWith(
                      color: context.colors.textMuted,
                      height: 1.4,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

/// ✍️ 직접 터치 서명 바텀시트
class _SignPadBottomSheet extends StatefulWidget {
  const _SignPadBottomSheet();

  @override
  State<_SignPadBottomSheet> createState() => _SignPadBottomSheetState();
}

class _SignPadBottomSheetState extends State<_SignPadBottomSheet> {
  final List<Offset?> _points = [];
  bool _isExporting = false;

  void _clear() {
    setState(() {
      _points.clear();
    });
  }

  Future<void> _exportSignature() async {
    if (_points.where((p) => p != null).isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('서명을 화면에 그려주세요.')),
      );
      return;
    }

    setState(() => _isExporting = true);

    try {
      final recorder = ui.PictureRecorder();
      final canvas = Canvas(recorder);
      const size = Size(320, 240);

      // 투명 배경에 서명 선 렌더링
      final paint = Paint()
        ..color = Colors.black
        ..strokeCap = StrokeCap.round
        ..strokeWidth = 3.5;

      for (int i = 0; i < _points.length - 1; i++) {
        if (_points[i] != null && _points[i + 1] != null) {
          canvas.drawLine(_points[i]!, _points[i + 1]!, paint);
        }
      }

      final picture = recorder.endRecording();
      final img = await picture.toImage(size.width.toInt(), size.height.toInt());
      final byteData = await img.toByteData(format: ui.ImageByteFormat.png);

      if (byteData == null) throw Exception('이미지 변환 실패');

      final buffer = byteData.buffer.asUint8List();
      final tempDir = await getTemporaryDirectory();
      final file = File('${tempDir.path}/drawn_sign_${DateTime.now().millisecondsSinceEpoch}.png');
      await file.writeAsBytes(buffer);

      if (mounted) {
        Navigator.of(context).pop(file);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('서명 저장 중 오류가 발생했습니다: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isExporting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
        top: 16,
        left: 16,
        right: 16,
      ),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '직접 서명 그리기',
                style: AppTextStyles.titleLg.copyWith(
                  fontWeight: FontWeight.bold,
                  color: context.colors.textPrimary,
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            '박스 안을 터치하여 서명을 그려주세요.',
            style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
          ),
          const SizedBox(height: 12),

          // ── 서명 캔버스 박스 ──────────────────────────────────────────
          Container(
            width: double.infinity,
            height: 220,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: context.colors.accentApproval, width: 1.5),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(9),
              child: GestureDetector(
                behavior: HitTestBehavior.opaque,
                onPanDown: (details) {
                  setState(() {
                    _points.add(details.localPosition);
                  });
                },
                onPanStart: (details) {
                  setState(() {
                    _points.add(details.localPosition);
                  });
                },
                onPanUpdate: (details) {
                  setState(() {
                    _points.add(details.localPosition);
                  });
                },
                onPanEnd: (_) => setState(() => _points.add(null)),
                child: CustomPaint(
                  painter: _SignPainter(points: _points),
                  size: Size.infinite,
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),

          // ── 바닥 컨트롤 버튼 ──────────────────────────────────────────
          Row(
            children: [
              TextButton.icon(
                style: TextButton.styleFrom(
                  foregroundColor: context.colors.textMuted,
                ),
                onPressed: _clear,
                icon: const Icon(Icons.refresh_rounded, size: 18),
                label: const Text('지우기'),
              ),
              const Spacer(),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: context.colors.accentApproval,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
                onPressed: _isExporting ? null : _exportSignature,
                child: _isExporting
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('서명 적용하기'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// 🎨 서명 그리기 페인터
class _SignPainter extends CustomPainter {
  final List<Offset?> points;
  _SignPainter({required this.points});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.black
      ..strokeCap = StrokeCap.round
      ..strokeWidth = 3.5;

    for (int i = 0; i < points.length - 1; i++) {
      if (points[i] != null && points[i + 1] != null) {
        canvas.drawLine(points[i]!, points[i + 1]!, paint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _SignPainter oldDelegate) => true;
}

/// 🏁 투명 배경용 체크패턴 페인터
class _CheckerboardPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = const Color(0xFFF1F5F9);
    const cellSize = 10.0;
    for (double x = 0; x < size.width; x += cellSize) {
      for (double y = 0; y < size.height; y += cellSize) {
        if (((x / cellSize).floor() + (y / cellSize).floor()) % 2 == 0) {
          canvas.drawRect(Rect.fromLTWH(x, y, cellSize, cellSize), paint);
        }
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
