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

class LetterAttachmentModel {
  final int id;
  final String name;
  final String quantity;
  final String? file;
  final String? fileName;
  final int? fileSize;
  final String? created;

  const LetterAttachmentModel({
    required this.id,
    this.name = '',
    this.quantity = '1부',
    this.file,
    this.fileName,
    this.fileSize,
    this.created,
  });

  factory LetterAttachmentModel.fromJson(Map<String, dynamic> json) {
    return LetterAttachmentModel(
      id: _readId(json),
      name: json['name'] as String? ?? '',
      quantity: json['quantity'] as String? ?? '1부',
      file: json['file'] as String?,
      fileName: json['file_name'] as String?,
      fileSize: json['file_size'] as int?,
      created: json['created'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'quantity': quantity,
      if (file != null) 'file': file,
      if (fileName != null) 'file_name': fileName,
      if (fileSize != null) 'file_size': fileSize,
      if (created != null) 'created': created,
    };
  }
}

class OfficialLetterModel {
  final int id;
  final int? company;
  final String? companyName;
  final String documentNumber;
  final String title;
  final String recipientName;
  final String via;
  final String recipientReference;
  final String content;
  final String attachmentText;
  final String? issueDate;
  final String? effectiveIssueDate;
  final String disclosureType;
  final String? disclosureTypeDesc;
  final int? seal;
  final Map<String, dynamic>? sealDetail;
  final int? coSeal;
  final Map<String, dynamic>? coSealDetail;
  final String senderDisplayType;
  final String senderDutyTitle;
  final String senderName;
  final bool isSoloApproval;
  final String drafterName;
  final String drafterPosition;
  final String senderZipcode;
  final String senderAddress;
  final String recipientAddress;
  final String recipientContact;
  final String dispatchMethod;
  final String? dispatchMethodDesc;
  final String trackingNumber;
  final String? dispatchedAt;
  final String? pdfFile;
  final int? approvalDocument;
  final Map<String, dynamic>? approvalDocumentDetail;
  final String approvalStatus;
  final String? approvalStatusDesc;
  final SimpleUserModel? creator;
  final List<LetterAttachmentModel> attachments;
  final bool hasAttachments;
  final String? created;
  final String? updated;

  const OfficialLetterModel({
    required this.id,
    this.company,
    this.companyName,
    this.documentNumber = '',
    this.title = '',
    this.recipientName = '',
    this.via = '',
    this.recipientReference = '',
    this.content = '',
    this.attachmentText = '',
    this.issueDate,
    this.effectiveIssueDate,
    this.disclosureType = '1',
    this.disclosureTypeDesc,
    this.seal,
    this.sealDetail,
    this.coSeal,
    this.coSealDetail,
    this.senderDisplayType = 'company_only',
    this.senderDutyTitle = '',
    this.senderName = '',
    this.isSoloApproval = false,
    this.drafterName = '',
    this.drafterPosition = '',
    this.senderZipcode = '',
    this.senderAddress = '',
    this.recipientAddress = '',
    this.recipientContact = '',
    this.dispatchMethod = 'email',
    this.dispatchMethodDesc,
    this.trackingNumber = '',
    this.dispatchedAt,
    this.pdfFile,
    this.approvalDocument,
    this.approvalDocumentDetail,
    this.approvalStatus = 'none',
    this.approvalStatusDesc,
    this.creator,
    this.attachments = const [],
    this.hasAttachments = false,
    this.created,
    this.updated,
  });

