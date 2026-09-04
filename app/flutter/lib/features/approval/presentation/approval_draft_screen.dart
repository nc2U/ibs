import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/theme/app_colors_extension.dart';
import '../../../../core/widgets/loading_shimmer.dart';
import '../data/approval_repository.dart';
import '../data/models/approval_model.dart';
import '../providers/approval_providers.dart';

class ApprovalDraftScreen extends ConsumerStatefulWidget {
  final ApprovalDocumentModel? editDoc;

  const ApprovalDraftScreen({super.key, this.editDoc});

  @override
  ConsumerState<ApprovalDraftScreen> createState() => _ApprovalDraftScreenState();
}

class _ApprovalDraftScreenState extends ConsumerState<ApprovalDraftScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();

  // 폼 선택 상태
  StaffAssignmentItemModel? _selectedAssignment;
  DocumentTypeModel? _selectedDocType;
  final List<String> _attachedFilePaths = [];
  bool _isSubmitting = false;

  // ── 양식별 컨트롤러 ─────────────────────────────────────────────
  // 휴가신청서
  String _leaveType = '연차';
  DateTime? _startDate = DateTime.now();
  DateTime? _endDate = DateTime.now();
  final _leaveDaysController = TextEditingController(text: '1.0');
  final _leaveReasonController = TextEditingController();
  final _substituteWorkerController = TextEditingController();
  final _emergencyContactController = TextEditingController();

  // 지출결의서 / 구매품의서
  final _amountController = TextEditingController();
  final _purposeController = TextEditingController();
  final _vendorController = TextEditingController();
  final _generalContentController = TextEditingController();

  // 공문 발신 (OFFICIAL_LETTER)
  final _receiverController = TextEditingController();
  final _referToController = TextEditingController();
  final _senderNameController = TextEditingController();
  final _docNumberExtController = TextEditingController();
  final _letterSubjectController = TextEditingController();
  final _letterBodyController = TextEditingController();
  final _enclosedFilesController = TextEditingController();
  String _sendMethod = 'EMAIL';
  DateTime? _sendDueDate = DateTime.now();
  String _sealType = 'CORP_SEAL';
  final _sealCountController = TextEditingController(text: '1');

  // 일반품의 (GENERAL / BIZ_APPROVAL)
  final _scheduleController = TextEditingController();
  String _budgetAccount = 'GENERAL_EXPENSE';
  final _expectedEffectController = TextEditingController();
  final _noteController = TextEditingController();

  // 출장신청서 (BUSINESS_TRIP / TRIP)
  String _tripType = 'DOMESTIC';
  final _destinationController = TextEditingController();
  final _companionController = TextEditingController();
  String _transportation = 'CORP_CAR';
  final _transportCostController = TextEditingController();
  final _lodgingCostController = TextEditingController();
  final _dailyAllowanceController = TextEditingController();
  final _otherCostController = TextEditingController();
  final _itineraryController = TextEditingController();

  // 연장/휴일근무 (OVERTIME / OVERTIME_WORK)
  String _workType = 'OVERTIME';
  DateTime? _workDate = DateTime.now();
  final _startTimeController = TextEditingController(text: '18:30');
  final _endTimeController = TextEditingController(text: '21:30');
  final _breakHoursController = TextEditingController(text: '0');
  final _totalHoursController = TextEditingController(text: '3.0');
  String _compensationType = 'ALLOWANCE';
  final _coWorkersController = TextEditingController();

  // 인사발령 (HR_APPOINTMENT / APPOINTMENT)
  String _appointmentType = 'PROMOTION';
  DateTime? _effectiveDate = DateTime.now();
  final _targetNameController = TextEditingController();
  final _currentDeptController = TextEditingController();
  final _currentPositionController = TextEditingController();
  final _newDeptController = TextEditingController();
  final _newPositionController = TextEditingController();
  final _typeDescController = TextEditingController(text: '승진/전보');

  // 인사 관련 신청 (HR_REQUEST / CERT_REQUEST)
  String _hrRequestType = 'CERTIFICATE';
  String _certType = 'EMPLOYMENT';
  String _certLanguage = 'KOREAN';
  final _certCountController = TextEditingController(text: '1');
  final _submitToController = TextEditingController();
  final _usagePurposeController = TextEditingController();
  String _receiveMethod = 'PDF_EMAIL';
  bool _includeResidentNum = false;
  String _eventType = 'MARRIAGE_SELF';
  DateTime? _eventDate = DateTime.now();
  final _eventPlaceController = TextEditingController();
  final _supportItemsController = TextEditingController();

  // 구매품의서 (PURCHASE_ORDER / PURCHASE)
  final _deliveryLocationController = TextEditingController();
  DateTime? _deliveryDueDate = DateTime.now().add(const Duration(days: 7));

  // 지출결의서 (EXPENSE_REPORT / EXPENSE)
  String _expenseType = 'CARD';
  DateTime? _paymentDueDate = DateTime.now();
  final _bankNameController = TextEditingController();
  final _accountNumberController = TextEditingController();
  final _accountHolderController = TextEditingController();

  // 경비정산서 (EXPENSE_SETTLEMENT / SETTLEMENT)
  String _settlementType = 'CORP_CARD';
  final _targetMonthController = TextEditingController(text: '${DateTime.now().year}-${DateTime.now().month.toString().padLeft(2, '0')}');
  final _cardNumberController = TextEditingController();

  // 선급금 / 가지급금 (ADVANCE / ADVANCE_PAY / ADVANCE_REQUEST)
  String _advanceType = 'ADVANCE_PAY';
  String _receiverType = 'EMPLOYEE';
  DateTime? _settlementDueDate = DateTime.now().add(const Duration(days: 14));
  bool _settlementPromise = true;

  // 계약 체결 품의서 (CONTRACT / CONTRACT_APPROVAL / CONTRACT_PROPOSAL)
  String _contractType = 'SERVICE';
  String _contractKind = 'NEW';
  String _vatType = 'EXCLUDED';
  final _contractNameController = TextEditingController();
  final _contractorCeoController = TextEditingController();
  final _contractorRegNumberController = TextEditingController();
  final _contractorContactController = TextEditingController();
  final _paymentTermsController = TextEditingController();
  final _warrantyTermsController = TextEditingController();
  final _specialTermsController = TextEditingController();

  // 계약 변경 / 해지 (CONTRACT_CHANGE / CONTRACT_TERMINATION / CONTRACT_AMENDMENT)
  String _contractChangeType = 'COMPREHENSIVE';
  final _origContractNameController = TextEditingController();
  final _origContractNoController = TextEditingController();
  DateTime? _origContractDate = DateTime.now();
  DateTime? _origEndDate = DateTime.now().add(const Duration(days: 180));
  final _origAmountController = TextEditingController(text: '0');
  final _changeAmountController = TextEditingController(text: '0');
  final _periodChangeDescController = TextEditingController();
  DateTime? _terminationDate = DateTime.now();
  final _settlementAmountController = TextEditingController(text: '0');
  final _penaltyTermsController = TextEditingController();
  final _subsequentPlanController = TextEditingController();

  // 법무 검토 (LEGAL_REVIEW / LEGAL_CONSULTATION / LEGAL_ADVICE)
  String _legalReviewType = 'CONTRACT_REVIEW';
  String _legalUrgency = 'NORMAL';
  DateTime? _reviewDueDate = DateTime.now().add(const Duration(days: 5));
  final _keyIssuesController = TextEditingController();

  // 사업검토 (BUSINESS_REVIEW / PROJECT_FEASIBILITY / BIZ_FEASIBILITY / PROJECT_REVIEW / INVESTMENT_REVIEW)
  String _bizType = 'DEV_SELF';
  final _locationController = TextEditingController();
  final _buildingScaleController = TextEditingController();
  final _landAreaController = TextEditingController();
  final _grossFloorAreaController = TextEditingController();
  final _totalRevenueController = TextEditingController(text: '0');
  final _totalCostController = TextEditingController(text: '0');
  final _requiredEquityController = TextEditingController(text: '0');
  final _pfLoanAmountController = TextEditingController(text: '0');
  DateTime? _landSecureDate;
  DateTime? _approvalTargetDate;
  DateTime? _completionDate;
  final _marketAnalysisController = TextEditingController();
  final _riskFactorsController = TextEditingController();

  // 사업추진 승인 (BUSINESS_APPROVAL / PROJECT_APPROVAL / DEV_APPROVAL / INVESTMENT_APPROVAL)
  String _bizApprovalType = 'NEW_LAUNCH';
  final _bizScaleSummaryController = TextEditingController();
  final _requestedAmountController = TextEditingController(text: '0');
  final _totalProjectCostController = TextEditingController(text: '0');
  final _totalExpectedRevenueController = TextEditingController(text: '0');
  final _budgetUsagePlanController = TextEditingController();
  final _resolutionMattersController = TextEditingController();
  final _pmLeadController = TextEditingController();
  final _targetScheduleController = TextEditingController();
  final _expectedEffectsController = TextEditingController();

  // 프로젝트 주요 의사결정 (PROJECT_DECISION / PROJECT_KEY_DECISION / DECISION_PROPOSAL / KEY_DECISION)
  String _projectDecisionType = 'DESIGN_SPEC';
  String _decisionUrgency = 'NORMAL';
  DateTime? _decisionDueDate = DateTime.now().add(const Duration(days: 7));
  final _option1Controller = TextEditingController();
  final _option2Controller = TextEditingController();
  final _option3Controller = TextEditingController();
  final _actionPlanController = TextEditingController();

  // 실시간 결재선 미리보기 상태
  List<RoutePreviewStepModel> _previewSteps = [];
  bool _isPreviewLoading = false;

  @override
  void initState() {
    super.initState();
    if (widget.editDoc != null) {
      _initFromEditDoc(widget.editDoc!);
    }
  }

  void _initFromEditDoc(ApprovalDocumentModel doc) {
    _titleController.text = doc.title;
    final c = doc.content;

    // 1. 휴가
    if (c['leave_type'] != null) _leaveType = c['leave_type'].toString();
    if (c['start_date'] != null) _startDate = DateTime.tryParse(c['start_date'].toString());
    if (c['end_date'] != null) _endDate = DateTime.tryParse(c['end_date'].toString());
    if (c['days_count'] != null) _leaveDaysController.text = c['days_count'].toString();
    if (c['reason'] != null) _leaveReasonController.text = c['reason'].toString();
    if (c['substitute_worker'] != null) _substituteWorkerController.text = c['substitute_worker'].toString();
    if (c['emergency_contact'] != null) _emergencyContactController.text = c['emergency_contact'].toString();

    // 2. 지출/일반품의
    final amt = c['budget'] ?? c['amount'] ?? c['requested_amount'] ?? c['cost'] ?? c['total_cost'];
    if (amt != null) _amountController.text = amt.toString();
    if (c['purpose'] != null) _purposeController.text = c['purpose'].toString();
    if (c['content'] != null || c['body'] != null) _generalContentController.text = (c['content'] ?? c['body']).toString();
    if (c['schedule'] != null) _scheduleController.text = c['schedule'].toString();
    if (c['budget_account'] != null) _budgetAccount = c['budget_account'].toString();
    if (c['expected_effect'] != null) _expectedEffectController.text = c['expected_effect'].toString();
    if (c['note'] != null) _noteController.text = c['note'].toString();

    // 3. 공문
    if (c['receiver'] != null) _receiverController.text = c['receiver'].toString();
    if (c['refer_to'] != null) _referToController.text = c['refer_to'].toString();
    if (c['sender_name'] != null) _senderNameController.text = c['sender_name'].toString();
    if (c['doc_number_external'] != null) _docNumberExtController.text = c['doc_number_external'].toString();
    if (c['letter_subject'] != null) _letterSubjectController.text = c['letter_subject'].toString();
    if (c['letter_body'] != null) _letterBodyController.text = c['letter_body'].toString();
    if (c['enclosed_files_desc'] != null) _enclosedFilesController.text = c['enclosed_files_desc'].toString();
    if (c['send_method'] != null) _sendMethod = c['send_method'].toString();
    if (c['send_due_date'] != null) _sendDueDate = DateTime.tryParse(c['send_due_date'].toString());
    if (c['seal_type'] != null) _sealType = c['seal_type'].toString();
    if (c['seal_count'] != null) _sealCountController.text = c['seal_count'].toString();

    // 4. 출장
    if (c['trip_type'] != null) _tripType = c['trip_type'].toString();
    if (c['destination'] != null) _destinationController.text = c['destination'].toString();
    if (c['companion'] != null) _companionController.text = c['companion'].toString();
    if (c['transportation'] != null) _transportation = c['transportation'].toString();
    if (c['transport_cost'] != null) _transportCostController.text = c['transport_cost'].toString();
    if (c['lodging_cost'] != null) _lodgingCostController.text = c['lodging_cost'].toString();
    if (c['daily_allowance'] != null) _dailyAllowanceController.text = c['daily_allowance'].toString();
    if (c['other_cost'] != null) _otherCostController.text = c['other_cost'].toString();
    if (c['itinerary'] != null) _itineraryController.text = c['itinerary'].toString();

    // 5. 연장근무
    if (c['work_type'] != null) _workType = c['work_type'].toString();
    if (c['work_date'] != null) _workDate = DateTime.tryParse(c['work_date'].toString());
    if (c['start_time'] != null) _startTimeController.text = c['start_time'].toString();
    if (c['end_time'] != null) _endTimeController.text = c['end_time'].toString();
    if (c['break_hours'] != null) _breakHoursController.text = c['break_hours'].toString();
    if (c['total_hours'] != null) _totalHoursController.text = c['total_hours'].toString();
    if (c['compensation_type'] != null) _compensationType = c['compensation_type'].toString();
    if (c['co_workers'] != null) _coWorkersController.text = c['co_workers'].toString();

    // 6. 인사발령
    if (c['appointment_type'] != null) _appointmentType = c['appointment_type'].toString();
    if (c['effective_date'] != null) _effectiveDate = DateTime.tryParse(c['effective_date'].toString());
    if (c['targets'] is List && (c['targets'] as List).isNotEmpty) {
      final t = (c['targets'] as List).first as Map<String, dynamic>;
      if (t['name'] != null) _targetNameController.text = t['name'].toString();
      if (t['current_dept'] != null) _currentDeptController.text = t['current_dept'].toString();
      if (t['current_position'] != null) _currentPositionController.text = t['current_position'].toString();
      if (t['new_dept'] != null) _newDeptController.text = t['new_dept'].toString();
      if (t['new_position'] != null) _newPositionController.text = t['new_position'].toString();
      if (t['type_desc'] != null) _typeDescController.text = t['type_desc'].toString();
    }

    // 7. 인사 관련 신청
    if (c['request_type'] != null) _hrRequestType = c['request_type'].toString();
    if (c['cert_type'] != null) _certType = c['cert_type'].toString();
    if (c['cert_language'] != null) _certLanguage = c['cert_language'].toString();
    if (c['cert_count'] != null) _certCountController.text = c['cert_count'].toString();
    if (c['submit_to'] != null) _submitToController.text = c['submit_to'].toString();
    if (c['usage_purpose'] != null) _usagePurposeController.text = c['usage_purpose'].toString();
    if (c['include_resident_num'] != null) _includeResidentNum = c['include_resident_num'] == true;
    if (c['event_type'] != null) _eventType = c['event_type'].toString();
    if (c['event_date'] != null) _eventDate = DateTime.tryParse(c['event_date'].toString());
    if (c['event_place'] != null) _eventPlaceController.text = c['event_place'].toString();
    if (c['support_items'] != null) _supportItemsController.text = c['support_items'].toString();

    // 8. 구매/지출
    if (c['vendor'] != null) _vendorController.text = c['vendor'].toString();
    if (c['delivery_location'] != null) _deliveryLocationController.text = c['delivery_location'].toString();
    if (c['delivery_due_date'] != null) _deliveryDueDate = DateTime.tryParse(c['delivery_due_date'].toString());
    if (c['expense_type'] != null) _expenseType = c['expense_type'].toString();
    if (c['payment_due_date'] != null) _paymentDueDate = DateTime.tryParse(c['payment_due_date'].toString());
    if (c['bank_name'] != null) _bankNameController.text = c['bank_name'].toString();
    if (c['account_number'] != null) _accountNumberController.text = c['account_number'].toString();
    if (c['account_holder'] != null) _accountHolderController.text = c['account_holder'].toString();

    // 9. 경비 정산
    if (c['settlement_type'] != null) _settlementType = c['settlement_type'].toString();
    if (c['target_month'] != null) _targetMonthController.text = c['target_month'].toString();
    if (c['card_number'] != null) _cardNumberController.text = c['card_number'].toString();

    // 10. 선급금 / 가지급금
    if (c['advance_type'] != null) _advanceType = c['advance_type'].toString();
    if (c['receiver_type'] != null) _receiverType = c['receiver_type'].toString();
    if (c['settlement_due_date'] != null) _settlementDueDate = DateTime.tryParse(c['settlement_due_date'].toString());
    if (c['settlement_promise'] != null) _settlementPromise = c['settlement_promise'] == true;

    // 11. 계약 체결
    if (c['contract_type'] != null) _contractType = c['contract_type'].toString();
    if (c['contract_kind'] != null) _contractKind = c['contract_kind'].toString();
    if (c['contract_name'] != null) _contractNameController.text = c['contract_name'].toString();
    if (c['contractor_name'] != null) _vendorController.text = c['contractor_name'].toString();
    if (c['contractor_ceo'] != null) _contractorCeoController.text = c['contractor_ceo'].toString();
    if (c['contractor_reg_number'] != null) _contractorRegNumberController.text = c['contractor_reg_number'].toString();
    if (c['contractor_contact'] != null) _contractorContactController.text = c['contractor_contact'].toString();
    if (c['vat_type'] != null) _vatType = c['vat_type'].toString();
    if (c['contract_start_date'] != null) _startDate = DateTime.tryParse(c['contract_start_date'].toString());
    if (c['contract_end_date'] != null) _endDate = DateTime.tryParse(c['contract_end_date'].toString());
    if (c['payment_terms'] != null) _paymentTermsController.text = c['payment_terms'].toString();
    if (c['warranty_terms'] != null) _warrantyTermsController.text = c['warranty_terms'].toString();
    if (c['special_terms'] != null) _specialTermsController.text = c['special_terms'].toString();

    // 12. 계약 변경 / 해지
    if (c['change_type'] != null) _contractChangeType = c['change_type'].toString();
    if (c['original_contract_name'] != null) _origContractNameController.text = c['original_contract_name'].toString();
    if (c['original_contract_no'] != null) _origContractNoController.text = c['original_contract_no'].toString();
    if (c['original_contract_date'] != null) _origContractDate = DateTime.tryParse(c['original_contract_date'].toString());
    if (c['original_end_date'] != null) _origEndDate = DateTime.tryParse(c['original_end_date'].toString());
    if (c['original_amount'] != null) _origAmountController.text = c['original_amount'].toString();
    if (c['change_amount'] != null) _changeAmountController.text = c['change_amount'].toString();
    if (c['period_change_desc'] != null) _periodChangeDescController.text = c['period_change_desc'].toString();
    if (c['termination_date'] != null) _terminationDate = DateTime.tryParse(c['termination_date'].toString());
    if (c['settlement_amount'] != null) _settlementAmountController.text = c['settlement_amount'].toString();
    if (c['penalty_terms'] != null) _penaltyTermsController.text = c['penalty_terms'].toString();
    if (c['subsequent_plan'] != null) _subsequentPlanController.text = c['subsequent_plan'].toString();

    // 13. 법무 검토
    if (c['review_type'] != null) _legalReviewType = c['review_type'].toString();
    if (c['urgency'] != null) _legalUrgency = c['urgency'].toString();
    if (c['case_title'] != null) _contractNameController.text = c['case_title'].toString();
    if (c['review_due_date'] != null) _reviewDueDate = DateTime.tryParse(c['review_due_date'].toString());
    if (c['key_issues'] != null) _keyIssuesController.text = c['key_issues'].toString();

    // 14. 사업검토
    if (c['biz_type'] != null) _bizType = c['biz_type'].toString();
    if (c['location'] != null) _locationController.text = c['location'].toString();
    if (c['building_scale'] != null) _buildingScaleController.text = c['building_scale'].toString();
    if (c['land_area'] != null) _landAreaController.text = c['land_area'].toString();
    if (c['gross_floor_area'] != null) _grossFloorAreaController.text = c['gross_floor_area'].toString();
    if (c['total_revenue'] != null) _totalRevenueController.text = c['total_revenue'].toString();
    if (c['total_cost'] != null) _totalCostController.text = c['total_cost'].toString();
    if (c['required_equity'] != null) _requiredEquityController.text = c['required_equity'].toString();
    if (c['pf_loan_amount'] != null) _pfLoanAmountController.text = c['pf_loan_amount'].toString();
    if (c['land_secure_date'] != null) _landSecureDate = DateTime.tryParse(c['land_secure_date'].toString());
    if (c['approval_target_date'] != null) _approvalTargetDate = DateTime.tryParse(c['approval_target_date'].toString());
    if (c['completion_date'] != null) _completionDate = DateTime.tryParse(c['completion_date'].toString());
    if (c['market_analysis'] != null) _marketAnalysisController.text = c['market_analysis'].toString();
    if (c['risk_factors'] != null) _riskFactorsController.text = c['risk_factors'].toString();

    // 15. 사업추진 승인
    if (c['approval_type'] != null) _bizApprovalType = c['approval_type'].toString();
    if (c['biz_scale_summary'] != null) _bizScaleSummaryController.text = c['biz_scale_summary'].toString();
    if (c['requested_amount'] != null) _requestedAmountController.text = c['requested_amount'].toString();
    if (c['total_project_cost'] != null) _totalProjectCostController.text = c['total_project_cost'].toString();
    if (c['total_expected_revenue'] != null) _totalExpectedRevenueController.text = c['total_expected_revenue'].toString();
    if (c['budget_usage_plan'] != null) _budgetUsagePlanController.text = c['budget_usage_plan'].toString();
    if (c['resolution_matters'] != null) _resolutionMattersController.text = c['resolution_matters'].toString();
    if (c['pm_lead'] != null) _pmLeadController.text = c['pm_lead'].toString();
    if (c['target_schedule'] != null) _targetScheduleController.text = c['target_schedule'].toString();
    if (c['expected_effects'] != null) _expectedEffectsController.text = c['expected_effects'].toString();

    // 16. 프로젝트 의사결정
    if (c['decision_type'] != null) _projectDecisionType = c['decision_type'].toString();
    if (c['urgency'] != null) _decisionUrgency = c['urgency'].toString();
    if (c['decision_subject'] != null) _docNumberExtController.text = c['decision_subject'].toString();
    if (c['decision_due_date'] != null) _decisionDueDate = DateTime.tryParse(c['decision_due_date'].toString());
    if (c['financial_impact'] != null) _amountController.text = c['financial_impact'].toString();
    if (c['background_issue'] != null) _generalContentController.text = c['background_issue'].toString();
    if (c['option_1'] != null) _option1Controller.text = c['option_1'].toString();
    if (c['option_2'] != null) _option2Controller.text = c['option_2'].toString();
    if (c['option_3'] != null) _option3Controller.text = c['option_3'].toString();
    if (c['recommendation'] != null) _purposeController.text = c['recommendation'].toString();
    if (c['action_plan'] != null) _actionPlanController.text = c['action_plan'].toString();
  }

  @override
  void dispose() {
    _titleController.dispose();
    _leaveDaysController.dispose();
    _leaveReasonController.dispose();
    _substituteWorkerController.dispose();
    _emergencyContactController.dispose();
    _amountController.dispose();
    _purposeController.dispose();
    _vendorController.dispose();
    _generalContentController.dispose();
    _receiverController.dispose();
    _referToController.dispose();
    _senderNameController.dispose();
    _docNumberExtController.dispose();
    _letterSubjectController.dispose();
    _letterBodyController.dispose();
    _enclosedFilesController.dispose();
    _sealCountController.dispose();
    _scheduleController.dispose();
    _expectedEffectController.dispose();
    _noteController.dispose();
    _destinationController.dispose();
    _companionController.dispose();
    _transportCostController.dispose();
    _lodgingCostController.dispose();
    _dailyAllowanceController.dispose();
    _otherCostController.dispose();
    _itineraryController.dispose();
    _startTimeController.dispose();
    _endTimeController.dispose();
    _breakHoursController.dispose();
    _totalHoursController.dispose();
    _coWorkersController.dispose();
    _targetNameController.dispose();
    _currentDeptController.dispose();
    _currentPositionController.dispose();
    _newDeptController.dispose();
    _newPositionController.dispose();
    _typeDescController.dispose();
    _certCountController.dispose();
    _submitToController.dispose();
    _usagePurposeController.dispose();
    _eventPlaceController.dispose();
    _supportItemsController.dispose();
    _deliveryLocationController.dispose();
    _bankNameController.dispose();
    _accountNumberController.dispose();
    _accountHolderController.dispose();
    _targetMonthController.dispose();
    _cardNumberController.dispose();
    _contractNameController.dispose();
    _contractorCeoController.dispose();
    _contractorRegNumberController.dispose();
    _contractorContactController.dispose();
    _paymentTermsController.dispose();
    _warrantyTermsController.dispose();
    _specialTermsController.dispose();
    _origContractNameController.dispose();
    _origContractNoController.dispose();
    _origAmountController.dispose();
    _changeAmountController.dispose();
    _periodChangeDescController.dispose();
    _settlementAmountController.dispose();
    _penaltyTermsController.dispose();
    _subsequentPlanController.dispose();
    _keyIssuesController.dispose();
    _locationController.dispose();
    _buildingScaleController.dispose();
    _landAreaController.dispose();
    _grossFloorAreaController.dispose();
    _totalRevenueController.dispose();
    _totalCostController.dispose();
    _requiredEquityController.dispose();
    _pfLoanAmountController.dispose();
    _marketAnalysisController.dispose();
    _riskFactorsController.dispose();
    _bizScaleSummaryController.dispose();
    _requestedAmountController.dispose();
    _totalProjectCostController.dispose();
    _totalExpectedRevenueController.dispose();
    _budgetUsagePlanController.dispose();
    _resolutionMattersController.dispose();
    _pmLeadController.dispose();
    _targetScheduleController.dispose();
    _expectedEffectsController.dispose();
    _option1Controller.dispose();
    _option2Controller.dispose();
    _option3Controller.dispose();
    _actionPlanController.dispose();
    super.dispose();
  }

  Future<void> _updateRoutePreview() async {
    if (_selectedDocType == null) {
      setState(() => _previewSteps = []);
      return;
    }

    setState(() => _isPreviewLoading = true);
    try {
      final amount = num.tryParse(_amountController.text.replaceAll(',', '').trim());
      final repo = ref.read(approvalRepositoryProvider);
      final steps = await repo.fetchRoutePreview(
        docTypeId: _selectedDocType!.id,
        assignmentId: _selectedAssignment?.id,
        amount: amount,
      );
      if (mounted) {
        setState(() {
          _previewSteps = steps;
          _isPreviewLoading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _isPreviewLoading = false);
      }
    }
  }

  Future<void> _pickFiles() async {
    final result = await FilePicker.platform.pickFiles(allowMultiple: true);
    if (result != null && result.paths.isNotEmpty) {
      setState(() {
        _attachedFilePaths.addAll(result.paths.whereType<String>());
      });
    }
  }

  void _removeFile(int index) {
    setState(() {
      _attachedFilePaths.removeAt(index);
    });
  }

  Map<String, dynamic> _buildContentMap() {
    final normKey = _selectedDocType?.formTemplateKey.toUpperCase();
    final map = <String, dynamic>{};

    if (normKey == 'LEAVE_APPLICATION' || normKey == 'LEAVE') {
      map['leave_type'] = _leaveType;
      map['start_date'] = _startDate?.toIso8601String().split('T').first;
      map['end_date'] = _endDate?.toIso8601String().split('T').first;
      map['days'] = double.tryParse(_leaveDaysController.text) ?? 1.0;
      map['days_count'] = map['days'];
      map['reason'] = _leaveReasonController.text.trim();
      map['substitute_worker'] = _substituteWorkerController.text.trim();
      map['emergency_contact'] = _emergencyContactController.text.trim();
    } else if (normKey == 'EXPENSE_REPORT' || normKey == 'EXPENSE') {
      final amt = num.tryParse(_amountController.text.replaceAll(',', '').trim()) ?? 0;
      map['expense_type'] = _expenseType;
      map['payment_due_date'] = _paymentDueDate?.toIso8601String().split('T').first;
      map['bank_name'] = _bankNameController.text.trim();
      map['account_number'] = _accountNumberController.text.trim();
      map['account_holder'] = _accountHolderController.text.trim();
      map['total_amount'] = amt;
      map['amount'] = amt;
      map['purpose'] = _purposeController.text.trim();
      map['items'] = [
        {
          'date': DateTime.now().toIso8601String().split('T').first,
          'description': _purposeController.text.trim().isNotEmpty ? _purposeController.text.trim() : '지출 내역',
          'amount': amt,
          'note': _noteController.text.trim(),
        }
      ];
    } else if (normKey == 'PURCHASE_ORDER' || normKey == 'PURCHASE') {
      final amt = num.tryParse(_amountController.text.replaceAll(',', '').trim()) ?? 0;
      map['total_amount'] = amt;
      map['amount'] = amt;
      map['vendor'] = _vendorController.text.trim();
      map['purpose'] = _purposeController.text.trim();
      map['delivery_due_date'] = _deliveryDueDate?.toIso8601String().split('T').first;
      map['delivery_location'] = _deliveryLocationController.text.trim();
      map['items'] = [
        {
          'name': _purposeController.text.trim().isNotEmpty ? _purposeController.text.trim() : '구매 품목',
          'quantity': 1,
          'unit_price': amt,
          'supply_price': amt,
          'vat': 0,
        }
      ];
    } else if (normKey == 'OFFICIAL_LETTER') {
      map['receiver'] = _receiverController.text.trim();
      map['refer_to'] = _referToController.text.trim();
      map['sender_name'] = _senderNameController.text.trim();
      map['doc_number_external'] = _docNumberExtController.text.trim();
      map['letter_subject'] = _letterSubjectController.text.trim();
      map['letter_body'] = _letterBodyController.text.trim();
      map['enclosed_files_desc'] = _enclosedFilesController.text.trim();
      map['send_method'] = _sendMethod;
      map['send_due_date'] = _sendDueDate?.toIso8601String().split('T').first;
      map['seal_type'] = _sealType;
      map['seal_count'] = int.tryParse(_sealCountController.text) ?? 1;
    } else if (normKey == 'GENERAL' || normKey == 'BIZ_APPROVAL') {
      final amt = num.tryParse(_amountController.text.replaceAll(',', '').trim()) ?? 0;
      map['purpose'] = _purposeController.text.trim();
      map['schedule'] = _scheduleController.text.trim();
      map['budget_account'] = _budgetAccount;
      map['budget'] = amt;
      map['amount'] = amt;
      map['content'] = _generalContentController.text.trim();
      map['expected_effect'] = _expectedEffectController.text.trim();
      map['note'] = _noteController.text.trim();
    } else if (normKey == 'BUSINESS_TRIP' || normKey == 'TRIP') {
      final tCost = num.tryParse(_transportCostController.text.replaceAll(',', '').trim()) ?? 0;
      final lCost = num.tryParse(_lodgingCostController.text.replaceAll(',', '').trim()) ?? 0;
      final dCost = num.tryParse(_dailyAllowanceController.text.replaceAll(',', '').trim()) ?? 0;
      final oCost = num.tryParse(_otherCostController.text.replaceAll(',', '').trim()) ?? 0;
      final total = tCost + lCost + dCost + oCost;

      map['trip_type'] = _tripType;
      map['destination'] = _destinationController.text.trim();
      map['start_date'] = _startDate?.toIso8601String().split('T').first;
      map['end_date'] = _endDate?.toIso8601String().split('T').first;
      map['days'] = double.tryParse(_leaveDaysController.text) ?? 1.0;
      map['days_count'] = map['days'];
      map['purpose'] = _purposeController.text.trim();
      map['companion'] = _companionController.text.trim();
      map['substitute_worker'] = _substituteWorkerController.text.trim();
      map['transportation'] = _transportation;
      map['emergency_contact'] = _emergencyContactController.text.trim();
      map['transport_cost'] = tCost;
      map['lodging_cost'] = lCost;
      map['daily_allowance'] = dCost;
      map['other_cost'] = oCost;
      map['total_cost'] = total;
      map['amount'] = total;
      map['itinerary'] = _itineraryController.text.trim();
    } else if (normKey == 'OVERTIME' || normKey == 'OVERTIME_WORK') {
      map['work_type'] = _workType;
      map['work_date'] = _workDate?.toIso8601String().split('T').first;
      map['start_time'] = _startTimeController.text.trim();
      map['end_time'] = _endTimeController.text.trim();
      map['break_hours'] = double.tryParse(_breakHoursController.text) ?? 0.0;
      map['total_hours'] = double.tryParse(_totalHoursController.text) ?? 3.0;
      map['compensation_type'] = _compensationType;
      map['reason'] = _leaveReasonController.text.trim().isNotEmpty
          ? _leaveReasonController.text.trim()
          : _generalContentController.text.trim();
      map['co_workers'] = _coWorkersController.text.trim();
      map['note'] = _noteController.text.trim();
    } else if (normKey == 'HR_APPOINTMENT' || normKey == 'APPOINTMENT') {
      map['appointment_type'] = _appointmentType;
      map['effective_date'] = _effectiveDate?.toIso8601String().split('T').first;
      map['reason'] = _generalContentController.text.trim().isNotEmpty
          ? _generalContentController.text.trim()
          : _leaveReasonController.text.trim();
      map['note'] = _noteController.text.trim();
      map['targets'] = [
        {
          'name': _targetNameController.text.trim(),
          'current_dept': _currentDeptController.text.trim(),
          'current_position': _currentPositionController.text.trim(),
          'new_dept': _newDeptController.text.trim(),
          'new_position': _newPositionController.text.trim(),
          'type_desc': _typeDescController.text.trim(),
          'note': _noteController.text.trim(),
        }
      ];
    } else if (normKey == 'HR_REQUEST' || normKey == 'CERT_REQUEST') {
      map['request_type'] = _hrRequestType;
      map['receive_method'] = _receiveMethod;
      map['reason'] = _generalContentController.text.trim().isNotEmpty
          ? _generalContentController.text.trim()
          : _leaveReasonController.text.trim();
      map['note'] = _noteController.text.trim();

      if (_hrRequestType == 'CERTIFICATE') {
        map['cert_type'] = _certType;
        map['cert_language'] = _certLanguage;
        map['cert_count'] = int.tryParse(_certCountController.text) ?? 1;
        map['submit_to'] = _submitToController.text.trim();
        map['usage_purpose'] = _usagePurposeController.text.trim();
        map['include_resident_num'] = _includeResidentNum;
      } else if (_hrRequestType == 'CONGRATULATION_CONDOLENCE') {
        final amt = num.tryParse(_amountController.text.replaceAll(',', '').trim()) ?? 0;
        map['event_type'] = _eventType;
        map['event_date'] = _eventDate?.toIso8601String().split('T').first;
        map['event_place'] = _eventPlaceController.text.trim();
        map['support_items'] = _supportItemsController.text.trim();
        map['congratulation_amount'] = amt;
        map['amount'] = amt;
      } else if (_hrRequestType == 'LEAVE_OF_ABSENCE') {
        map['leave_start_date'] = _startDate?.toIso8601String().split('T').first;
        map['leave_end_date'] = _endDate?.toIso8601String().split('T').first;
      } else if (_hrRequestType == 'REINSTATEMENT') {
        map['reinstatement_date'] = _startDate?.toIso8601String().split('T').first;
      }
    } else if (normKey == 'EXPENSE_SETTLEMENT' || normKey == 'SETTLEMENT') {
      final amt = num.tryParse(_amountController.text.replaceAll(',', '').trim()) ?? 0;
      map['settlement_type'] = _settlementType;
      map['target_month'] = _targetMonthController.text.trim();
      map['card_number'] = _cardNumberController.text.trim();
      map['bank_name'] = _bankNameController.text.trim();
      map['account_number'] = _accountNumberController.text.trim();
      map['account_holder'] = _accountHolderController.text.trim();
      map['total_amount'] = amt;
      map['amount'] = amt;
      map['reason'] = _purposeController.text.trim().isNotEmpty
          ? _purposeController.text.trim()
          : _generalContentController.text.trim();
      map['note'] = _noteController.text.trim();
      map['items'] = [
        {
          'date': DateTime.now().toIso8601String().split('T').first,
          'merchant': _vendorController.text.trim().isNotEmpty ? _vendorController.text.trim() : '경비 사용처',
          'category': '복리후생비(식대/음료)',
          'amount': amt,
          'purpose': map['reason'],
        }
      ];
    } else if (normKey == 'ADVANCE' || normKey == 'ADVANCE_PAY' || normKey == 'ADVANCE_REQUEST') {
      final amt = num.tryParse(_amountController.text.replaceAll(',', '').trim()) ?? 0;
      map['advance_type'] = _advanceType;
      map['receiver_type'] = _receiverType;
      map['payment_due_date'] = _paymentDueDate?.toIso8601String().split('T').first;
      map['settlement_due_date'] = _settlementDueDate?.toIso8601String().split('T').first;
      map['advance_amount'] = amt;
      map['amount'] = amt;
      map['bank_name'] = _bankNameController.text.trim();
      map['account_number'] = _accountNumberController.text.trim();
      map['account_holder'] = _accountHolderController.text.trim();
      map['purpose'] = _purposeController.text.trim().isNotEmpty
          ? _purposeController.text.trim()
          : _generalContentController.text.trim();
      map['settlement_promise'] = _settlementPromise;
      map['note'] = _noteController.text.trim();
    } else if (normKey == 'CONTRACT' || normKey == 'CONTRACT_APPROVAL' || normKey == 'CONTRACT_PROPOSAL') {
      final amt = num.tryParse(_amountController.text.replaceAll(',', '').trim()) ?? 0;
      map['contract_type'] = _contractType;
      map['contract_kind'] = _contractKind;
      map['contract_name'] = _contractNameController.text.trim().isNotEmpty
          ? _contractNameController.text.trim()
          : _titleController.text.trim();
      map['contractor_name'] = _vendorController.text.trim();
      map['contractor_ceo'] = _contractorCeoController.text.trim();
      map['contractor_reg_number'] = _contractorRegNumberController.text.trim();
      map['contractor_contact'] = _contractorContactController.text.trim();
      map['contract_amount'] = amt;
      map['amount'] = amt;
      map['vat_type'] = _vatType;
      map['contract_start_date'] = _startDate?.toIso8601String().split('T').first;
      map['contract_end_date'] = _endDate?.toIso8601String().split('T').first;
      map['payment_terms'] = _paymentTermsController.text.trim();
      map['warranty_terms'] = _warrantyTermsController.text.trim();
      map['purpose_reason'] = _purposeController.text.trim().isNotEmpty
          ? _purposeController.text.trim()
          : _generalContentController.text.trim();
      map['special_terms'] = _specialTermsController.text.trim();
      map['note'] = _noteController.text.trim();
    } else if (normKey == 'CONTRACT_CHANGE' || normKey == 'CONTRACT_TERMINATION' || normKey == 'CONTRACT_AMENDMENT') {
      final origAmt = num.tryParse(_origAmountController.text.replaceAll(',', '').trim()) ?? 0;
      final chgAmt = num.tryParse(_changeAmountController.text.replaceAll(',', '').trim()) ?? 0;
      final stlAmt = num.tryParse(_settlementAmountController.text.replaceAll(',', '').trim()) ?? 0;
      final finAmt = _contractChangeType == 'TERMINATION' ? stlAmt : (origAmt + chgAmt);

      map['change_type'] = _contractChangeType;
      map['original_contract_name'] = _origContractNameController.text.trim().isNotEmpty
          ? _origContractNameController.text.trim()
          : _titleController.text.trim();
      map['contractor_name'] = _vendorController.text.trim();
      map['original_contract_no'] = _origContractNoController.text.trim();
      map['original_contract_date'] = _origContractDate?.toIso8601String().split('T').first;
      map['original_end_date'] = _origEndDate?.toIso8601String().split('T').first;
      map['original_amount'] = origAmt;
      map['change_amount'] = chgAmt;
      map['final_amount'] = finAmt;
      map['final_end_date'] = _endDate?.toIso8601String().split('T').first;
      map['period_change_desc'] = _periodChangeDescController.text.trim();
      map['termination_date'] = _terminationDate?.toIso8601String().split('T').first;
      map['settlement_amount'] = stlAmt;
      map['penalty_terms'] = _penaltyTermsController.text.trim();
      map['amount'] = chgAmt.abs() > 0 ? chgAmt.abs() : finAmt;
      map['change_reason'] = _purposeController.text.trim().isNotEmpty
          ? _purposeController.text.trim()
          : _generalContentController.text.trim();
      map['subsequent_plan'] = _subsequentPlanController.text.trim();
      map['note'] = _noteController.text.trim();
    } else if (normKey == 'LEGAL_REVIEW' || normKey == 'LEGAL_CONSULTATION' || normKey == 'LEGAL_ADVICE') {
      final amt = num.tryParse(_amountController.text.replaceAll(',', '').trim()) ?? 0;
      map['review_type'] = _legalReviewType;
      map['urgency'] = _legalUrgency;
      map['case_title'] = _contractNameController.text.trim().isNotEmpty
          ? _contractNameController.text.trim()
          : _titleController.text.trim();
      map['review_due_date'] = _reviewDueDate?.toIso8601String().split('T').first;
      map['counterparty'] = _vendorController.text.trim();
      map['dispute_amount'] = amt;
      if (amt > 0) map['amount'] = amt;
      map['background'] = _generalContentController.text.trim().isNotEmpty
          ? _generalContentController.text.trim()
          : _purposeController.text.trim();
      map['key_issues'] = _keyIssuesController.text.trim();
      map['note'] = _noteController.text.trim();
    } else if (normKey == 'BUSINESS_REVIEW' || normKey == 'PROJECT_FEASIBILITY' || normKey == 'BIZ_FEASIBILITY' || normKey == 'PROJECT_REVIEW' || normKey == 'INVESTMENT_REVIEW') {
      final rev = num.tryParse(_totalRevenueController.text.replaceAll(',', '').trim()) ?? 0;
      final cst = num.tryParse(_totalCostController.text.replaceAll(',', '').trim()) ?? 0;
      final eqt = num.tryParse(_requiredEquityController.text.replaceAll(',', '').trim()) ?? 0;
      final pf = num.tryParse(_pfLoanAmountController.text.replaceAll(',', '').trim()) ?? 0;
      final np = rev - cst;
      final pr = cst > 0 ? ((np / cst) * 100).toStringAsFixed(2) : '0';

      map['biz_type'] = _bizType;
      map['project_name'] = _contractNameController.text.trim().isNotEmpty
          ? _contractNameController.text.trim()
          : _titleController.text.trim();
      map['location'] = _locationController.text.trim();
      map['building_scale'] = _buildingScaleController.text.trim();
      map['land_area'] = _landAreaController.text.trim();
      map['gross_floor_area'] = _grossFloorAreaController.text.trim();
      map['total_revenue'] = rev;
      map['total_cost'] = cst;
      map['net_profit'] = np;
      map['profit_rate'] = pr;
      map['required_equity'] = eqt;
      map['pf_loan_amount'] = pf;
      map['amount'] = cst; // 총사업비 기준 결재선 연동
      map['land_secure_date'] = _landSecureDate?.toIso8601String().split('T').first;
      map['approval_target_date'] = _approvalTargetDate?.toIso8601String().split('T').first;
      map['start_date'] = _startDate?.toIso8601String().split('T').first;
      map['completion_date'] = _completionDate?.toIso8601String().split('T').first;
      map['market_analysis'] = _marketAnalysisController.text.trim();
      map['risk_factors'] = _riskFactorsController.text.trim();
      map['recommendation'] = _purposeController.text.trim().isNotEmpty
          ? _purposeController.text.trim()
          : _generalContentController.text.trim();
      map['enclosed_docs'] = _noteController.text.trim();
      map['note'] = _noteController.text.trim();
    } else if (normKey == 'BUSINESS_APPROVAL' || normKey == 'PROJECT_APPROVAL' || normKey == 'DEV_APPROVAL' || normKey == 'INVESTMENT_APPROVAL') {
      final reqAmt = num.tryParse(_requestedAmountController.text.replaceAll(',', '').trim()) ?? 0;
      final cst = num.tryParse(_totalProjectCostController.text.replaceAll(',', '').trim()) ?? 0;
      final rev = num.tryParse(_totalExpectedRevenueController.text.replaceAll(',', '').trim()) ?? 0;
      final np = rev - cst;

      map['approval_type'] = _bizApprovalType;
      map['project_name'] = _contractNameController.text.trim().isNotEmpty
          ? _contractNameController.text.trim()
          : _titleController.text.trim();
      map['location'] = _locationController.text.trim();
      map['biz_scale_summary'] = _bizScaleSummaryController.text.trim();
      map['requested_amount'] = reqAmt;
      map['approval_budget'] = reqAmt;
      map['total_project_cost'] = cst;
      map['total_expected_revenue'] = rev;
      map['expected_profit'] = np;
      map['budget_usage_plan'] = _budgetUsagePlanController.text.trim();
      map['amount'] = reqAmt > 0 ? reqAmt : cst;
      map['resolution_matters'] = _resolutionMattersController.text.trim().isNotEmpty
          ? _resolutionMattersController.text.trim()
          : _purposeController.text.trim();
      map['pm_lead'] = _pmLeadController.text.trim();
      map['target_schedule'] = _targetScheduleController.text.trim();
      map['expected_effects'] = _expectedEffectsController.text.trim();
      map['enclosed_docs'] = _noteController.text.trim();
      map['note'] = _noteController.text.trim();
    } else if (normKey == 'PROJECT_DECISION' || normKey == 'PROJECT_KEY_DECISION' || normKey == 'DECISION_PROPOSAL' || normKey == 'KEY_DECISION') {
      final finImpact = num.tryParse(_amountController.text.replaceAll(',', '').trim()) ?? 0;

      map['decision_type'] = _projectDecisionType;
      map['urgency'] = _decisionUrgency;
      map['project_name'] = _contractNameController.text.trim().isNotEmpty
          ? _contractNameController.text.trim()
          : _titleController.text.trim();
      map['decision_subject'] = _docNumberExtController.text.trim().isNotEmpty
          ? _docNumberExtController.text.trim()
          : _titleController.text.trim();
      map['decision_due_date'] = _decisionDueDate?.toIso8601String().split('T').first;
      map['financial_impact'] = finImpact;
      if (finImpact > 0) map['amount'] = finImpact;
      map['background_issue'] = _generalContentController.text.trim().isNotEmpty
          ? _generalContentController.text.trim()
          : _purposeController.text.trim();
      map['option_1'] = _option1Controller.text.trim();
      map['option_2'] = _option2Controller.text.trim();
      map['option_3'] = _option3Controller.text.trim();
      map['recommendation'] = _purposeController.text.trim();
      map['action_plan'] = _actionPlanController.text.trim();
      map['enclosed_docs'] = _noteController.text.trim();
      map['note'] = _noteController.text.trim();
    } else {
      map['body'] = _generalContentController.text.trim();
      final amt = num.tryParse(_amountController.text.replaceAll(',', '').trim());
      if (amt != null) map['amount'] = amt;
    }
    return map;
  }

  Future<void> _handleSave({required bool isDirectSubmit}) async {
    if (_selectedAssignment == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('기안자의 소속 보직 정보가 없어 문서를 기안할 수 없습니다.')),
      );
      return;
    }
    if (!_formKey.currentState!.validate()) return;
    if (_selectedDocType == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('문서 유형을 선택해 주세요.')),
      );
      return;
    }

    setState(() => _isSubmitting = true);
    try {
      final repo = ref.read(approvalRepositoryProvider);
      final content = _buildContentMap();

      final payload = <String, dynamic>{
        'title': _titleController.text.trim(),
        'doc_type': _selectedDocType!.id,
        'drafter_assignment': _selectedAssignment!.id,
        'content': content,
      };

      final ApprovalDocumentModel doc;
      if (widget.editDoc != null) {
        doc = await repo.updateDocument(widget.editDoc!.id, payload);
      } else {
        doc = await repo.createDocument(
          payload,
          filePaths: _attachedFilePaths.isNotEmpty ? _attachedFilePaths : null,
        );
      }

      if (isDirectSubmit) {
        await repo.submitDocument(doc.id);
      }

      ref.invalidate(pendingApprovalsProvider);
      ref.invalidate(draftedApprovalsProvider);
      ref.invalidate(approvedApprovalsProvider);
      ref.invalidate(allApprovalsProvider);
      if (widget.editDoc != null) {
        ref.invalidate(approvalDetailProvider(widget.editDoc!.id));
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              isDirectSubmit
                  ? (widget.editDoc != null ? '결재가 성공적으로 재상신되었습니다.' : '결재가 성공적으로 상신되었습니다.')
                  : (widget.editDoc != null ? '문서 수정 내용이 저장되었습니다.' : '문서가 임시저장되었습니다.'),
            ),
            backgroundColor: context.colors.success,
          ),
        );
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isSubmitting = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('저장 실패: $e'),
            backgroundColor: context.colors.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final assignmentsAsync = ref.watch(myAssignmentsProvider);
    final hasValidAssignment = _selectedAssignment != null;

    return Scaffold(
      backgroundColor: context.colors.bgPrimary,
      appBar: AppBar(
        title: Text(
          widget.editDoc != null ? '결재 문서 수정' : '새 결재 기안',
          style: AppTextStyles.titleMd.copyWith(
            fontWeight: FontWeight.w800,
            color: context.colors.textPrimary,
          ),
        ),
        backgroundColor: context.colors.bgCard,
        elevation: 0,
      ),
      body: assignmentsAsync.when(
        data: (assignments) {
          if (assignments.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.badge_outlined, size: 56, color: context.colors.textDisabled),
                    const SizedBox(height: 16),
                    Text(
                      '기안 가능한 보직 정보가 없습니다.',
                      style: AppTextStyles.titleMd.copyWith(
                        fontWeight: FontWeight.bold,
                        color: context.colors.textPrimary,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '전자결재 문서를 기안하려면 임직원(Staff) 및 소속 부서 보직이 먼저 등록되어 있어야 합니다.\n관리자에게 문의해 주세요.',
                      style: AppTextStyles.bodySm.copyWith(color: context.colors.textMuted),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            );
          }
          return _buildForm(context, assignments);
        },
        loading: () => const LoadingShimmer(itemCount: 5, itemHeight: 80),
        error: (e, _) => Center(child: Text('보직 정보를 불러올 수 없습니다: $e')),
      ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: context.colors.bgCard,
          border: Border(top: BorderSide(color: context.colors.border, width: 0.8)),
        ),
        child: SafeArea(
          child: Row(
            children: [
              Expanded(
                child: SizedBox(
                  height: 46,
                  child: OutlinedButton(
                    onPressed: (_isSubmitting || !hasValidAssignment)
                        ? null
                        : () => _handleSave(isDirectSubmit: false),
                    style: OutlinedButton.styleFrom(
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      side: BorderSide(color: context.colors.border),
                    ),
                    child: const Text('임시저장', style: TextStyle(fontWeight: FontWeight.w700)),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                flex: 2,
                child: SizedBox(
                  height: 46,
                  child: ElevatedButton.icon(
                    onPressed: (_isSubmitting || !hasValidAssignment)
                        ? null
                        : () => _handleSave(isDirectSubmit: true),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: context.colors.accentApproval,
                      disabledBackgroundColor: context.colors.border,
                      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                      elevation: 0,
                    ),
                    icon: _isSubmitting
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Icon(Icons.send_rounded, color: Colors.white, size: 18),
                    label: const Text(
                      '결재 상신',
                      style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildForm(BuildContext context, List<StaffAssignmentItemModel> assignments) {
    if (_selectedAssignment == null && assignments.isNotEmpty) {
      if (widget.editDoc?.drafterAssignment != null) {
        _selectedAssignment = assignments.where((a) => a.id == widget.editDoc!.drafterAssignment).firstOrNull;
      }
      _selectedAssignment ??= assignments.where((a) => a.isPrimary).firstOrNull ?? assignments.first;
    }

    final docTypesAsync = ref.watch(forDraftDocTypesProvider(_selectedAssignment?.id));
    final normKey = _selectedDocType?.formTemplateKey.toUpperCase();

    return Form(
      key: _formKey,
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── 1. 기안 보직 선택 ───────────────────────────────────────
            _buildSectionCard(
              context,
              title: '기안자 정보',
              icon: Icons.person_pin_circle_outlined,
              child: DropdownButtonFormField<StaffAssignmentItemModel>(
                value: _selectedAssignment,
                decoration: _inputDecoration(context, '기안 보직'),
                items: assignments.map((a) {
                  final primary = a.isPrimary ? '[주]' : '[겸]';
                  final label = '$primary ${a.departmentName ?? ''} ${a.dutyName ?? a.positionName ?? ''}'.trim();
                  return DropdownMenuItem(value: a, child: Text(label, style: const TextStyle(fontSize: 13)));
                }).toList(),
                onChanged: (val) {
                  setState(() {
                    _selectedAssignment = val;
                    _selectedDocType = null;
                  });
                  _updateRoutePreview();
                },
              ),
            ),
            const SizedBox(height: 14),

            // ── 2. 문서 유형 선택 ───────────────────────────────────────
            _buildSectionCard(
              context,
              title: '결재 문서 양식',
              icon: Icons.category_outlined,
              child: docTypesAsync.when(
                data: (docTypes) {
                  if (_selectedDocType == null && widget.editDoc != null) {
                    _selectedDocType = docTypes.where((dt) => dt.id == widget.editDoc!.docType).firstOrNull;
                  }
                  return DropdownButtonFormField<DocumentTypeModel>(
                    value: _selectedDocType,
                    decoration: _inputDecoration(context, '문서 유형 선택'),
                    items: docTypes.map((dt) {
                      final cat = dt.categoryName != null ? '[${dt.categoryName}] ' : '';
                      return DropdownMenuItem(
                        value: dt,
                        child: Text('$cat${dt.name}', style: const TextStyle(fontSize: 13)),
                      );
                    }).toList(),
                    onChanged: (val) {
                      setState(() => _selectedDocType = val);
                      _updateRoutePreview();
                    },
                    validator: (v) => v == null ? '문서 유형을 선택하세요' : null,
                  );
                },
                loading: () => const LinearProgressIndicator(),
                error: (e, _) => Text('문서 유형 로드 실패: $e'),
              ),
            ),
            const SizedBox(height: 14),

            // ── 3. 문서 기본 정보 및 본문 ─────────────────────────────
            _buildSectionCard(
              context,
              title: '문서 내용 작성',
              icon: Icons.edit_note_rounded,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // 제목
                  TextFormField(
                    controller: _titleController,
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                    decoration: _inputDecoration(context, '문서 제목 (필수)'),
                    validator: (v) => (v == null || v.trim().isEmpty) ? '제목을 입력하세요' : null,
                  ),
                  const SizedBox(height: 12),

                  // 템플릿별 필드 렌더링
                  if (normKey == 'LEAVE_APPLICATION' || normKey == 'LEAVE')
                    _buildLeaveFormFields(context)
                  else if (normKey == 'EXPENSE_REPORT' || normKey == 'EXPENSE')
                    _buildExpenseFormFields(context)
                  else if (normKey == 'PURCHASE_ORDER' || normKey == 'PURCHASE')
                    _buildPurchaseFormFields(context)
                  else if (normKey == 'OFFICIAL_LETTER')
                    _buildOfficialLetterFormFields(context)
                  else if (normKey == 'BUSINESS_TRIP' || normKey == 'TRIP')
                    _buildBusinessTripFormFields(context)
                  else if (normKey == 'OVERTIME' || normKey == 'OVERTIME_WORK')
                    _buildOvertimeFormFields(context)
                  else if (normKey == 'HR_APPOINTMENT' || normKey == 'APPOINTMENT')
                    _buildHrAppointmentFormFields(context)
                  else if (normKey == 'HR_REQUEST' || normKey == 'CERT_REQUEST')
                    _buildHrRequestFormFields(context)
                  else if (normKey == 'EXPENSE_SETTLEMENT' || normKey == 'SETTLEMENT')
                    _buildExpenseSettlementFormFields(context)
                  else if (normKey == 'ADVANCE' || normKey == 'ADVANCE_PAY' || normKey == 'ADVANCE_REQUEST')
                    _buildAdvancePaymentFormFields(context)
                  else if (normKey == 'CONTRACT' || normKey == 'CONTRACT_APPROVAL' || normKey == 'CONTRACT_PROPOSAL')
                    _buildContractFormFields(context)
                  else if (normKey == 'CONTRACT_CHANGE' || normKey == 'CONTRACT_TERMINATION' || normKey == 'CONTRACT_AMENDMENT')
                    _buildContractChangeFormFields(context)
                  else if (normKey == 'LEGAL_REVIEW' || normKey == 'LEGAL_CONSULTATION' || normKey == 'LEGAL_ADVICE')
                    _buildLegalReviewFormFields(context)
                  else if (normKey == 'BUSINESS_REVIEW' || normKey == 'PROJECT_FEASIBILITY' || normKey == 'BIZ_FEASIBILITY' || normKey == 'PROJECT_REVIEW' || normKey == 'INVESTMENT_REVIEW')
                    _buildBusinessReviewFormFields(context)
                  else if (normKey == 'BUSINESS_APPROVAL' || normKey == 'PROJECT_APPROVAL' || normKey == 'DEV_APPROVAL' || normKey == 'INVESTMENT_APPROVAL')
                    _buildBusinessApprovalFormFields(context)
                  else if (normKey == 'PROJECT_DECISION' || normKey == 'PROJECT_KEY_DECISION' || normKey == 'DECISION_PROPOSAL' || normKey == 'KEY_DECISION')
                    _buildProjectDecisionFormFields(context)
                  else
                    _buildGeneralFormFields(context),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // ── 4. 실시간 결재선 미리보기 ─────────────────────────────
            _buildSectionCard(
              context,
              title: '자동 결재선 미리보기',
              icon: Icons.alt_route_rounded,
              child: _buildRoutePreviewWidget(context),
            ),
            const SizedBox(height: 14),

            // ── 5. 첨부파일 ─────────────────────────────────────────────
            _buildSectionCard(
              context,
              title: '첨부파일',
              icon: Icons.attach_file_rounded,
              action: TextButton.icon(
                onPressed: _pickFiles,
                icon: const Icon(Icons.add, size: 16),
                label: const Text('파일 추가', style: TextStyle(fontSize: 12)),
              ),
              child: Column(
                children: [
                  if (_attachedFilePaths.isEmpty)
                    Text('첨부된 파일이 없습니다.', style: TextStyle(fontSize: 12, color: context.colors.textMuted))
                  else
                    for (int i = 0; i < _attachedFilePaths.length; i++)
                      Container(
                        margin: const EdgeInsets.only(bottom: 6),
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        color: context.colors.bgSurface,
                        child: Row(
                          children: [
                            Icon(Icons.insert_drive_file_outlined, size: 16, color: context.colors.textSecond),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                _attachedFilePaths[i].split('/').last,
                                style: const TextStyle(fontSize: 12),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            IconButton(
                              icon: const Icon(Icons.close, size: 16),
                              padding: EdgeInsets.zero,
                              constraints: const BoxConstraints(),
                              onPressed: () => _removeFile(i),
                            ),
                          ],
                        ),
                      ),
                ],
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildLeaveFormFields(BuildContext context) {
    return Column(
      children: [
        DropdownButtonFormField<String>(
          value: _leaveType,
          decoration: _inputDecoration(context, '휴가 구분'),
          items: const [
            DropdownMenuItem(value: '연차', child: Text('연차')),
            DropdownMenuItem(value: '반차', child: Text('반차')),
            DropdownMenuItem(value: '경조사', child: Text('경조사')),
            DropdownMenuItem(value: '병가', child: Text('병가')),
            DropdownMenuItem(value: '공가', child: Text('공가')),
            DropdownMenuItem(value: '기타', child: Text('기타')),
          ],
          onChanged: (v) {
            setState(() {
              _leaveType = v ?? '연차';
              if (_leaveType == '반차') {
                _leaveDaysController.text = '0.5';
                if (_startDate != null) _endDate = _startDate;
              } else if (_startDate != null && _endDate != null) {
                final diff = _endDate!.difference(_startDate!).inDays + 1;
                _leaveDaysController.text = (diff > 0 ? diff : 1).toString();
              }
            });
          },
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _startDate ?? DateTime.now(),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) {
                    setState(() {
                      _startDate = d;
                      if (_endDate == null || _endDate!.isBefore(_startDate!)) {
                        _endDate = _startDate;
                      }
                      if (_leaveType == '반차') {
                        _leaveDaysController.text = '0.5';
                        _endDate = _startDate;
                      } else {
                        final diff = _endDate!.difference(_startDate!).inDays + 1;
                        _leaveDaysController.text = (diff > 0 ? diff : 1).toString();
                      }
                    });
                  }
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _startDate != null ? '시작: ${_startDate!.toIso8601String().split('T').first}' : '시작일 선택',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _endDate ?? (_startDate ?? DateTime.now()),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) {
                    setState(() {
                      _endDate = d;
                      if (_startDate != null && _endDate!.isBefore(_startDate!)) {
                        _startDate = _endDate;
                      }
                      if (_leaveType == '반차') {
                        _leaveDaysController.text = '0.5';
                      } else if (_startDate != null) {
                        final diff = _endDate!.difference(_startDate!).inDays + 1;
                        _leaveDaysController.text = (diff > 0 ? diff : 1).toString();
                      }
                    });
                  }
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _endDate != null ? '종료: ${_endDate!.toIso8601String().split('T').first}' : '종료일 선택',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _leaveDaysController,
          keyboardType: TextInputType.number,
          decoration: _inputDecoration(context, '휴가 일수 (예: 1.0, 0.5)'),
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _leaveReasonController,
          maxLines: 3,
          decoration: _inputDecoration(context, '휴가 사유 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '휴가 사유를 입력하세요' : null,
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _substituteWorkerController,
                decoration: _inputDecoration(context, '업무 대행자 (인수인계자)'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _emergencyContactController,
                decoration: _inputDecoration(context, '비상 연락처'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildExpenseFormFields(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _expenseType,
                decoration: _inputDecoration(context, '지출 구분'),
                items: const [
                  DropdownMenuItem(value: 'CARD', child: Text('법인카드')),
                  DropdownMenuItem(value: 'TAX_INVOICE', child: Text('세금계산서')),
                  DropdownMenuItem(value: 'RECEIPT', child: Text('현금/간이영수증')),
                  DropdownMenuItem(value: 'TRANSFER', child: Text('일반 계좌이체')),
                ],
                onChanged: (v) => setState(() => _expenseType = v ?? 'CARD'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _paymentDueDate ?? DateTime.now(),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _paymentDueDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _paymentDueDate != null ? '지급요청: ${_paymentDueDate!.toIso8601String().split('T').first}' : '지급요청일 선택',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
          ],
        ),
        if (_expenseType != 'CARD') ...[
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                flex: 3,
                child: TextFormField(
                  controller: _bankNameController,
                  decoration: _inputDecoration(context, '은행명'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                flex: 4,
                child: TextFormField(
                  controller: _accountNumberController,
                  decoration: _inputDecoration(context, '계좌번호'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                flex: 3,
                child: TextFormField(
                  controller: _accountHolderController,
                  decoration: _inputDecoration(context, '예금주명'),
                ),
              ),
            ],
          ),
        ],
        const SizedBox(height: 10),
        TextFormField(
          controller: _amountController,
          keyboardType: TextInputType.number,
          decoration: _inputDecoration(context, '총 지출 결의 금액 (원)'),
          onChanged: (_) => _updateRoutePreview(),
          validator: (v) => (v == null || v.trim().isEmpty) ? '지출 금액을 입력하세요' : null,
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _purposeController,
          maxLines: 4,
          decoration: _inputDecoration(context, '지출 목적 및 상세 내역 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '지출 목적을 입력하세요' : null,
        ),
      ],
    );
  }

  Widget _buildPurchaseFormFields(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _amountController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '총 품의 금액 (원)'),
                onChanged: (_) => _updateRoutePreview(),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _vendorController,
                decoration: _inputDecoration(context, '거래처 / 공급업체'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _deliveryDueDate ?? DateTime.now().add(const Duration(days: 7)),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _deliveryDueDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _deliveryDueDate != null ? '납품희망: ${_deliveryDueDate!.toIso8601String().split('T').first}' : '납품희망일 선택',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _deliveryLocationController,
                decoration: _inputDecoration(context, '납품 장소 (예: 본사 4층)'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _purposeController,
          maxLines: 4,
          decoration: _inputDecoration(context, '구매 목적 및 품목 내역 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '구매 목적을 입력하세요' : null,
        ),
      ],
    );
  }

  Widget _buildOfficialLetterFormFields(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _receiverController,
                decoration: _inputDecoration(context, '수신처 (필수)'),
                validator: (v) => (v == null || v.trim().isEmpty) ? '수신처를 입력하세요' : null,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _referToController,
                decoration: _inputDecoration(context, '참조처 (경유)'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _senderNameController,
                decoration: _inputDecoration(context, '발신 명의 (미입력시 대표이사)'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _docNumberExtController,
                decoration: _inputDecoration(context, '대외 문서번호 (선택)'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _letterSubjectController,
          decoration: _inputDecoration(context, '공문 제목 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '공문 제목을 입력하세요' : null,
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _letterBodyController,
          maxLines: 5,
          decoration: _inputDecoration(context, '공문 본문 / 요지 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '공문 본문을 입력하세요' : null,
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _enclosedFilesController,
          maxLines: 2,
          decoration: _inputDecoration(context, '붙임 서류 내역 (선택)'),
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _sendMethod,
                decoration: _inputDecoration(context, '발송 방법'),
                items: const [
                  DropdownMenuItem(value: 'EMAIL', child: Text('이메일')),
                  DropdownMenuItem(value: 'POST', child: Text('등기우편')),
                  DropdownMenuItem(value: 'DIRECT', child: Text('인편(직접전달)')),
                  DropdownMenuItem(value: 'FAX', child: Text('팩스(FAX)')),
                  DropdownMenuItem(value: 'OTHER', child: Text('기타')),
                ],
                onChanged: (v) => setState(() => _sendMethod = v ?? 'EMAIL'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _sendDueDate ?? DateTime.now(),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _sendDueDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _sendDueDate != null ? '발송: ${_sendDueDate!.toIso8601String().split('T').first}' : '발송예정일 선택',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _sealType,
                decoration: _inputDecoration(context, '날인 인감'),
                items: const [
                  DropdownMenuItem(value: 'CORP_SEAL', child: Text('법인인감')),
                  DropdownMenuItem(value: 'USAGE_SEAL_1', child: Text('사용인감 1호')),
                  DropdownMenuItem(value: 'USAGE_SEAL_2', child: Text('사용인감 2호')),
                  DropdownMenuItem(value: 'SIGN', child: Text('서명')),
                  DropdownMenuItem(value: 'OMIT', child: Text('직인생략')),
                ],
                onChanged: (v) => setState(() => _sealType = v ?? 'CORP_SEAL'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _sealCountController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '날인 부수'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildBusinessTripFormFields(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _tripType,
                decoration: _inputDecoration(context, '출장 구분'),
                items: const [
                  DropdownMenuItem(value: 'DOMESTIC', child: Text('국내 출장')),
                  DropdownMenuItem(value: 'OVERSEAS', child: Text('해외 출장')),
                ],
                onChanged: (v) => setState(() => _tripType = v ?? 'DOMESTIC'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _destinationController,
                decoration: _inputDecoration(context, '출장지 (필수)'),
                validator: (v) => (v == null || v.trim().isEmpty) ? '출장지를 입력하세요' : null,
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _startDate ?? DateTime.now(),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _startDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _startDate != null ? '시작: ${_startDate!.toIso8601String().split('T').first}' : '시작일 선택',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _endDate ?? (_startDate ?? DateTime.now()),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _endDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _endDate != null ? '종료: ${_endDate!.toIso8601String().split('T').first}' : '종료일 선택',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _purposeController,
          decoration: _inputDecoration(context, '출장 목적 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '출장 목적을 입력하세요' : null,
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _companionController,
                decoration: _inputDecoration(context, '동행자 명단'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _substituteWorkerController,
                decoration: _inputDecoration(context, '업무 대행자'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _transportation,
                decoration: _inputDecoration(context, '주요 교통편'),
                items: const [
                  DropdownMenuItem(value: 'CORP_CAR', child: Text('법인차량')),
                  DropdownMenuItem(value: 'PRIVATE_CAR', child: Text('개인차량')),
                  DropdownMenuItem(value: 'TRAIN', child: Text('KTX/열차')),
                  DropdownMenuItem(value: 'AIRPLANE', child: Text('항공편')),
                  DropdownMenuItem(value: 'BUS', child: Text('고속버스')),
                  DropdownMenuItem(value: 'PUBLIC', child: Text('대중교통')),
                  DropdownMenuItem(value: 'OTHER', child: Text('기타')),
                ],
                onChanged: (v) => setState(() => _transportation = v ?? 'CORP_CAR'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _emergencyContactController,
                decoration: _inputDecoration(context, '비상 연락처'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _transportCostController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '교통비 (원)'),
                onChanged: (_) => _updateRoutePreview(),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _lodgingCostController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '숙박비 (원)'),
                onChanged: (_) => _updateRoutePreview(),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _dailyAllowanceController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '일비/식비 (원)'),
                onChanged: (_) => _updateRoutePreview(),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _otherCostController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '기타경비 (원)'),
                onChanged: (_) => _updateRoutePreview(),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _itineraryController,
          maxLines: 4,
          decoration: _inputDecoration(context, '세부 일정 계획 (선택)'),
        ),
      ],
    );
  }

  Widget _buildOvertimeFormFields(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _workType,
                decoration: _inputDecoration(context, '근무 구분'),
                items: const [
                  DropdownMenuItem(value: 'OVERTIME', child: Text('평일 연장근무')),
                  DropdownMenuItem(value: 'NIGHT', child: Text('야간근무 (22시 이후)')),
                  DropdownMenuItem(value: 'HOLIDAY', child: Text('휴일 근무')),
                ],
                onChanged: (v) => setState(() => _workType = v ?? 'OVERTIME'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _workDate ?? DateTime.now(),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _workDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _workDate != null ? '일자: ${_workDate!.toIso8601String().split('T').first}' : '근무일자 선택',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _startTimeController,
                decoration: _inputDecoration(context, '시작 시각 (예: 18:30)'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _endTimeController,
                decoration: _inputDecoration(context, '종료 시각 (예: 21:30)'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _breakHoursController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '휴게시간(시간)'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _totalHoursController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '인정 시간(시간)'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        DropdownButtonFormField<String>(
          value: _compensationType,
          decoration: _inputDecoration(context, '보상 방식'),
          items: const [
            DropdownMenuItem(value: 'ALLOWANCE', child: Text('연장/휴일 수당 지급')),
            DropdownMenuItem(value: 'COMP_LEAVE', child: Text('대체휴무 (보상휴가) 적립')),
          ],
          onChanged: (v) => setState(() => _compensationType = v ?? 'ALLOWANCE'),
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _generalContentController,
          maxLines: 4,
          decoration: _inputDecoration(context, '구체적 근무 사유 및 업무 내용 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '근무 사유를 입력하세요' : null,
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _coWorkersController,
                decoration: _inputDecoration(context, '동반 근무자'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _noteController,
                decoration: _inputDecoration(context, '비고 / 특이사항'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildHrAppointmentFormFields(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _appointmentType,
                decoration: _inputDecoration(context, '발령 구분'),
                items: const [
                  DropdownMenuItem(value: 'PROMOTION', child: Text('승진 / 승격')),
                  DropdownMenuItem(value: 'TRANSFER', child: Text('부서이동 / 전보')),
                  DropdownMenuItem(value: 'APPOINT', child: Text('보직 임명/해임')),
                  DropdownMenuItem(value: 'HIRE', child: Text('신규 채용/입사')),
                  DropdownMenuItem(value: 'LEAVE_RETURN', child: Text('휴직 / 복직')),
                  DropdownMenuItem(value: 'RETIRE', child: Text('퇴직 / 면직')),
                  DropdownMenuItem(value: 'DISPATCH', child: Text('현장 파견/복귀')),
                  DropdownMenuItem(value: 'OTHER', child: Text('기타 발령')),
                ],
                onChanged: (v) => setState(() => _appointmentType = v ?? 'PROMOTION'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _effectiveDate ?? DateTime.now(),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _effectiveDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _effectiveDate != null ? '시행: ${_effectiveDate!.toIso8601String().split('T').first}' : '시행일 선택',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _targetNameController,
                decoration: _inputDecoration(context, '대상자 성명 (필수)'),
                validator: (v) => (v == null || v.trim().isEmpty) ? '대상자 성명을 입력하세요' : null,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _typeDescController,
                decoration: _inputDecoration(context, '발령 세부 구분 (예: 승진/전보)'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _currentDeptController,
                decoration: _inputDecoration(context, '현 소속 부서'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _currentPositionController,
                decoration: _inputDecoration(context, '현 직급 / 직책'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _newDeptController,
                decoration: _inputDecoration(context, '발령 부서 (신규)'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _newPositionController,
                decoration: _inputDecoration(context, '발령 직급 / 직책 (신규)'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _generalContentController,
          maxLines: 4,
          decoration: _inputDecoration(context, '발령 사유 및 인사 배경 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '발령 사유를 입력하세요' : null,
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _noteController,
          decoration: _inputDecoration(context, '비고 / 특이사항'),
        ),
      ],
    );
  }

  Widget _buildHrRequestFormFields(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _hrRequestType,
                decoration: _inputDecoration(context, '신청 구분'),
                items: const [
                  DropdownMenuItem(value: 'CERTIFICATE', child: Text('제증명서 발급')),
                  DropdownMenuItem(value: 'CONGRATULATION_CONDOLENCE', child: Text('경조사 지원/경조금')),
                  DropdownMenuItem(value: 'LEAVE_OF_ABSENCE', child: Text('휴직 신청')),
                  DropdownMenuItem(value: 'REINSTATEMENT', child: Text('복직원 제출')),
                  DropdownMenuItem(value: 'ACCOUNT_CHANGE', child: Text('계좌/정보 변경')),
                  DropdownMenuItem(value: 'OTHER', child: Text('기타 인사 신청')),
                ],
                onChanged: (v) => setState(() => _hrRequestType = v ?? 'CERTIFICATE'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _receiveMethod,
                decoration: _inputDecoration(context, '수령 방법'),
                items: const [
                  DropdownMenuItem(value: 'PDF_EMAIL', child: Text('PDF 이메일 수령')),
                  DropdownMenuItem(value: 'PRINT_DIRECT', child: Text('원본 직접 수령')),
                  DropdownMenuItem(value: 'POST', child: Text('우편(등기) 수령')),
                ],
                onChanged: (v) => setState(() => _receiveMethod = v ?? 'PDF_EMAIL'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        // 증명서 전용 필드
        if (_hrRequestType == 'CERTIFICATE') ...[
          Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<String>(
                  value: _certType,
                  decoration: _inputDecoration(context, '증명서 종류'),
                  items: const [
                    DropdownMenuItem(value: 'EMPLOYMENT', child: Text('재직증명서')),
                    DropdownMenuItem(value: 'CAREER', child: Text('경력증명서')),
                    DropdownMenuItem(value: 'RETIREMENT', child: Text('퇴직증명서')),
                    DropdownMenuItem(value: 'WITHHOLDING_TAX', child: Text('원천징수영수증')),
                    DropdownMenuItem(value: 'PAY_SLIP', child: Text('급여명세확인서')),
                    DropdownMenuItem(value: 'OTHER', child: Text('기타 증명서')),
                  ],
                  onChanged: (v) => setState(() => _certType = v ?? 'EMPLOYMENT'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: DropdownButtonFormField<String>(
                  value: _certLanguage,
                  decoration: _inputDecoration(context, '발급 언어'),
                  items: const [
                    DropdownMenuItem(value: 'KOREAN', child: Text('국문')),
                    DropdownMenuItem(value: 'ENGLISH', child: Text('영문')),
                  ],
                  onChanged: (v) => setState(() => _certLanguage = v ?? 'KOREAN'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _submitToController,
                  decoration: _inputDecoration(context, '제출처 (예: 국민은행)'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextFormField(
                  controller: _usagePurposeController,
                  decoration: _inputDecoration(context, '용도 (예: 대출용)'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          CheckboxListTile(
            title: const Text('주민등록번호 뒷자리 전체 표기', style: TextStyle(fontSize: 12.5)),
            value: _includeResidentNum,
            dense: true,
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            onChanged: (v) => setState(() => _includeResidentNum = v ?? false),
          ),
          const SizedBox(height: 10),
        ] else if (_hrRequestType == 'CONGRATULATION_CONDOLENCE') ...[
          Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<String>(
                  value: _eventType,
                  decoration: _inputDecoration(context, '경조 구분'),
                  items: const [
                    DropdownMenuItem(value: 'MARRIAGE_SELF', child: Text('본인 결혼')),
                    DropdownMenuItem(value: 'MARRIAGE_CHILD', child: Text('자녀 결혼')),
                    DropdownMenuItem(value: 'CHILSOON_PARENT', child: Text('부모 칠순/팔순')),
                    DropdownMenuItem(value: 'DEATH_PARENT', child: Text('부모/배우자부모 사망')),
                    DropdownMenuItem(value: 'CHILDBIRTH', child: Text('출산 축하')),
                    DropdownMenuItem(value: 'OTHER', child: Text('기타 경조사')),
                  ],
                  onChanged: (v) => setState(() => _eventType = v ?? 'MARRIAGE_SELF'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: OutlinedButton(
                  onPressed: () async {
                    final d = await showDatePicker(
                      context: context,
                      initialDate: _eventDate ?? DateTime.now(),
                      firstDate: DateTime(2020),
                      lastDate: DateTime(2035),
                    );
                    if (d != null) setState(() => _eventDate = d);
                  },
                  style: OutlinedButton.styleFrom(
                    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                    side: BorderSide(color: context.colors.border),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                  child: Text(
                    _eventDate != null ? '일자: ${_eventDate!.toIso8601String().split('T').first}' : '경조일자 선택',
                    style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _eventPlaceController,
                  decoration: _inputDecoration(context, '경조 장소 / 예식장'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextFormField(
                  controller: _amountController,
                  keyboardType: TextInputType.number,
                  decoration: _inputDecoration(context, '경조금 신청액 (원)'),
                  onChanged: (_) => _updateRoutePreview(),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          TextFormField(
            controller: _supportItemsController,
            decoration: _inputDecoration(context, '물품 지원 요청 (예: 축하화환 1점, 상조용품)'),
          ),
          const SizedBox(height: 10),
        ],

        TextFormField(
          controller: _generalContentController,
          maxLines: 4,
          decoration: _inputDecoration(context, '신청 사유 및 요청 상세 내용 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '신청 사유를 입력하세요' : null,
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _noteController,
          decoration: _inputDecoration(context, '비고 / 특이사항 (선택)'),
        ),
      ],
    );
  }

  Widget _buildExpenseSettlementFormFields(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _settlementType,
                decoration: _inputDecoration(context, '정산 구분'),
                items: const [
                  DropdownMenuItem(value: 'CORP_CARD', child: Text('법인카드 정산')),
                  DropdownMenuItem(value: 'PERSONAL_EXPENSE', child: Text('개인경비 실비환급')),
                  DropdownMenuItem(value: 'BUSINESS_TRIP', child: Text('출장경비 정산')),
                  DropdownMenuItem(value: 'ADVANCE_PAY', child: Text('가지급금 정산')),
                  DropdownMenuItem(value: 'OTHER', child: Text('기타 경비정산')),
                ],
                onChanged: (v) => setState(() => _settlementType = v ?? 'CORP_CARD'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _targetMonthController,
                decoration: _inputDecoration(context, '귀속 연월 (예: 2026-08)'),
                validator: (v) => (v == null || v.trim().isEmpty) ? '귀속 연월을 입력하세요' : null,
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        if (_settlementType == 'CORP_CARD') ...[
          TextFormField(
            controller: _cardNumberController,
            decoration: _inputDecoration(context, '법인카드 정보 (예: 국민 법인카드 5678)'),
          ),
          const SizedBox(height: 10),
        ] else if (_settlementType == 'PERSONAL_EXPENSE') ...[
          Row(
            children: [
              Expanded(
                flex: 3,
                child: TextFormField(
                  controller: _bankNameController,
                  decoration: _inputDecoration(context, '환급 은행'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                flex: 4,
                child: TextFormField(
                  controller: _accountNumberController,
                  decoration: _inputDecoration(context, '환급 계좌번호'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                flex: 3,
                child: TextFormField(
                  controller: _accountHolderController,
                  decoration: _inputDecoration(context, '예금주'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
        ],

        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _amountController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '총 정산 금액 (원)'),
                onChanged: (_) => _updateRoutePreview(),
                validator: (v) => (v == null || v.trim().isEmpty) ? '정산 금액을 입력하세요' : null,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _vendorController,
                decoration: _inputDecoration(context, '주요 가맹점 / 사용처'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _purposeController,
          maxLines: 4,
          decoration: _inputDecoration(context, '정산 개요 및 사용 목적 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '정산 사유를 입력하세요' : null,
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _noteController,
          decoration: _inputDecoration(context, '비고 / 증빙 안내 (예: 영수증 총무팀 전달)'),
        ),
      ],
    );
  }

  Widget _buildAdvancePaymentFormFields(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _advanceType,
                decoration: _inputDecoration(context, '신청 구분'),
                items: const [
                  DropdownMenuItem(value: 'ADVANCE_PAY', child: Text('가지급금 (업무용)')),
                  DropdownMenuItem(value: 'PREPAYMENT', child: Text('선급금 (계약상)')),
                  DropdownMenuItem(value: 'IMPREST_FUND', child: Text('전도금 (상비운영비)')),
                  DropdownMenuItem(value: 'EVENT_FUND', child: Text('행사/프로젝트 진행비')),
                  DropdownMenuItem(value: 'OTHER', child: Text('기타 선급금')),
                ],
                onChanged: (v) => setState(() => _advanceType = v ?? 'ADVANCE_PAY'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _paymentDueDate ?? DateTime.now(),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _paymentDueDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _paymentDueDate != null ? '지급요청: ${_paymentDueDate!.toIso8601String().split('T').first}' : '지급요청일 선택',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _amountController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '신청 금액 (원)'),
                onChanged: (_) => _updateRoutePreview(),
                validator: (v) => (v == null || v.trim().isEmpty) ? '신청 금액을 입력하세요' : null,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _settlementDueDate ?? DateTime.now().add(const Duration(days: 14)),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _settlementDueDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _settlementDueDate != null ? '정산예정: ${_settlementDueDate!.toIso8601String().split('T').first}' : '정산예정일 선택',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              flex: 3,
              child: DropdownButtonFormField<String>(
                value: _receiverType,
                decoration: _inputDecoration(context, '수령 대상'),
                items: const [
                  DropdownMenuItem(value: 'EMPLOYEE', child: Text('임직원 계좌')),
                  DropdownMenuItem(value: 'VENDOR', child: Text('거래처 지급')),
                  DropdownMenuItem(value: 'OTHER', child: Text('기타 계좌')),
                ],
                onChanged: (v) => setState(() => _receiverType = v ?? 'EMPLOYEE'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              flex: 3,
              child: TextFormField(
                controller: _bankNameController,
                decoration: _inputDecoration(context, '은행명'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              flex: 4,
              child: TextFormField(
                controller: _accountNumberController,
                decoration: _inputDecoration(context, '계좌번호'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _accountHolderController,
          decoration: _inputDecoration(context, '예금주명'),
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _purposeController,
          maxLines: 4,
          decoration: _inputDecoration(context, '사용 목적 및 세부 집행 계획 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '사용 목적을 입력하세요' : null,
        ),
        const SizedBox(height: 10),

        CheckboxListTile(
          value: _settlementPromise,
          onChanged: (v) => setState(() => _settlementPromise = v ?? true),
          title: const Text(
            '정산 예정일까지 영수증 증빙을 첨부하여 전액 정산할 것을 확약합니다.',
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
          ),
          controlAffinity: ListTileControlAffinity.leading,
          contentPadding: EdgeInsets.zero,
        ),
        const SizedBox(height: 6),

        TextFormField(
          controller: _noteController,
          decoration: _inputDecoration(context, '비고 / 특이사항'),
        ),
      ],
    );
  }

  Widget _buildContractFormFields(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _contractType,
                decoration: _inputDecoration(context, '계약 구분'),
                items: const [
                  DropdownMenuItem(value: 'CONSTRUCTION', child: Text('공사 도급/하도급')),
                  DropdownMenuItem(value: 'SERVICE', child: Text('용역/설계/감리/PM')),
                  DropdownMenuItem(value: 'PURCHASE', child: Text('물품/자재 구매')),
                  DropdownMenuItem(value: 'LEASE', child: Text('부동산 임대차')),
                  DropdownMenuItem(value: 'MOU_NDA', child: Text('MOU/NDA')),
                  DropdownMenuItem(value: 'OTHER', child: Text('기타 일반계약')),
                ],
                onChanged: (v) => setState(() => _contractType = v ?? 'SERVICE'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _contractKind,
                decoration: _inputDecoration(context, '계약 형태'),
                items: const [
                  DropdownMenuItem(value: 'NEW', child: Text('신규 계약')),
                  DropdownMenuItem(value: 'CHANGE', child: Text('변경(증/감액/연장)')),
                  DropdownMenuItem(value: 'RENEWAL', child: Text('갱신/연장')),
                ],
                onChanged: (v) => setState(() => _contractKind = v ?? 'NEW'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _contractNameController,
          decoration: _inputDecoration(context, '계약 건명 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '계약 건명을 입력하세요' : null,
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              flex: 4,
              child: TextFormField(
                controller: _vendorController,
                decoration: _inputDecoration(context, '상대방 상호 (필수)'),
                validator: (v) => (v == null || v.trim().isEmpty) ? '상대방 상호를 입력하세요' : null,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              flex: 3,
              child: TextFormField(
                controller: _contractorCeoController,
                decoration: _inputDecoration(context, '대표자명'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _contractorRegNumberController,
                decoration: _inputDecoration(context, '사업자등록번호'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _contractorContactController,
                decoration: _inputDecoration(context, '담당자 / 연락처'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              flex: 4,
              child: TextFormField(
                controller: _amountController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '총 계약 금액 (원)'),
                onChanged: (_) => _updateRoutePreview(),
                validator: (v) => (v == null || v.trim().isEmpty) ? '계약 금액을 입력하세요' : null,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              flex: 3,
              child: DropdownButtonFormField<String>(
                value: _vatType,
                decoration: _inputDecoration(context, '부가세 구분'),
                items: const [
                  DropdownMenuItem(value: 'EXCLUDED', child: Text('VAT 별도')),
                  DropdownMenuItem(value: 'INCLUDED', child: Text('VAT 포함')),
                  DropdownMenuItem(value: 'ZERO_TAX', child: Text('면세/영세')),
                ],
                onChanged: (v) => setState(() => _vatType = v ?? 'EXCLUDED'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _startDate ?? DateTime.now(),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _startDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _startDate != null ? '시작: ${_startDate!.toIso8601String().split('T').first}' : '시작일 선택',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _endDate ?? DateTime.now().add(const Duration(days: 365)),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _endDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _endDate != null ? '종료: ${_endDate!.toIso8601String().split('T').first}' : '종료일 선택',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _paymentTermsController,
          decoration: _inputDecoration(context, '대금 지급 조건 (예: 계약금 10%, 잔금 90%)'),
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _warrantyTermsController,
          decoration: _inputDecoration(context, '이행 / 하자 보증 조건 (예: 하자보증 5%)'),
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _purposeController,
          maxLines: 4,
          decoration: _inputDecoration(context, '계약 체결 목적 및 추진 배경 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '체결 목적을 입력하세요' : null,
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _specialTermsController,
          maxLines: 2,
          decoration: _inputDecoration(context, '주요 특약 사항 / 비고'),
        ),
      ],
    );
  }

  Widget _buildContractChangeFormFields(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _contractChangeType,
                decoration: _inputDecoration(context, '변경/해지 구분'),
                items: const [
                  DropdownMenuItem(value: 'COMPREHENSIVE', child: Text('복합변경 (금액+기간)')),
                  DropdownMenuItem(value: 'AMOUNT_CHANGE', child: Text('금액 변경 (증/감액)')),
                  DropdownMenuItem(value: 'PERIOD_CHANGE', child: Text('기간 변경 (공기연장)')),
                  DropdownMenuItem(value: 'SCOPE_CHANGE', child: Text('과업/조건 변경')),
                  DropdownMenuItem(value: 'TERMINATION', child: Text('중도 해지 / 합의 해제')),
                ],
                onChanged: (v) => setState(() => _contractChangeType = v ?? 'COMPREHENSIVE'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _vendorController,
                decoration: _inputDecoration(context, '계약 상대방 상호 (필수)'),
                validator: (v) => (v == null || v.trim().isEmpty) ? '상대방 상호를 입력하세요' : null,
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _origContractNameController,
          decoration: _inputDecoration(context, '원 계약 건명 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '원 계약 건명을 입력하세요' : null,
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _origAmountController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '원 계약 금액 (원)'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _origEndDate ?? DateTime.now(),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _origEndDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _origEndDate != null ? '원종료일: ${_origEndDate!.toIso8601String().split('T').first}' : '원종료일 선택',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        if (_contractChangeType != 'TERMINATION') ...[
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _changeAmountController,
                  keyboardType: TextInputType.number,
                  decoration: _inputDecoration(context, '증감 금액 (+/- 원)'),
                  onChanged: (_) => _updateRoutePreview(),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: OutlinedButton(
                  onPressed: () async {
                    final d = await showDatePicker(
                      context: context,
                      initialDate: _endDate ?? DateTime.now().add(const Duration(days: 365)),
                      firstDate: DateTime(2020),
                      lastDate: DateTime(2035),
                    );
                    if (d != null) setState(() => _endDate = d);
                  },
                  style: OutlinedButton.styleFrom(
                    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                    side: BorderSide(color: context.colors.border),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                  child: Text(
                    _endDate != null ? '변경종료: ${_endDate!.toIso8601String().split('T').first}' : '변경종료일 선택',
                    style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          TextFormField(
            controller: _periodChangeDescController,
            decoration: _inputDecoration(context, '연장 / 단축 사유 및 일수 (예: 30일 공기연장)'),
          ),
          const SizedBox(height: 10),
        ] else ...[
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () async {
                    final d = await showDatePicker(
                      context: context,
                      initialDate: _terminationDate ?? DateTime.now(),
                      firstDate: DateTime(2020),
                      lastDate: DateTime(2035),
                    );
                    if (d != null) setState(() => _terminationDate = d);
                  },
                  style: OutlinedButton.styleFrom(
                    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                    side: BorderSide(color: context.colors.border),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                  child: Text(
                    _terminationDate != null ? '해지일: ${_terminationDate!.toIso8601String().split('T').first}' : '해지일 선택',
                    style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextFormField(
                  controller: _settlementAmountController,
                  keyboardType: TextInputType.number,
                  decoration: _inputDecoration(context, '타절 정산금액 (원)'),
                  onChanged: (_) => _updateRoutePreview(),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          TextFormField(
            controller: _penaltyTermsController,
            decoration: _inputDecoration(context, '위약금 / 보증금 몰취 내역'),
          ),
          const SizedBox(height: 10),
        ],

        TextFormField(
          controller: _purposeController,
          maxLines: 4,
          decoration: _inputDecoration(context, '계약 변경 / 해지 사유 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '변경/해지 사유를 입력하세요' : null,
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _subsequentPlanController,
          maxLines: 2,
          decoration: _inputDecoration(context, '향후 후속 조치 계획 및 비고'),
        ),
      ],
    );
  }

  Widget _buildLegalReviewFormFields(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _legalReviewType,
                decoration: _inputDecoration(context, '검토 분야'),
                items: const [
                  DropdownMenuItem(value: 'CONTRACT_REVIEW', child: Text('계약서/협약서 검토')),
                  DropdownMenuItem(value: 'LITIGATION_DISPUTE', child: Text('소송/분쟁 대응')),
                  DropdownMenuItem(value: 'REGULATORY_COMPLIANCE', child: Text('법령해석/인허가')),
                  DropdownMenuItem(value: 'INTERNAL_RULE', child: Text('사규/내부규정')),
                  DropdownMenuItem(value: 'CLAIM_NOTICE', child: Text('내용증명/공문')),
                  DropdownMenuItem(value: 'OTHER', child: Text('기타 법률자문')),
                ],
                onChanged: (v) => setState(() => _legalReviewType = v ?? 'CONTRACT_REVIEW'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _legalUrgency,
                decoration: _inputDecoration(context, '긴급도'),
                items: const [
                  DropdownMenuItem(value: 'NORMAL', child: Text('보통 (3~5일)')),
                  DropdownMenuItem(value: 'URGENT', child: Text('긴급 (1~2일)')),
                  DropdownMenuItem(value: 'VERY_URGENT', child: Text('당일 긴급')),
                ],
                onChanged: (v) => setState(() => _legalUrgency = v ?? 'NORMAL'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              flex: 4,
              child: TextFormField(
                controller: _contractNameController,
                decoration: _inputDecoration(context, '의뢰 건명 (필수)'),
                validator: (v) => (v == null || v.trim().isEmpty) ? '의뢰 건명을 입력하세요' : null,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              flex: 3,
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _reviewDueDate ?? DateTime.now().add(const Duration(days: 5)),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _reviewDueDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _reviewDueDate != null ? '희망: ${_reviewDueDate!.toIso8601String().split('T').first}' : '회신희망일',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _vendorController,
                decoration: _inputDecoration(context, '상대방 (당사자)'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _amountController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '관련 가액 / 분쟁금액 (원)'),
                onChanged: (_) => _updateRoutePreview(),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _generalContentController,
          maxLines: 3,
          decoration: _inputDecoration(context, '사실관계 및 검토 배경 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '사실관계 및 배경을 입력하세요' : null,
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _keyIssuesController,
          maxLines: 4,
          decoration: _inputDecoration(context, '주요 쟁점 사항 (필수: 조항별 쟁점 기술)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '주요 쟁점 사항을 입력하세요' : null,
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _noteController,
          decoration: _inputDecoration(context, '첨부 서류 목록 / 비고'),
        ),
      ],
    );
  }

  Widget _buildBusinessReviewFormFields(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              flex: 4,
              child: TextFormField(
                controller: _contractNameController,
                decoration: _inputDecoration(context, '사업명 (프로젝트명 - 필수)'),
                validator: (v) => (v == null || v.trim().isEmpty) ? '사업명을 입력하세요' : null,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              flex: 3,
              child: DropdownButtonFormField<String>(
                value: _bizType,
                decoration: _inputDecoration(context, '사업 유형'),
                items: const [
                  DropdownMenuItem(value: 'DEV_SELF', child: Text('자체 개발사업')),
                  DropdownMenuItem(value: 'DEV_TRUST', child: Text('토지신탁')),
                  DropdownMenuItem(value: 'CONTRACT_CIVIL', child: Text('단순 도급(시공)')),
                  DropdownMenuItem(value: 'REDEVELOPMENT', child: Text('재개발/재건축')),
                  DropdownMenuItem(value: 'PF_INVEST', child: Text('지분투자/공동')),
                  DropdownMenuItem(value: 'OTHER', child: Text('기타 신규')),
                ],
                onChanged: (v) => setState(() => _bizType = v ?? 'DEV_SELF'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              flex: 4,
              child: TextFormField(
                controller: _locationController,
                decoration: _inputDecoration(context, '사업 부지 위치 (필수)'),
                validator: (v) => (v == null || v.trim().isEmpty) ? '부지 위치를 입력하세요' : null,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              flex: 3,
              child: TextFormField(
                controller: _buildingScaleController,
                decoration: _inputDecoration(context, '건축 규모/세대수'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _landAreaController,
                decoration: _inputDecoration(context, '대지면적 (㎡)'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _grossFloorAreaController,
                decoration: _inputDecoration(context, '연면적 (㎡)'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _totalRevenueController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '총 분양/매출 수입 (원)'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _totalCostController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '총 사업비 (지출 - 원)'),
                onChanged: (_) => _updateRoutePreview(),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _requiredEquityController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '자기자본 (Equity - 원)'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _pfLoanAmountController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, 'PF 차입금 (원)'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _startDate ?? DateTime.now().add(const Duration(days: 90)),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _startDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _startDate != null ? '착공: ${_startDate!.toIso8601String().split('T').first}' : '착공/분양일',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  final d = await showDatePicker(
                    context: context,
                    initialDate: _completionDate ?? DateTime.now().add(const Duration(days: 730)),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (d != null) setState(() => _completionDate = d);
                },
                style: OutlinedButton.styleFrom(
                  shape: const RoundedRectangleBorder(borderRadius: BorderRadius.zero),
                  side: BorderSide(color: context.colors.border),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: Text(
                  _completionDate != null ? '준공: ${_completionDate!.toIso8601String().split('T').first}' : '준공/입주일',
                  style: TextStyle(fontSize: 12, color: context.colors.textPrimary),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _marketAnalysisController,
          maxLines: 2,
          decoration: _inputDecoration(context, '입지 및 분양성 요약'),
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _riskFactorsController,
          maxLines: 2,
          decoration: _inputDecoration(context, '주요 리스크 요인 및 대책'),
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _purposeController,
          maxLines: 4,
          decoration: _inputDecoration(context, '종합 검토의견 및 추진 전략 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '종합 검토의견을 입력하세요' : null,
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _noteController,
          decoration: _inputDecoration(context, '첨부 서류 목록 / 비고'),
        ),
      ],
    );
  }

  Widget _buildBusinessApprovalFormFields(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              flex: 4,
              child: TextFormField(
                controller: _contractNameController,
                decoration: _inputDecoration(context, '사업명 (승인 건명 - 필수)'),
                validator: (v) => (v == null || v.trim().isEmpty) ? '사업명을 입력하세요' : null,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              flex: 3,
              child: DropdownButtonFormField<String>(
                value: _bizApprovalType,
                decoration: _inputDecoration(context, '승인 의결 구분'),
                items: const [
                  DropdownMenuItem(value: 'NEW_LAUNCH', child: Text('사업 론칭 승인')),
                  DropdownMenuItem(value: 'LAND_ACQUISITION', child: Text('토지매매/계약금')),
                  DropdownMenuItem(value: 'SPC_ESTABLISH', child: Text('SPC/PFV 설립')),
                  DropdownMenuItem(value: 'PF_EXECUTION', child: Text('본PF약정/인출')),
                  DropdownMenuItem(value: 'CONSTRUCTION_START', child: Text('시공계약/착공')),
                  DropdownMenuItem(value: 'OTHER', child: Text('기타 승인')),
                ],
                onChanged: (v) => setState(() => _bizApprovalType = v ?? 'NEW_LAUNCH'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              flex: 4,
              child: TextFormField(
                controller: _locationController,
                decoration: _inputDecoration(context, '사업 부지 위치 (필수)'),
                validator: (v) => (v == null || v.trim().isEmpty) ? '부지 위치를 입력하세요' : null,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              flex: 3,
              child: TextFormField(
                controller: _bizScaleSummaryController,
                decoration: _inputDecoration(context, '사업 규모 / 용도'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _requestedAmountController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '금회 승인요청액 (필수 - 원)'),
                onChanged: (_) => _updateRoutePreview(),
                validator: (v) => (v == null || v.trim().isEmpty) ? '승인요청액을 입력하세요' : null,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _totalProjectCostController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '전체 총사업비 (원)'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _totalExpectedRevenueController,
                keyboardType: TextInputType.number,
                decoration: _inputDecoration(context, '예상 총분양수입 (원)'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _pmLeadController,
                decoration: _inputDecoration(context, '총괄 PM / 담당부서'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _budgetUsagePlanController,
          decoration: _inputDecoration(context, '금회 승인예산 세부 집행 내역 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '예산 집행 내역을 입력하세요' : null,
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _resolutionMattersController,
          maxLines: 4,
          decoration: _inputDecoration(context, '주요 승인 의결 요청 사항 (필수: 안건별 기술)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '승인 의결 사항을 입력하세요' : null,
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _targetScheduleController,
          decoration: _inputDecoration(context, '향후 주요 추진 일정 (마일스톤)'),
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _expectedEffectsController,
          maxLines: 2,
          decoration: _inputDecoration(context, '기대 효과 및 주요 리스크 대책'),
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _noteController,
          decoration: _inputDecoration(context, '첨부 서류 목록 / 비고'),
        ),
      ],
    );
  }

  Widget _buildProjectDecisionFormFields(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              flex: 4,
              child: DropdownButtonFormField<String>(
                value: _projectDecisionType,
                decoration: _inputDecoration(context, '현안 분야'),
                items: const [
                  DropdownMenuItem(value: 'DESIGN_SPEC', child: Text('설계변경/스펙결정')),
                  DropdownMenuItem(value: 'SALES_PRICING', child: Text('분양가/분양조건')),
                  DropdownMenuItem(value: 'CONSTRUCTION_METHOD', child: Text('시공공법/자재선정')),
                  DropdownMenuItem(value: 'FINANCIAL_STRUCTURING', child: Text('금융구조/PF변경')),
                  DropdownMenuItem(value: 'CLAIM_DISPUTE', child: Text('민원/분쟁대응')),
                  DropdownMenuItem(value: 'CONTRACTOR_TERMINATION', child: Text('업체선정/타절')),
                  DropdownMenuItem(value: 'OTHER', child: Text('기타 의사결정')),
                ],
                onChanged: (v) => setState(() => _projectDecisionType = v ?? 'DESIGN_SPEC'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              flex: 3,
              child: DropdownButtonFormField<String>(
                value: _decisionUrgency,
                decoration: _inputDecoration(context, '긴급도'),
                items: const [
                  DropdownMenuItem(value: 'NORMAL', child: Text('보통')),
                  DropdownMenuItem(value: 'URGENT', child: Text('긴급(금주내)')),
                  DropdownMenuItem(value: 'CRITICAL', child: Text('즉시 결정')),
                ],
                onChanged: (v) => setState(() => _decisionUrgency = v ?? 'NORMAL'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              flex: 4,
              child: TextFormField(
                controller: _docNumberExtController,
                decoration: _inputDecoration(context, '심의 안건명 (필수)'),
                validator: (v) => (v == null || v.trim().isEmpty) ? '안건명을 입력하세요' : null,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              flex: 3,
              child: InkWell(
                onTap: () async {
                  final picked = await showDatePicker(
                    context: context,
                    initialDate: _decisionDueDate ?? DateTime.now().add(const Duration(days: 7)),
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2035),
                  );
                  if (picked != null) setState(() => _decisionDueDate = picked);
                },
                child: InputDecorator(
                  decoration: _inputDecoration(context, '결정 목표일'),
                  child: Text(
                    _decisionDueDate != null ? _decisionDueDate!.toIso8601String().split('T').first : '날짜 선택',
                    style: TextStyle(fontSize: 13, color: context.colors.textPrimary),
                  ),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _amountController,
          keyboardType: TextInputType.number,
          decoration: _inputDecoration(context, '재무적 영향 / 증감 예산 (원, 없으면 0)'),
          onChanged: (_) => _updateRoutePreview(),
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _generalContentController,
          maxLines: 3,
          decoration: _inputDecoration(context, '현안 배경 및 문제점 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '현안 배경 및 문제점을 입력하세요' : null,
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _option1Controller,
          maxLines: 2,
          decoration: _inputDecoration(context, '대안 1 (원안: 내용, 장단점, 비용, 공기)'),
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _option2Controller,
          maxLines: 2,
          decoration: _inputDecoration(context, '대안 2 (추천안/변경안: 내용, 장단점, 비용, 공기)'),
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _option3Controller,
          maxLines: 2,
          decoration: _inputDecoration(context, '대안 3 (선택 대안 - 선택사항)'),
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _purposeController,
          maxLines: 3,
          decoration: _inputDecoration(context, '주관부서 최종 추천안 및 선정 사유 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '주관부서 추천안을 입력하세요' : null,
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _actionPlanController,
          decoration: _inputDecoration(context, '향후 조치 계획'),
        ),
        const SizedBox(height: 10),

        TextFormField(
          controller: _noteController,
          decoration: _inputDecoration(context, '첨부 서류 목록 / 비고'),
        ),
      ],
    );
  }

  Widget _buildGeneralFormFields(BuildContext context) {
    return Column(
      children: [
        TextFormField(
          controller: _purposeController,
          decoration: _inputDecoration(context, '품의 목적 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '품의 목적을 입력하세요' : null,
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _scheduleController,
                decoration: _inputDecoration(context, '추진 일정 / 기간'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _budgetAccount,
                decoration: _inputDecoration(context, '예산 과목'),
                items: const [
                  DropdownMenuItem(value: 'NONE', child: Text('예산 비소요')),
                  DropdownMenuItem(value: 'GENERAL_EXPENSE', child: Text('일반관리비')),
                  DropdownMenuItem(value: 'PROJECT_COST', child: Text('사업비')),
                  DropdownMenuItem(value: 'OUTSOURCING', child: Text('외주용역비')),
                  DropdownMenuItem(value: 'MARKETING', child: Text('홍보마케팅비')),
                  DropdownMenuItem(value: 'ASSET_PURCHASE', child: Text('자산취득비')),
                  DropdownMenuItem(value: 'OTHER', child: Text('기타 예산')),
                ],
                onChanged: (v) => setState(() => _budgetAccount = v ?? 'GENERAL_EXPENSE'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _amountController,
          keyboardType: TextInputType.number,
          decoration: _inputDecoration(context, '소요 예산 / 예상 금액 (원) - 결재선 자동반영'),
          onChanged: (_) => _updateRoutePreview(),
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _generalContentController,
          maxLines: 5,
          decoration: _inputDecoration(context, '세부 품의 내용 (필수)'),
          validator: (v) => (v == null || v.trim().isEmpty) ? '세부 품의 내용을 입력하세요' : null,
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _expectedEffectController,
          maxLines: 2,
          decoration: _inputDecoration(context, '기대 효과 (선택)'),
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _noteController,
          decoration: _inputDecoration(context, '비고 / 특이사항 (선택)'),
        ),
      ],
    );
  }

  Widget _buildRoutePreviewWidget(BuildContext context) {
    if (_isPreviewLoading) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 12),
        child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
      );
    }
    if (_selectedDocType == null) {
      return Text('문서 유형을 선택하면 결재선이 자동 계산됩니다.',
          style: TextStyle(fontSize: 12, color: context.colors.textMuted));
    }
    if (_previewSteps.isEmpty) {
      return Text('자동 생성된 결재선이 없습니다. (단독 전결 또는 즉시 승인)',
          style: TextStyle(fontSize: 12, color: context.colors.textMuted));
    }

    return Column(
      children: [
        for (int i = 0; i < _previewSteps.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: Row(
              children: [
                Container(
                  width: 20,
                  height: 20,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: context.colors.accentApproval.withAlpha(30),
                    border: Border.all(color: context.colors.accentApproval, width: 0.8),
                  ),
                  child: Text('${i + 1}',
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: context.colors.accentApprovalDeep)),
                ),
                const SizedBox(width: 8),
                Text(_previewSteps[i].roleLabel,
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: context.colors.textPrimary)),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    _previewSteps[i].approvers.map((u) => u.username).join(', '),
                    style: TextStyle(fontSize: 11.5, color: context.colors.textSecond),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildSectionCard(
    BuildContext context, {
    required String title,
    required IconData icon,
    required Widget child,
    Widget? action,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: context.colors.bgCard,
        borderRadius: BorderRadius.zero,
        border: Border.all(color: context.colors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 15, color: context.colors.accentApproval),
              const SizedBox(width: 6),
              Text(title, style: AppTextStyles.titleSm.copyWith(fontWeight: FontWeight.w700)),
              const Spacer(),
              if (action != null) action,
            ],
          ),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }

  InputDecoration _inputDecoration(BuildContext context, String label) {
    return InputDecoration(
      labelText: label,
      labelStyle: TextStyle(fontSize: 12.5, color: context.colors.textMuted),
      filled: true,
      fillColor: context.colors.bgSurface,
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: context.colors.border, width: 0.8),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: context.colors.border, width: 0.8),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.zero,
        borderSide: BorderSide(color: context.colors.accentApproval, width: 1.2),
      ),
    );
  }
}
