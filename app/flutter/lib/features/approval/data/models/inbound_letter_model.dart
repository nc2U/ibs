import '../../../../core/models/common_models.dart';

int _readId(Map<String, dynamic> json) {
  final val = json['id'] ?? json['pk'];
  if (val is num) return val.toInt();
  if (val is String) return int.tryParse(val) ?? 0;
  return 0;
}

int? _readCompanyId(Map<String, dynamic> json) {
  final val = json['company'];
  if (val is num) return val.toInt();
  if (val is Map) {
    final subId = val['id'] ?? val['pk'];
    if (subId is num) return subId.toInt();
  }
  final valId = json['company_id'];
  if (valId is num) return valId.toInt();
  return null;
}

String? _readCompanyName(Map<String, dynamic> json) {
  if (json['company_name'] != null) return json['company_name'].toString();
  if (json['company'] is Map && json['company']['name'] != null) {
    return json['company']['name'].toString();
  }
  return null;
}

class InboundLetterAttachmentModel {
  final int id;
  final int? letter;
  final String? file;
  final String name;
  final String? fileName;
  final int? fileSize;
  final String quantity;
  final int? ordering;
  final String? created;

  const InboundLetterAttachmentModel({
    required this.id,
    this.letter,
    this.file,
    this.name = '',
    this.fileName,
    this.fileSize,
    this.quantity = '1부',
    this.ordering,
    this.created,
  });

  factory InboundLetterAttachmentModel.fromJson(Map<String, dynamic> json) {
    return InboundLetterAttachmentModel(
      id: _readId(json),
      letter: json['letter'] is num ? (json['letter'] as num).toInt() : null,
      file: json['file'] as String?,
      name: json['name'] as String? ?? '',
      fileName: json['file_name'] as String?,
      fileSize: json['file_size'] as int?,
      quantity: json['quantity'] as String? ?? '1부',
      ordering: json['ordering'] as int?,
      created: json['created'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      if (letter != null) 'letter': letter,
      if (file != null) 'file': file,
      'name': name,
      if (fileName != null) 'file_name': fileName,
      if (fileSize != null) 'file_size': fileSize,
      'quantity': quantity,
      if (ordering != null) 'ordering': ordering,
      if (created != null) 'created': created,
    };
  }
}

class InboundLetterModel {
  final int id;
  final int? company;
  final String? companyName;
  final String receiptNumber;
  final String documentNumber;
  final String senderName;
  final String senderContact;
  final String receivedDate;
  final String? replyDueDate;
  final int? dDay;
  final String title;
  final String content;
  final String? scanFile;
  final int? recipientDept;
  final String? recipientDeptName;
  final int? recipientManager;
  final String? recipientManagerName;
  final String status;
  final String? statusDesc;
  final bool hasScan;
  final bool hasAttachments;
  final int? approvalDocument;
  final Map<String, dynamic>? approvalDocumentDetail;
  final List<InboundLetterAttachmentModel> attachments;
  final List<Map<String, dynamic>> replyLetters;
  final SimpleUserModel? creator;
  final SimpleUserModel? updator;
  final String? created;
  final String? updated;
  final int? prevPk;
  final int? nextPk;

  const InboundLetterModel({
    required this.id,
    this.company,
    this.companyName,
    this.receiptNumber = '',
    this.documentNumber = '',
    this.senderName = '',
    this.senderContact = '',
    this.receivedDate = '',
    this.replyDueDate,
    this.dDay,
    this.title = '',
    this.content = '',
    this.scanFile,
    this.recipientDept,
    this.recipientDeptName,
    this.recipientManager,
    this.recipientManagerName,
    this.status = 'received',
    this.statusDesc,
    this.hasScan = false,
    this.hasAttachments = false,
    this.approvalDocument,
    this.approvalDocumentDetail,
    this.attachments = const [],
    this.replyLetters = const [],
    this.creator,
    this.updator,
    this.created,
    this.updated,
    this.prevPk,
    this.nextPk,
  });