  factory OfficialLetterModel.fromJson(Map<String, dynamic> json) {
    final attachmentsList = <LetterAttachmentModel>[];
    if (json['attachments'] is List) {
      for (final item in json['attachments'] as List) {
        if (item is Map<String, dynamic>) {
          attachmentsList.add(LetterAttachmentModel.fromJson(item));
        }
      }
    }

    SimpleUserModel? creatorUser;
    if (json['creator'] is Map<String, dynamic>) {
      creatorUser = SimpleUserModel.fromJson(json['creator'] as Map<String, dynamic>);
    }

    return OfficialLetterModel(
      id: _readId(json),
      company: _readCompanyId(json),
      companyName: _readCompanyName(json),
      documentNumber: json['document_number'] as String? ?? '',
      title: json['title'] as String? ?? '',
      recipientName: json['recipient_name'] as String? ?? '',
      via: json['via'] as String? ?? '',
      recipientReference: json['recipient_reference'] as String? ?? '',
      content: json['content'] as String? ?? '',
      attachmentText: json['attachment_text'] as String? ?? '',
      issueDate: json['issue_date'] as String?,
      effectiveIssueDate: json['effective_issue_date'] as String?,
      disclosureType: json['disclosure_type'] as String? ?? '1',
      disclosureTypeDesc: json['disclosure_type_desc'] as String?,
      seal: json['seal'] as int?,
      sealDetail: json['seal_detail'] is Map<String, dynamic> ? json['seal_detail'] as Map<String, dynamic> : null,
      coSeal: json['co_seal'] as int?,
      coSealDetail: json['co_seal_detail'] is Map<String, dynamic> ? json['co_seal_detail'] as Map<String, dynamic> : null,
      senderDisplayType: json['sender_display_type'] as String? ?? 'company_only',
      senderDutyTitle: json['sender_duty_title'] as String? ?? '',
      senderName: json['sender_name'] as String? ?? '',
      isSoloApproval: json['is_solo_approval'] as bool? ?? false,
      drafterName: json['drafter_name'] as String? ?? '',
      drafterPosition: json['drafter_position'] as String? ?? '',
      senderZipcode: json['sender_zipcode'] as String? ?? '',
      senderAddress: json['sender_address'] as String? ?? '',
      recipientAddress: json['recipient_address'] as String? ?? '',
      recipientContact: json['recipient_contact'] as String? ?? '',
      dispatchMethod: json['dispatch_method'] as String? ?? 'email',
      dispatchMethodDesc: json['dispatch_method_desc'] as String?,
      trackingNumber: json['tracking_number'] as String? ?? '',
      dispatchedAt: json['dispatched_at'] as String?,
      pdfFile: json['pdf_file'] as String?,
      approvalDocument: json['approval_document'] as int?,
      approvalDocumentDetail: json['approval_document_detail'] is Map<String, dynamic>
          ? json['approval_document_detail'] as Map<String, dynamic>
          : null,
      approvalStatus: json['approval_status'] as String? ?? 'none',
      approvalStatusDesc: json['approval_status_desc'] as String?,
      creator: creatorUser,
      attachments: attachmentsList,
      hasAttachments: json['has_attachments'] as bool? ?? attachmentsList.isNotEmpty,
      created: json['created'] as String?,
      updated: json['updated'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      if (company != null) 'company': company,
      'document_number': documentNumber,
      'title': title,
      'recipient_name': recipientName,
      'via': via,
      'recipient_reference': recipientReference,
      'content': content,
      'attachment_text': attachmentText,
      if (issueDate != null) 'issue_date': issueDate,
      if (effectiveIssueDate != null) 'effective_issue_date': effectiveIssueDate,
      'disclosure_type': disclosureType,
      if (seal != null) 'seal': seal,
      if (coSeal != null) 'co_seal': coSeal,
      'sender_display_type': senderDisplayType,
      'sender_duty_title': senderDutyTitle,
      'sender_name': senderName,
      'is_solo_approval': isSoloApproval,
      'drafter_name': drafterName,
      'drafter_position': drafterPosition,
      'sender_zipcode': senderZipcode,
      'sender_address': senderAddress,
      'recipient_address': recipientAddress,
      'recipient_contact': recipientContact,
      'dispatch_method': dispatchMethod,
      'tracking_number': trackingNumber,
      if (dispatchedAt != null) 'dispatched_at': dispatchedAt,
      if (pdfFile != null) 'pdf_file': pdfFile,
      if (approvalDocument != null) 'approval_document': approvalDocument,
      'approval_status': approvalStatus,
      if (creator != null) 'creator': creator!.toJson(),
      'attachments': attachments.map((a) => a.toJson()).toList(),
      'has_attachments': hasAttachments,
    };
  }

  OfficialLetterModel copyWith({
    int? id,
    int? company,
    String? companyName,
    String? documentNumber,
    String? title,
    String? recipientName,
    String? via,
    String? recipientReference,
    String? content,
    String? attachmentText,
    String? issueDate,
    String? effectiveIssueDate,
    String? disclosureType,
    String? disclosureTypeDesc,
    int? seal,
    Map<String, dynamic>? sealDetail,
    int? coSeal,
    Map<String, dynamic>? coSealDetail,
    String? senderDisplayType,
    String? senderDutyTitle,
    String? senderName,
    bool? isSoloApproval,
    String? drafterName,
    String? drafterPosition,
    String? senderZipcode,
    String? senderAddress,
    String? recipientAddress,
    String? recipientContact,
    String? dispatchMethod,
    String? dispatchMethodDesc,
    String? trackingNumber,
    String? dispatchedAt,
    String? pdfFile,
    int? approvalDocument,
    Map<String, dynamic>? approvalDocumentDetail,
    String? approvalStatus,
    String? approvalStatusDesc,
    SimpleUserModel? creator,
    List<LetterAttachmentModel>? attachments,
    bool? hasAttachments,
    String? created,
    String? updated,
  }) {
    return OfficialLetterModel(
      id: id ?? this.id,
      company: company ?? this.company,
      companyName: companyName ?? this.companyName,
      documentNumber: documentNumber ?? this.documentNumber,
      title: title ?? this.title,
      recipientName: recipientName ?? this.recipientName,
      via: via ?? this.via,
      recipientReference: recipientReference ?? this.recipientReference,
      content: content ?? this.content,
      attachmentText: attachmentText ?? this.attachmentText,
      issueDate: issueDate ?? this.issueDate,
      effectiveIssueDate: effectiveIssueDate ?? this.effectiveIssueDate,
      disclosureType: disclosureType ?? this.disclosureType,
      disclosureTypeDesc: disclosureTypeDesc ?? this.disclosureTypeDesc,
      seal: seal ?? this.seal,
      sealDetail: sealDetail ?? this.sealDetail,
      coSeal: coSeal ?? this.coSeal,
      coSealDetail: coSealDetail ?? this.coSealDetail,
      senderDisplayType: senderDisplayType ?? this.senderDisplayType,
      senderDutyTitle: senderDutyTitle ?? this.senderDutyTitle,
      senderName: senderName ?? this.senderName,
      isSoloApproval: isSoloApproval ?? this.isSoloApproval,
      drafterName: drafterName ?? this.drafterName,
      drafterPosition: drafterPosition ?? this.drafterPosition,
      senderZipcode: senderZipcode ?? this.senderZipcode,
      senderAddress: senderAddress ?? this.senderAddress,
      recipientAddress: recipientAddress ?? this.recipientAddress,
      recipientContact: recipientContact ?? this.recipientContact,
      dispatchMethod: dispatchMethod ?? this.dispatchMethod,
      dispatchMethodDesc: dispatchMethodDesc ?? this.dispatchMethodDesc,
      trackingNumber: trackingNumber ?? this.trackingNumber,
      dispatchedAt: dispatchedAt ?? this.dispatchedAt,
      pdfFile: pdfFile ?? this.pdfFile,
      approvalDocument: approvalDocument ?? this.approvalDocument,
      approvalDocumentDetail: approvalDocumentDetail ?? this.approvalDocumentDetail,
      approvalStatus: approvalStatus ?? this.approvalStatus,
      approvalStatusDesc: approvalStatusDesc ?? this.approvalStatusDesc,
      creator: creator ?? this.creator,
      attachments: attachments ?? this.attachments,
      hasAttachments: hasAttachments ?? this.hasAttachments,
      created: created ?? this.created,
      updated: updated ?? this.updated,
    );
  }
}

class OfficialLetterListResponseModel {
  final int count;
  final String? next;
  final String? previous;
  final List<OfficialLetterModel> results;

  const OfficialLetterListResponseModel({
    required this.count,
    this.next,
    this.previous,
    required this.results,
  });

  factory OfficialLetterListResponseModel.fromJson(Map<String, dynamic> json) {
    final list = <OfficialLetterModel>[];
    if (json['results'] is List) {
      for (final item in json['results'] as List) {
        if (item is Map<String, dynamic>) {
          list.add(OfficialLetterModel.fromJson(item));
        }
      }
    }
    return OfficialLetterListResponseModel(
      count: json['count'] as int? ?? 0,
      next: json['next'] as String?,
      previous: json['previous'] as String?,
      results: list,
    );
  }
}
