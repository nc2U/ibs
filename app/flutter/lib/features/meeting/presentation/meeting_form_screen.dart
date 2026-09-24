import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'package:go_router/go_router.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';
import '../../../core/api/api_client.dart';
import '../../../core/constants/app_text_styles.dart';
import '../../../core/models/common_models.dart';
import '../../../core/providers/project_provider.dart';
import '../../../core/theme/app_colors_extension.dart';
import '../data/meeting_repository.dart';
import '../data/models/meeting_model.dart';
import '../providers/meeting_provider.dart';

import '../../project/providers/project_provider.dart';

/// 회의 생성 및 수정 폼 화면
class MeetingFormScreen extends ConsumerStatefulWidget {
  final MeetingModel? initialMeeting;

  const MeetingFormScreen({super.key, this.initialMeeting});

  @override
  ConsumerState<MeetingFormScreen> createState() => _MeetingFormScreenState();
}

class _MeetingFormScreenState extends ConsumerState<MeetingFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _titleController;
  late TextEditingController _meetingDateController;
  late TextEditingController _locationController;
  late TextEditingController _otherAttendeesController;
  late TextEditingController _agendaController;
  late TextEditingController _contentController;
  late TextEditingController _decisionsController;
  late TextEditingController _actionItemsController;

  String _status = '1'; // 1: 예정, 2: 종료
  bool _isConfirmed = false;
  bool _isSaving = false;
  int? _selectedProjectPk;
  int? _selectedCategoryPk;
  List<int> _selectedAttendeePks = [];

  // ── AI 음성 녹음 및 분석 상태 ─────────────────────────
  final AudioRecorder _audioRecorder = AudioRecorder();
  bool _isRecording = false;
  int _recordingSeconds = 0;
  Timer? _recordingTimer;
  String? _currentRecordingPath;
  bool _isAiAnalyzing = false;
  String _aiStatusMessage = '';

  @override
  void initState() {
    super.initState();
    final m = widget.initialMeeting;
    _titleController = TextEditingController(text: m?.title ?? '');
    _locationController = TextEditingController(text: m?.location ?? '');

    String initialDateStr = '';
    if (m?.meetingDate != null && m!.meetingDate.isNotEmpty) {
      final clean = m.meetingDate.replaceAll('T', ' ');
      initialDateStr = clean.length >= 16 ? clean.substring(0, 16) : clean;
    } else {
      final now = DateTime.now();
      final y = now.year.toString().padLeft(4, '0');
      final mo = now.month.toString().padLeft(2, '0');
      final d = now.day.toString().padLeft(2, '0');
      final h = now.hour.toString().padLeft(2, '0');
      final mi = now.minute.toString().padLeft(2, '0');
      initialDateStr = '$y-$mo-$d $h:$mi';
    }
    _meetingDateController = TextEditingController(text: initialDateStr);

    _otherAttendeesController =
        TextEditingController(text: m?.otherAttendees ?? '');
    _agendaController = TextEditingController(text: m?.agenda ?? '');
    _contentController = TextEditingController(text: m?.content ?? '');
    _decisionsController = TextEditingController(text: m?.decisions ?? '');
    _actionItemsController = TextEditingController(text: m?.actionItems ?? '');

    if (m != null) {
      _status = m.status;
      _isConfirmed = m.isConfirmed;
      _selectedCategoryPk = m.category;
      _selectedAttendeePks = List.from(m.attendees);
      _selectedProjectPk = m.project;
    } else {
      final selectedProj = ref.read(selectedProjectProvider);
      if (selectedProj != null) {
        _selectedProjectPk = selectedProj.pk;
      }
    }
  }

  @override
  void dispose() {
    _recordingTimer?.cancel();
    _audioRecorder.dispose();
    _titleController.dispose();
    _meetingDateController.dispose();
    _locationController.dispose();
    _otherAttendeesController.dispose();
    _agendaController.dispose();
    _contentController.dispose();
    _decisionsController.dispose();
    _actionItemsController.dispose();
    super.dispose();
  }

  String _formatRecordingTime(int seconds) {
    final m = (seconds ~/ 60).toString().padLeft(2, '0');
    final s = (seconds % 60).toString().padLeft(2, '0');
    return '$m:$s';
  }

  Future<void> _startRecording() async {
    try {
      if (await _audioRecorder.hasPermission()) {
        final tempDir = await getTemporaryDirectory();
        final path = '${tempDir.path}/meeting_record_${DateTime.now().millisecondsSinceEpoch}.m4a';

        await _audioRecorder.start(
          const RecordConfig(encoder: AudioEncoder.aacLc),
          path: path,
        );

        _currentRecordingPath = path;
        _recordingSeconds = 0;
        _isRecording = true;

        _recordingTimer?.cancel();
        _recordingTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
          if (mounted) {
            setState(() => _recordingSeconds++);
          }
        });

        setState(() {});
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: const Text('마이크 접근 권한이 필요합니다.'),
              backgroundColor: context.colors.error,
            ),
          );
        }
      }
    } catch (e) {
      debugPrint('Error starting audio recording: $e');
    }
  }

  Future<void> _stopRecordingAndAnalyze() async {
    try {
      final path = await _audioRecorder.stop();
      _recordingTimer?.cancel();
      setState(() {
        _isRecording = false;
      });

      final finalPath = path ?? _currentRecordingPath;
      if (finalPath != null && File(finalPath).existsSync()) {
        await _processAudioFileWithAi(File(finalPath));
      }
    } catch (e) {
      debugPrint('Error stopping audio recording: $e');
    }
  }

  Future<void> _cancelRecording() async {
    try {
      await _audioRecorder.stop();
      _recordingTimer?.cancel();
      if (_currentRecordingPath != null) {
        final f = File(_currentRecordingPath!);
        if (f.existsSync()) await f.delete();
      }
      setState(() {
        _isRecording = false;
        _recordingSeconds = 0;
        _currentRecordingPath = null;
      });
    } catch (e) {
      debugPrint('Error canceling audio recording: $e');
    }
  }

  Future<void> _pickAudioFile() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['m4a', 'mp3', 'wav', 'aac', 'ogg', 'webm'],
      );

      if (result != null && result.files.single.path != null) {
        final file = File(result.files.single.path!);
        await _processAudioFileWithAi(file);
      }
    } catch (e) {
      debugPrint('Error picking audio file: $e');
    }
  }

  Future<void> _processAudioFileWithAi(File audioFile) async {
    setState(() {
      _isAiAnalyzing = true;
      _aiStatusMessage = 'AI 음성 인식 및 회의록 분석 중...';
    });

    try {
      final repo = ref.read(meetingRepositoryProvider);
      final aiData = await repo.aiSummarizeAudio(audioFile);

      if (mounted) {
        setState(() {
          if (aiData['title'] != null && (aiData['title'] as String).isNotEmpty) {
            _titleController.text = aiData['title'];
          }
          if (aiData['agenda'] != null && (aiData['agenda'] as String).isNotEmpty) {
            _agendaController.text = aiData['agenda'];
          }
          if (aiData['content'] != null && (aiData['content'] as String).isNotEmpty) {
            _contentController.text = aiData['content'];
          }
          if (aiData['decisions'] != null && (aiData['decisions'] as String).isNotEmpty) {
            _decisionsController.text = aiData['decisions'];
          }
          if (aiData['action_items'] != null && (aiData['action_items'] as String).isNotEmpty) {
            _actionItemsController.text = aiData['action_items'];
          }
        });

        // 카테고리 자동 매핑
        final catName = aiData['category_name'] as String?;
        if (catName != null && catName.isNotEmpty) {
          final cats = ref.read(meetingCategoriesProvider(_selectedProjectPk)).valueOrNull ?? [];
          final match = cats.where((c) => c.name.contains(catName) || catName.contains(c.name)).firstOrNull;
          if (match != null) {
            setState(() => _selectedCategoryPk = match.pk);
          }
        }

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('✨ AI 회의록 분석이 완료되어 폼에 반영되었습니다.'),
            backgroundColor: context.colors.success,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('AI 회의록 생성 실패: ${getDioErrorMessage(e)}'),
            backgroundColor: context.colors.error,
          ),
        );
      }
    } finally {
      // 분석 완료 즉시 임시 오디오 파일 삭제
      try {
        if (audioFile.existsSync()) await audioFile.delete();
      } catch (_) {}

      if (mounted) {
        setState(() {
          _isAiAnalyzing = false;
          _aiStatusMessage = '';
          _currentRecordingPath = null;
        });
      }
    }
  }

  Future<void> _selectDateTime() async {
    DateTime initialDateTime = DateTime.now();
    try {
      final text = _meetingDateController.text.trim();
      if (text.isNotEmpty) {
        final parsed = DateTime.tryParse(text.replaceAll(' ', 'T'));
        if (parsed != null) initialDateTime = parsed;
      }
    } catch (_) {}

    final pickedDate = await showDatePicker(
      context: context,
      initialDate: initialDateTime,
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
    );
    if (pickedDate == null || !mounted) return;

    final pickedTime = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(initialDateTime),
    );
    if (pickedTime == null || !mounted) return;

    final y = pickedDate.year.toString().padLeft(4, '0');
    final mo = pickedDate.month.toString().padLeft(2, '0');
    final d = pickedDate.day.toString().padLeft(2, '0');
    final h = pickedTime.hour.toString().padLeft(2, '0');
    final mi = pickedTime.minute.toString().padLeft(2, '0');

    _meetingDateController.text = '$y-$mo-$d $h:$mi';
  }

  Future<void> _showAddCategoryDialog() async {
    final textController = TextEditingController();
    final formKey = GlobalKey<FormState>();

    final createdCategory = await showDialog<MeetingCategoryModel?>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(
          '새 회의 카테고리 추가',
          style: AppTextStyles.titleSm.copyWith(
            fontWeight: FontWeight.bold,
            color: context.colors.textPrimary,
          ),
        ),
        content: Form(
          key: formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                _selectedProjectPk != null
                    ? '현재 워크스페이스 전용 카테고리로 등록됩니다.'
                    : '전체 공용 카테고리로 등록됩니다.',
                style: TextStyle(fontSize: 11, color: context.colors.textMuted),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: textController,
                autofocus: true,
                style: TextStyle(color: context.colors.textPrimary),
                decoration: _inputDecoration('카테고리명 입력 (예: 설계/인허가, 분양)'),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? '카테고리명을 입력해 주세요.' : null,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('취소'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: context.colors.accentWork,
              foregroundColor: Colors.white,
            ),
            onPressed: () async {
              if (!formKey.currentState!.validate()) return;
              try {
                final newCat = await ref.read(meetingRepositoryProvider).createCategory(
                  name: textController.text.trim(),
                  projectPk: _selectedProjectPk,
                );
                if (ctx.mounted) Navigator.pop(ctx, newCat);
              } catch (e) {
                if (ctx.mounted) {
                  ScaffoldMessenger.of(ctx).showSnackBar(
                    SnackBar(
                      content: Text('카테고리 생성 실패: ${getDioErrorMessage(e)}'),
                      backgroundColor: Colors.redAccent,
                    ),
                  );
                }
              }
            },
            child: const Text('추가'),
          ),
        ],
      ),
    );

    if (createdCategory != null && mounted) {
      ref.invalidate(meetingCategoriesProvider(_selectedProjectPk));
      setState(() => _selectedCategoryPk = createdCategory.pk);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("'${createdCategory.name}' 카테고리가 추가되어 선택되었습니다."),
          backgroundColor: context.colors.success,
        ),
      );
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    if (widget.initialMeeting == null && _selectedProjectPk == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('프로젝트를 먼저 선택해 주세요.'),
          backgroundColor: context.colors.error,
        ),
      );
      return;
    }

    setState(() => _isSaving = true);

    final meetingDateText = _meetingDateController.text.trim();
    final payload = <String, dynamic>{
      'title': _titleController.text.trim(),
      'status': _status,
      'is_confirmed': _isConfirmed,
      'category': _selectedCategoryPk,
      'location': _locationController.text.trim(),
      'attendees': _selectedAttendeePks,
      'other_attendees': _otherAttendeesController.text.trim(),
      'agenda': _agendaController.text.trim(),
      'content': _contentController.text.trim(),
      'decisions': _decisionsController.text.trim(),
      'action_items': _actionItemsController.text.trim(),
    };
    if (meetingDateText.isNotEmpty) {
      payload['meeting_date'] = meetingDateText;
    } else {
      payload['meeting_date'] = null;
    }

    if (widget.initialMeeting == null && _selectedProjectPk != null) {
      payload['project'] = _selectedProjectPk;
    }

    try {
      if (widget.initialMeeting != null) {
        await ref
            .read(meetingRepositoryProvider)
            .updateMeeting(widget.initialMeeting!.pk, payload);
        ref.invalidate(meetingDetailProvider(widget.initialMeeting!.pk));
      } else {
        await ref.read(meetingRepositoryProvider).createMeeting(payload);
      }
      ref.invalidate(meetingListProvider);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(widget.initialMeeting != null
                ? '회의록이 수정되었습니다.'
                : '새 회의록이 등록되었습니다.'),
            backgroundColor: context.colors.success,
          ),
        );
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        final errorMsg = getDioErrorMessage(e);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('저장 실패: $errorMsg'),
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
    final isEdit = widget.initialMeeting != null;
    final projectsAsync = ref.watch(meetingFormProjectsProvider);

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      appBar: AppBar(
        backgroundColor: context.colors.bgPrimary,
        foregroundColor: context.colors.textPrimary,
        title:
            Text(isEdit ? '회의록 수정' : '새 회의록 작성', style: AppTextStyles.titleMd.copyWith(color: context.colors.textPrimary)),
        actions: [
          TextButton(
            onPressed: _isSaving ? null : _submit,
            child: _isSaving
                ? SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: context.colors.accentWork),
                  )
                : Text('저장',
                    style: AppTextStyles.titleSm
                        .copyWith(color: context.colors.accentWork)),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── 섹션 1: 회의 개요 ─────────────────────────────────────────
              _buildSectionHeader('회의 개요', Icons.info_outline_rounded),

              // ── 🎙️ AI 음성 회의록 생성 배너 (신규 작성 시) ───────────────
              if (!isEdit) ...[
                Container(
                  width: double.infinity,
                  margin: const EdgeInsets.only(bottom: 18),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: context.colors.accentWork.withAlpha(20),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: context.colors.accentWork.withAlpha(60),
                      width: 1,
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.auto_awesome, size: 18, color: context.colors.accentWork),
                          const SizedBox(width: 6),
                          Text(
                            'AI 음성 회의록 자동 생성',
                            style: AppTextStyles.titleSm.copyWith(
                              color: context.colors.accentWork,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        '회의실 음성을 실시간 녹음하거나 오디오 파일을 분석하여 회의 제목, 의제, 본문, 결정 사항 및 후속 조치를 자동 완성합니다.',
                        style: AppTextStyles.caption.copyWith(color: context.colors.textMuted),
                      ),
                      const SizedBox(height: 12),

                      if (_isAiAnalyzing) ...[
                        Row(
                          children: [
                            SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: context.colors.accentWork,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                _aiStatusMessage,
                                style: AppTextStyles.caption.copyWith(
                                  color: context.colors.accentWork,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ] else if (_isRecording) ...[
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          decoration: BoxDecoration(
                            color: Colors.red.withAlpha(25),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.redAccent.withAlpha(80)),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.fiber_manual_record, color: Colors.red, size: 16),
                              const SizedBox(width: 8),
                              Text(
                                '녹음 중: ${_formatRecordingTime(_recordingSeconds)}',
                                style: AppTextStyles.titleSm.copyWith(
                                  color: Colors.red,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const Spacer(),
                              TextButton(
                                onPressed: _cancelRecording,
                                child: Text('취소', style: AppTextStyles.caption.copyWith(color: context.colors.textMuted)),
                              ),
                              const SizedBox(width: 4),
                              ElevatedButton.icon(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: context.colors.success,
                                  foregroundColor: Colors.white,
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                  minimumSize: Size.zero,
                                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                ),
                                icon: const Icon(Icons.stop, size: 14),
                                label: const Text('완료 & 분석', style: TextStyle(fontSize: 12)),
                                onPressed: _stopRecordingAndAnalyze,
                              ),
                            ],
                          ),
                        ),
                      ] else ...[
                        Row(
                          children: [
                            ElevatedButton.icon(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.redAccent,
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                              ),
                              icon: const Icon(Icons.mic, size: 16),
                              label: const Text('실시간 녹음 시작'),
                              onPressed: _startRecording,
                            ),
                            const SizedBox(width: 8),
                            OutlinedButton.icon(
                              style: OutlinedButton.styleFrom(
                                foregroundColor: context.colors.accentWork,
                                side: BorderSide(color: context.colors.accentWork.withAlpha(120)),
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                              ),
                              icon: const Icon(Icons.audio_file_outlined, size: 16),
                              label: const Text('음성 파일 선택'),
                              onPressed: _pickAudioFile,
                            ),
                          ],
                        ),
                      ],
                    ],
                  ),
                ),
              ],

              // 프로젝트 선택 (신규 등록 시)
              if (!isEdit) ...[
                Text('워크스페이스 (프로젝트) *', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                const SizedBox(height: 6),
                projectsAsync.when(
                  loading: () => SizedBox(
                    height: 48,
                    child: Center(
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: context.colors.accentWork)),
                  ),
                  error: (e, _) => Text('프로젝트 목록을 불러올 수 없습니다.',
                      style: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted)),
                  data: (projects) {
                    final validProjectPk = (_selectedProjectPk != null &&
                            projects.any((p) => p.pk == _selectedProjectPk))
                        ? _selectedProjectPk
                        : (projects.isNotEmpty ? projects.first.pk : null);

                    // 만약 _selectedProjectPk가 설정되지 않았고 유효한 프로젝트가 존재하면 상태 변수에 명시적으로 바인딩
                    if (_selectedProjectPk == null && validProjectPk != null) {
                      WidgetsBinding.instance.addPostFrameCallback((_) {
                        if (mounted && _selectedProjectPk == null) {
                          setState(() => _selectedProjectPk = validProjectPk);
                        }
                      });
                    }

                    return DropdownButtonFormField<int>(
                      value: validProjectPk,
                      isExpanded: true,
                      style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                      dropdownColor: context.colors.bgCard,
                      decoration: _inputDecoration('프로젝트 선택'),
                      items: projects
                          .map((p) => DropdownMenuItem(
                                value: p.pk,
                                child: Text(p.indentedLabel,
                                    overflow: TextOverflow.ellipsis),
                              ))
                          .toList(),
                      onChanged: (v) {
                        setState(() {
                          _selectedProjectPk = v;
                          _selectedCategoryPk = null;
                          _selectedAttendeePks = [];
                        });
                      },
                      validator: (v) => v == null ? '프로젝트를 선택해 주세요.' : null,
                    );
                  },
                ),
                const SizedBox(height: 14),
              ],

              // 회의 제목
              Text('회의 제목 *', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _titleController,
                style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? '제목을 입력해 주세요.' : null,
                decoration: _inputDecoration('회의 제목을 입력하세요'),
              ),
              const SizedBox(height: 14),

              // Row: 회의 일시 (50%) & 진행 상태 (50%)
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('회의 일시', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                        const SizedBox(height: 6),
                        TextField(
                          controller: _meetingDateController,
                          readOnly: true,
                          style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                          decoration:
                              _inputDecoration('YYYY-MM-DD HH:mm').copyWith(
                            suffixIcon: IconButton(
                              icon: Icon(Icons.access_time_rounded,
                                  size: 18, color: context.colors.textMuted),
                              onPressed: _selectDateTime,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('진행 상태', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                        const SizedBox(height: 6),
                        DropdownButtonFormField<String>(
                          value: _status,
                          isExpanded: true,
                          style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                          dropdownColor: context.colors.bgCard,
                          decoration: _inputDecoration(''),
                          items: const [
                            DropdownMenuItem(value: '1', child: Text('준비')),
                            DropdownMenuItem(value: '2', child: Text('종료')),
                            DropdownMenuItem(value: '3', child: Text('취소')),
                          ],
                          onChanged: (v) => setState(() => _status = v ?? '1'),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),

              // 회의 장소 (선택 입력)
              Text('회의 장소', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _locationController,
                style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                decoration: _inputDecoration('회의 장소 입력 (예: 본사 대회의실, 구청 미팅룸, Zoom)'),
              ),
              const SizedBox(height: 14),

              // 카테고리 헤더 (+ 추가 버튼 포함)
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('카테고리 *', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                  InkWell(
                    onTap: _showAddCategoryDialog,
                    borderRadius: BorderRadius.circular(4),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.add_circle_outline_rounded, size: 14, color: context.colors.accentWork),
                          const SizedBox(width: 4),
                          Text(
                            '카테고리 추가',
                            style: AppTextStyles.caption.copyWith(
                              color: context.colors.accentWork,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              ref.watch(meetingCategoriesProvider(_selectedProjectPk)).when(
                    data: (categories) {
                      final validCategoryPk = (_selectedCategoryPk != null &&
                              categories.any((c) => c.pk == _selectedCategoryPk))
                          ? _selectedCategoryPk
                          : (categories.isNotEmpty ? categories.first.pk : null);

                      // 만약 _selectedCategoryPk가 비어있고 카테고리가 존재하면 첫 번째 카테고리로 자동 지정
                      if (_selectedCategoryPk == null && validCategoryPk != null) {
                        WidgetsBinding.instance.addPostFrameCallback((_) {
                          if (mounted && _selectedCategoryPk == null) {
                            setState(() => _selectedCategoryPk = validCategoryPk);
                          }
                        });
                      }

                      return DropdownButtonFormField<int?>(
                        value: validCategoryPk,
                        isExpanded: true,
                        style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                        dropdownColor: context.colors.bgCard,
                        decoration: _inputDecoration('카테고리 선택'),
                        validator: (v) => v == null ? '카테고리를 선택해 주세요.' : null,
                        items: categories
                            .map((c) => DropdownMenuItem<int?>(
                                  value: c.pk,
                                  child: Text(c.name,
                                      overflow: TextOverflow.ellipsis),
                                ))
                            .toList(),
                        onChanged: (v) =>
                            setState(() => _selectedCategoryPk = v),
                      );
                    },
                    loading: () => DropdownButtonFormField<int?>(
                      items: const [],
                      onChanged: null,
                      decoration: _inputDecoration('카테고리 불러오는 중...'),
                    ),
                    error: (_, __) => DropdownButtonFormField<int?>(
                      items: const [],
                      onChanged: null,
                      decoration: _inputDecoration('카테고리 없음'),
                    ),
                  ),
              const SizedBox(height: 24),

              // ── 섹션 2: 참석자 ───────────────────────────────────────────
              _buildSectionHeader('참석자', Icons.people_outline_rounded),

              // 사내 멤버 참석자
              ref.watch(meetingMembersProvider(_selectedProjectPk)).when(
                    data: (members) {
                      final selectedUsers = members
                          .where((u) => _selectedAttendeePks.contains(u.pk))
                          .toList();

                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Text('참석자 (사내 멤버)', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
                              if (_selectedAttendeePks.isNotEmpty) ...[
                                const SizedBox(width: 6),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 6, vertical: 1),
                                  decoration: BoxDecoration(
                                    color: context.colors.accentWork.withAlpha(40),
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Text('${_selectedAttendeePks.length}',
                                      style: AppTextStyles.label.copyWith(
                                          color: context.colors.accentWork)),
                                ),
                              ],
                            ],
                          ),
                          const SizedBox(height: 6),
                          InkWell(
                            onTap: () => _openAttendeePicker(members),
                            borderRadius: BorderRadius.circular(6),
                            child: Container(
                              width: double.infinity,
                              constraints: const BoxConstraints(minHeight: 48),
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 12, vertical: 10),
                              decoration: BoxDecoration(
                                color: context.colors.bgCard,
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(
                                    color: context.colors.border, width: 0.8),
                              ),
                              child: Row(
                                children: [
                                  Expanded(
                                    child: selectedUsers.isEmpty
                                        ? Text('참석자를 선택하세요 (검색 가능)',
                                            style: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted))
                                        : Wrap(
                                            spacing: 6,
                                            runSpacing: 4,
                                            children: selectedUsers
                                                .map(
                                                  (u) => Container(
                                                    padding:
                                                        const EdgeInsets.symmetric(
                                                            horizontal: 8,
                                                            vertical: 3),
                                                    decoration: BoxDecoration(
                                                      color: context.colors
                                                          .accentWork
                                                          .withAlpha(30),
                                                      border: Border.all(
                                                        color: context.colors
                                                            .accentWork
                                                            .withAlpha(100),
                                                        width: 0.8,
                                                      ),
                                                      borderRadius:
                                                          BorderRadius.circular(
                                                              4),
                                                    ),
                                                    child: Text(
                                                      u.username,
                                                      style: AppTextStyles.label
                                                          .copyWith(
                                                        color:
                                                            context.colors.accentWork,
                                                      ),
                                                    ),
                                                  ),
                                                )
                                                .toList(),
                                          ),
                                  ),
                                  const SizedBox(width: 8),
                                  Icon(Icons.people_alt_outlined,
                                      size: 20, color: context.colors.textMuted),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 14),
                        ],
                      );
                    },
                    loading: () => const SizedBox.shrink(),
                    error: (_, __) => const SizedBox.shrink(),
                  ),

              // 기타 참석자 (외부인)
              Text('기타 참석자 (외부인/기관)', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _otherAttendeesController,
                style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                decoration: _inputDecoration(
                    '예: 시공사 김소장, 감리단 박팀장 (쉼표 구분)'),
              ),
              const SizedBox(height: 24),

              // ── 섹션 3: 회의 기록 ─────────────────────────────────────────
              _buildSectionHeader('회의 기록', Icons.edit_note_rounded),

              // 회의 의제
              Text('회의 의제 (Agenda)', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _agendaController,
                maxLines: 3,
                style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                decoration: _inputDecoration('회의 안건 및 의제를 입력하세요'),
              ),
              const SizedBox(height: 14),

              // 회의 내용
              Text('회의 내용 (Content)', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _contentController,
                maxLines: 5,
                style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                decoration: _inputDecoration('논의된 회의 상세 내용을 입력하세요'),
              ),
              const SizedBox(height: 14),

              // 주요 결정 사항
              Text('주요 결정 사항 (Decisions)', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _decisionsController,
                maxLines: 3,
                style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                decoration: _inputDecoration('회의에서 결정된 최종 사항을 입력하세요'),
              ),
              const SizedBox(height: 14),

              // 후속 조치 사항
              Text('후속 조치 사항 (Action Items)', style: AppTextStyles.titleSm.copyWith(color: context.colors.textPrimary)),
              const SizedBox(height: 6),
              TextFormField(
                controller: _actionItemsController,
                maxLines: 3,
                style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                decoration: _inputDecoration('회의 후 진행할 액션 아이템을 입력하세요'),
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title, IconData icon) {
    return Padding(
      padding: const EdgeInsets.only(top: 6, bottom: 14),
      child: Row(
        children: [
          Icon(icon, size: 18, color: context.colors.accentWork),
          const SizedBox(width: 8),
          Text(
            title,
            style: AppTextStyles.titleSm.copyWith(
              fontWeight: FontWeight.bold,
              color: context.colors.accentWork,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Divider(height: 1, color: context.colors.border),
          ),
        ],
      ),
    );
  }

  Future<void> _openAttendeePicker(List<SimpleUserModel> allMembers) async {
    final tempSelected = List<int>.from(_selectedAttendeePks);
    String searchQuery = '';

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: context.colors.bgCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            final filteredMembers = allMembers.where((u) {
              if (searchQuery.trim().isEmpty) return true;
              final query = searchQuery.toLowerCase();
              final username = u.username.toLowerCase();
              final email = (u.email ?? '').toLowerCase();
              return username.contains(query) || email.contains(query);
            }).toList();

            return DraggableScrollableSheet(
              expand: false,
              initialChildSize: 0.7,
              minChildSize: 0.4,
              maxChildSize: 0.9,
              builder: (context, scrollController) {
                return Column(
                  children: [
                    // 드래그 핸들바
                    Center(
                      child: Container(
                        margin: const EdgeInsets.symmetric(vertical: 8),
                        width: 36,
                        height: 4,
                        decoration: BoxDecoration(
                          color: context.colors.textDisabled.withAlpha(80),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    // 상단 헤더
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                      child: Row(
                        children: [
                          Text('참석자 선택', style: AppTextStyles.titleMd.copyWith(color: context.colors.textPrimary)),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                            decoration: BoxDecoration(
                              color: context.colors.accentWork.withAlpha(40),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text('${tempSelected.length}명',
                                style: AppTextStyles.label.copyWith(color: context.colors.accentWork)),
                          ),
                          const Spacer(),
                          if (tempSelected.isNotEmpty)
                            TextButton(
                              onPressed: () {
                                setModalState(() => tempSelected.clear());
                              },
                              child: Text('전체 해제', style: AppTextStyles.caption.copyWith(color: context.colors.accentApproval)),
                            ),
                          ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: context.colors.accentWork,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                            ),
                            onPressed: () => Navigator.pop(context),
                            child: const Text('완료', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                          ),
                        ],
                      ),
                    ),
                    // 검색창
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      child: TextField(
                        style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary),
                        decoration: InputDecoration(
                          hintText: '이름 또는 이메일 검색',
                          hintStyle: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted),
                          prefixIcon: Icon(Icons.search, size: 20, color: context.colors.textMuted),
                          filled: true,
                          fillColor: context.colors.bgPrimary,
                          contentPadding: const EdgeInsets.symmetric(vertical: 0, horizontal: 12),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                            borderSide: BorderSide(color: context.colors.border, width: 0.8),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                            borderSide: BorderSide(color: context.colors.border, width: 0.8),
                          ),
                        ),
                        onChanged: (v) {
                          setModalState(() => searchQuery = v);
                        },
                      ),
                    ),
                    Divider(height: 1, color: context.colors.border),
                    // 멤버 목록
                    Expanded(
                      child: filteredMembers.isEmpty
                          ? Center(
                              child: Text(
                                '검색 결과가 없습니다.',
                                style: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted),
                              ),
                            )
                          : ListView.separated(
                              controller: scrollController,
                              padding: const EdgeInsets.symmetric(vertical: 6),
                              itemCount: filteredMembers.length,
                              separatorBuilder: (_, __) => Divider(
                                height: 1,
                                color: context.colors.borderSubtle,
                                indent: 56,
                              ),
                              itemBuilder: (context, idx) {
                                final user = filteredMembers[idx];
                                final isSelected = tempSelected.contains(user.pk);

                                return CheckboxListTile(
                                  value: isSelected,
                                  activeColor: context.colors.accentWork,
                                  checkColor: Colors.white,
                                  title: Text(user.username, style: AppTextStyles.bodyMd.copyWith(color: context.colors.textPrimary)),
                                  subtitle: user.email != null && user.email!.isNotEmpty
                                      ? Text(user.email!, style: AppTextStyles.caption.copyWith(color: context.colors.textMuted))
                                      : null,
                                  secondary: CircleAvatar(
                                    radius: 16,
                                    backgroundColor: isSelected
                                        ? context.colors.accentWork.withAlpha(40)
                                        : context.colors.bgSurface,
                                    child: Text(
                                      user.username.isNotEmpty ? user.username.substring(0, 1) : '?',
                                      style: TextStyle(
                                        color: isSelected ? context.colors.accentWork : context.colors.textMuted,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 12,
                                      ),
                                    ),
                                  ),
                                  onChanged: (val) {
                                    setModalState(() {
                                      if (val == true) {
                                        tempSelected.add(user.pk);
                                      } else {
                                        tempSelected.remove(user.pk);
                                      }
                                    });
                                  },
                                );
                              },
                            ),
                    ),
                  ],
                );
              },
            );
          },
        );
      },
    );

    setState(() {
      _selectedAttendeePks = tempSelected;
    });
  }

  InputDecoration _inputDecoration(String hint) {
    return InputDecoration(
      hintText: hint,
      hintStyle: AppTextStyles.bodyMuted.copyWith(color: context.colors.textMuted),
      filled: true,
      fillColor: context.colors.bgCard,
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: BorderSide(color: context.colors.border, width: 0.8),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: BorderSide(color: context.colors.border, width: 0.8),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: BorderSide(color: context.colors.accentWork, width: 1.5),
      ),
    );
  }
}