  factory InboundLetterModel.fromJson(Map<String, dynamic> json) {
    // 첨부파일 파싱
    final rawAttachments = json['attachments'];
    final List<InboundLetterAttachmentModel> attachmentsList = [];
    if (rawAttachments is List) {
      for (final item in rawAttachments) {
        if (item is Map<String, dynamic>) {
          attachmentsList.add(InboundLetterAttachmentModel.fromJson(item));
        }
      }
    }

    // 회신 공문 목록 파싱
    final rawReply = json['reply_letters'];
    final List<Map<String, dynamic>> replyList = [];
    if (rawReply is List) {
      for (final item in rawReply) {
        if (item is Map<String, dynamic>) {
          replyList.add(item);
        }
      }
    }

    final hasScanVal = json['has_scan'] == true ||
        (json['scan_file'] != null && json['scan_file'].toString().isNotEmpty);
    final hasAttachmentsVal =
        json['has_attachments'] == true || attachmentsList.isNotEmpty;

    return InboundLetterModel(
      id: _readId(json),
      company: _readCompanyId(json),
      companyName: _readCompanyName(json),
      receiptNumber: json['receipt_number'] as String? ?? '',
      documentNumber: json['document_number'] as String? ?? '',
      senderName: json['sender_name'] as String? ?? '',
      senderContact: json['sender_contact'] as String? ?? '',
      receivedDate: json['received_date'] as String? ?? '',
      replyDueDate: json['reply_due_date'] as String?,
      dDay: json['d_day'] is num ? (json['d_day'] as num).toInt() : null,
      title: json['title'] as String? ?? '',
      content: json['content'] as String? ?? '',
      scanFile: json['scan_file'] as String?,
      recipientDept: json['recipient_dept'] is num
          ? (json['recipient_dept'] as num).toInt()
          : null,
      recipientDeptName: json['recipient_dept_name'] as String?,
      recipientManager: json['recipient_manager'] is num
          ? (json['recipient_manager'] as num).toInt()
          : null,
      recipientManagerName: json['recipient_manager_name'] as String?,
      status: json['status'] as String? ?? 'received',
      statusDesc: json['status_desc'] as String? ??
          _defaultStatusDesc(json['status'] as String? ?? 'received'),
      hasScan: hasScanVal,
      hasAttachments: hasAttachmentsVal,
      approvalDocument: json['approval_document'] is num
          ? (json['approval_document'] as num).toInt()
          : null,
      approvalDocumentDetail: json['approval_document_detail'] is Map<String, dynamic>
          ? json['approval_document_detail'] as Map<String, dynamic>
          : null,
      attachments: attachmentsList,
      replyLetters: replyList,
      creator: json['creator'] != null && json['creator'] is Map<String, dynamic>
          ? SimpleUserModel.fromJson(json['creator'] as Map<String, dynamic>)
          : null,
      updator: json['updator'] != null && json['updator'] is Map<String, dynamic>
          ? SimpleUserModel.fromJson(json['updator'] as Map<String, dynamic>)
          : null,
      created: json['created'] as String?,
      updated: json['updated'] as String?,
      prevPk: json['prev_pk'] is num ? (json['prev_pk'] as num).toInt() : null,
      nextPk: json['next_pk'] is num ? (json['next_pk'] as num).toInt() : null,
    );
  }

  static String _defaultStatusDesc(String status) {
    switch (status) {
      case 'received':
        return '접수';
      case 'in_progress':
        return '처리중';
      case 'replied':
        return '회신완료';
      case 'closed':
        return '종결';
      default:
        return '접수';
    }
  }

  /// D-Day 포맷 텍스트 (null이면 없음, 음수면 기한초과, 0이면 오늘마감, 양수면 잔여일)
  String? get dDayFormatted {
    if (dDay == null) return null;
    if (dDay! < 0) return '기한경과 (D+${-dDay!})';
    if (dDay == 0) return 'D-Day (오늘)';
    return 'D-$dDay';
  }
}

class InboundLetterListResponseModel {
  final int count;
  final String? next;
  final String? previous;
  final List<InboundLetterModel> results;

  const InboundLetterListResponseModel({
    required this.count,
    this.next,
    this.previous,
    required this.results,
  });

  factory InboundLetterListResponseModel.fromJson(Map<String, dynamic> json) {
    final rawResults = json['results'];
    final List<InboundLetterModel> items = [];
    if (rawResults is List) {
      for (final item in rawResults) {
        if (item is Map<String, dynamic>) {
          items.add(InboundLetterModel.fromJson(item));
        }
      }
    }
    return InboundLetterListResponseModel(
      count: json['count'] as int? ?? items.length,
      next: json['next'] as String?,
      previous: json['previous'] as String?,
      results: items,
    );
  }
}
