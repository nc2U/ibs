export declare interface SalesBillIssue {
  pk: number | null
  project: number | null
  now_payment_order: number | null
  host_name: string
  host_tel: string
  agency: string
  agency_tel: string
  bank_account1: string
  bank_number1: string
  bank_host1: string
  bank_account2: string
  bank_number2: string
  bank_host2: string
  zipcode: string
  address1: string
  address2: string
  address3: string
  title: string
  content: string
  creator?: {
    pk: number
    username: string
  }
  updated?: string
}

// SMS/MMS/카카오톡 메시지 관련 타입
export declare interface SMSMessage {
  message_type?: 'SMS' | 'LMS' | 'AUTO'
  message: string
  title?: string
  sender_number: string
  recipients: string[]
  scheduled_send?: boolean
  schedule_date?: string
  schedule_time?: string
  use_v2_api?: boolean
  company_id?: string
}

export declare interface MMSMessage extends SMSMessage {
  image: File
}

export declare interface KakaoRecipient {
  phone: string
  template_param?: string[]
}

export declare interface KakaoMessage {
  template_code: string
  recipients: KakaoRecipient[]
  sender_number: string
  scheduled_send?: boolean
  schedule_date?: string
  schedule_time?: string
  re_send?: boolean
  resend_type?: 'Y' | 'N'
  resend_title?: string
  resend_content?: string
}

export declare interface SendHistoryParams {
  company_id: string
  start_date: string
  end_date: string
  request_no?: string
  page_num?: number
  page_size?: number
  phone?: string
}

export declare interface SendHistoryItem {
  requestNo: string
  companyid: string
  msgType: 'SMS' | 'LMS' | 'MMS'
  phone: string
  callback: string
  sendStatusCode: string
  sendStatusMessage?: string
  sendDate: string
}

export declare interface SendHistoryResponse {
  resultCode: number
  message: string
  totalCount: number
  list: SendHistoryItem[]
}

export declare interface BalanceResponse {
  code: number
  message: string
  charge: number
}

export declare interface SMSResponse {
  resultCode: number
  message: string
  requestNo: string | null
  msgType: 'SMS' | 'LMS' | 'MMS'
}

export declare interface KakaoResponse {
  code: number
  message: string
  success: number
  fail: number
}

// 메시지 템플릿 관련 타입
export declare interface MessageTemplate {
  id: number
  title: string
  message_type: 'SMS' | 'LMS' | 'MMS'
  content: string
  variables?: string[]
  is_active: boolean
  created_by?: number
  created_at: string
  updated_at: string
}

// 메시지 발송 기록 관련 타입
export declare interface MessageSendHistory {
  id: number
  message_type: 'SMS' | 'LMS' | 'MMS' | 'KAKAO'
  sender_number: string
  message_content: string
  title: string
  recipients: string[]
  recipient_count: number
  sent_at: string
  request_no: string
  company_id: string
  project: number | null
  scheduled_send: boolean
  schedule_datetime: string | null
  sent_by: {
    pk: number
    username: string
  } | null
  created: string
}

export declare interface MessageSendHistoryList {
  id: number
  message_type: 'SMS' | 'LMS' | 'MMS' | 'KAKAO'
  sender_number: string
  title: string
  message_content: string
  recipient_count: number
  sent_at: string
  request_no: string
  scheduled_send: boolean
  sent_by: {
    pk: number
    username: string
  } | null
  created: string
}

export declare interface HistoryListParams {
  start_date?: string
  end_date?: string
  message_type?: string
  sender_number?: string
  project?: number
  page?: number
  page_size?: number
  ordering?: string
}

export declare interface HistoryListResponse {
  count: number
  next: string | null
  previous: string | null
  results: MessageSendHistoryList[]
}
