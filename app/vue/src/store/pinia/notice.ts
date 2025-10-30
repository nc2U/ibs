import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { message, errorHandle } from '@/utils/helper'
import type {
  SalesBillIssue,
  SMSMessage,
  MMSMessage,
  KakaoMessage,
  SendHistoryParams,
  SendHistoryResponse,
  BalanceResponse,
  SMSResponse,
  KakaoResponse,
  MessageTemplate,
  MessageSendHistory,
  HistoryListParams,
  HistoryListResponse,
} from '@/store/types/notice'

export const useNotice = defineStore('notice', () => {
  // state & getters
  const loading = ref<boolean>(false)
  const billIssue = ref<SalesBillIssue | null>(null)
  const sendHistory = ref<SendHistoryResponse | null>(null)
  const balance = ref<number>(0)
  const senderNumbers = ref<Array<{ id: number; phone_number: string; label: string }>>([])
  const messageTemplates = ref<MessageTemplate[]>([])
  const messageSendHistory = ref<HistoryListResponse | null>(null)
  const currentHistory = ref<MessageSendHistory | null>(null)

  // Sales Bill Issue actions
  const fetchSalesBillIssue = (pk: number) =>
    api
      .get(`/sales-bill-issue/${pk}/`)
      .then(res => (billIssue.value = res.data))
      .catch(err => {
        billIssue.value = null
        console.log(err)
      })

  const createSalesBillIssue = (payload: SalesBillIssue) =>
    api
      .post('/sales-bill-issue/', payload)
      .then(() => message())
      .catch(err => errorHandle(err.response.data))

  const patchSalesBillIssue = (payload: SalesBillIssue) =>
    api
      .patch(`/sales-bill-issue/${payload.pk}/`, payload)
      .then(() => message())
      .catch(err => errorHandle(err.response.data))

  const updateSalesBillIssue = (payload: SalesBillIssue) =>
    api
      .put(`/sales-bill-issue/${payload.pk}/`, payload)
      .then(() => message())
      .catch(err => errorHandle(err.response.data))

  const deleteSalesBillIssue = (pk: number) =>
    api
      .delete(`/sales-bill-issue/${pk}/`)
      .then(() => message('warning', '', '해당 오브젝트가 삭제되었습니다.'))
      .catch(err => errorHandle(err.response.data))

  // SMS/LMS 발송
  const sendSMS = async (payload: SMSMessage): Promise<SMSResponse> => {
    loading.value = true
    try {
      const response = await api.post<SMSResponse>('/messages/send-sms/', payload)

      if (response.data.resultCode !== 0) {
        message('danger', '발송 실패', response.data.message || '알 수 없는 오류가 발생했습니다.')
        return response.data
      }

      // company_id가 없으면 즉시 경고 메시지 (전송 내역 조회 불가)
      if (!payload.company_id) {
        message(
          'warning',
          '발송 요청 접수',
          'SMS 발송 요청이 접수되었습니다. 조직 구분 ID가 없어 발송 결과를 확인할 수 없습니다.',
        )
        return response.data
      }

      // API 접수는 성공했으나, 실제 발송 결과는 비동기로 처리됨
      // 2-3초 후 전송 내역을 조회하여 실제 발송 상태 확인
      message('info', '', '발송 요청이 접수되었습니다. 실제 발송 결과를 확인 중...')

      // 2.5초 대기 (iwinv API가 실제 발송 처리할 시간)
      await new Promise(resolve => setTimeout(resolve, 2500))

      // 전송 내역 조회 (오늘 날짜, requestNo로 필터링)
      const today = new Date()
      const historyParams = {
        company_id: payload.company_id,
        start_date: today.toISOString().split('T')[0],
        end_date: today.toISOString().split('T')[0],
        request_no: response.data.requestNo,
        page_num: 1,
        page_size: 10,
      }

      const historyResponse = await api.get<SendHistoryResponse>('/messages/send-history/', {
        params: historyParams,
      })

      if (historyResponse.data.resultCode === 0 && historyResponse.data.list.length > 0) {
        // 같은 requestNo에 대해 여러 레코드가 있을 수 있음 (WAIT 상태와 최종 상태)
        // 최종 상태를 우선적으로 확인 (구분이 "API"인 것 또는 WAIT가 아닌 것)
        const records = historyResponse.data.list.filter(
          item => item.requestNo === response.data.requestNo,
        )

        // API 구분이 있는 것(최종 상태) 우선, 없으면 첫 번째 레코드
        const sendResult = records.find(item => item.sendStatusCode !== 'WAIT') || records[0]

        // 발송 상태 확인
        // '0', '06' = 성공
        // 'WAIT' = 대기 중
        // 그 외 = 실패
        if (sendResult.sendStatusCode === '0' || sendResult.sendStatusCode === '06') {
          message(
            'success',
            '발송 성공',
            `SMS가 성공적으로 발송되었습니다. (${payload.recipients.length}건)`,
          )
        } else if (sendResult.sendStatusCode === 'WAIT') {
          message(
            'info',
            '발송 대기 중',
            `SMS 발송이 접수되었습니다. 전송 처리 중입니다. (${payload.recipients.length}건)`,
          )
        } else {
          message(
            'danger',
            '발송 실패',
            sendResult.sendStatusMessage ||
              `발송에 실패했습니다. (코드: ${sendResult.sendStatusCode})`,
          )
        }
      } else {
        // 전송 내역 조회 실패 시 경고 메시지
        message(
          'warning',
          '발송 확인 필요',
          `발송 요청은 접수되었으나 결과 확인에 실패했습니다. (${historyResponse.data.message || '전송 내역을 확인해주세요.'})`,
        )
      }

      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || '발송 중 오류가 발생했습니다.'
      message('danger', '발송 실패', errorMsg)
      errorHandle(err.response?.data || { message: errorMsg })
      throw err
    } finally {
      loading.value = false
    }
  }

  // MMS 발송
  const sendMMS = async (payload: MMSMessage): Promise<SMSResponse> => {
    loading.value = true
    try {
      const formData = new FormData()
      formData.append('message', payload.message)
      formData.append('title', payload.title || '')
      formData.append('sender_number', payload.sender_number)

      // recipients는 배열이므로 각각 개별적으로 append (DRF가 배열로 인식)
      payload.recipients.forEach(phone => {
        formData.append('recipients', phone)
      })

      formData.append('image', payload.image)
      formData.append('scheduled_send', String(payload.scheduled_send || false))

      if (payload.company_id) formData.append('company_id', payload.company_id)
      if (payload.schedule_date) formData.append('schedule_date', payload.schedule_date)
      if (payload.schedule_time) formData.append('schedule_time', payload.schedule_time)
      if (payload.use_v2_api !== undefined)
        formData.append('use_v2_api', String(payload.use_v2_api))

      const response = await api.post<SMSResponse>('/messages/send-mms/', formData)

      if (response.data.resultCode === 0) {
        message('success', '', 'MMS가 성공적으로 발송되었습니다.')
      } else {
        message('danger', '발송 실패', response.data.message || '알 수 없는 오류가 발생했습니다.')
      }

      return response.data
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.detail || err.response?.data?.message || '발송 중 오류가 발생했습니다.'
      message('danger', '발송 실패', errorMsg)
      errorHandle(err.response?.data || { message: errorMsg })
      throw err
    } finally {
      loading.value = false
    }
  }

  // 카카오 알림톡 발송
  const sendKakao = async (payload: KakaoMessage): Promise<KakaoResponse> => {
    loading.value = true
    try {
      const response = await api.post<KakaoResponse>('/messages/send-kakao/', payload)

      if (response.data.code === 200) {
        message(
          'success',
          '',
          `카카오 알림톡이 성공적으로 발송되었습니다. (성공: ${response.data.success}건)`,
        )
      } else {
        message('danger', '발송 실패', response.data.message || '알 수 없는 오류가 발생했습니다.')
      }

      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || '발송 중 오류가 발생했습니다.'
      message('danger', '발송 실패', errorMsg)
      errorHandle(err.response?.data || { message: errorMsg })
      throw err
    } finally {
      loading.value = false
    }
  }

  // 전송 내역 조회
  const fetchSendHistory = async (params: SendHistoryParams): Promise<SendHistoryResponse> => {
    loading.value = true
    try {
      const response = await api.get<SendHistoryResponse>('/messages/send-history/', { params })

      if (response.data.resultCode === 0) sendHistory.value = response.data
      else message('warning', '', response.data.message)

      return response.data
    } catch (err: any) {
      errorHandle(err.response?.data || { message: '내역 조회 중 오류가 발생했습니다.' })
      throw err
    } finally {
      loading.value = false
    }
  }

  // 잔액 조회
  const fetchBalance = async (): Promise<number> => {
    loading.value = true
    try {
      const response = await api.get<BalanceResponse>('/messages/balance/')

      if (response.data.code === 0) balance.value = response.data.charge
      else message('warning', '', response.data.message)

      return response.data.charge
    } catch (err: any) {
      errorHandle(err.response?.data || { message: '잔액 조회 중 오류가 발생했습니다.' })
      throw err
    } finally {
      loading.value = false
    }
  }

  // 에러 코드 조회
  const fetchErrorCodes = async (): Promise<{
    sms_error_codes: Record<string, string>
    kakao_error_codes: Record<string, string>
  }> => {
    try {
      const response = await api.get('/messages/error-codes/')
      return response.data
    } catch (err: any) {
      errorHandle(err.response?.data || { message: '에러 코드 조회 중 오류가 발생했습니다.' })
      throw err
    }
  }

  // 등록된 발신번호 목록 조회
  const fetchSenderNumbers = async () => {
    loading.value = true
    try {
      const response = await api.get('/registered-sender-numbers/')
      // DRF pagination response: { count, next, previous, results }
      const data = response.data.results || response.data
      senderNumbers.value = Array.isArray(data) ? data : []
      return response.data
    } catch (err: any) {
      senderNumbers.value = [] // Ensure it remains an array on error
      errorHandle(err.response?.data || { message: '발신번호 목록 조회 중 오류가 발생했습니다.' })
      throw err
    } finally {
      loading.value = false
    }
  }

  // 발신번호 생성
  const createSenderNumber = async (payload: { phone_number: string; label: string }) => {
    loading.value = true
    try {
      const response = await api.post('/registered-sender-numbers/', payload)
      message('success', '', '발신번호가 등록되었습니다.')
      await fetchSenderNumbers() // 목록 갱신
      return response.data
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.phone_number?.[0] ||
        err.response?.data?.message ||
        '발신번호 등록 중 오류가 발생했습니다.'
      message('danger', '등록 실패', errorMsg)
      errorHandle(err.response?.data || { message: errorMsg })
      throw err
    } finally {
      loading.value = false
    }
  }

  // 발신번호 수정
  const updateSenderNumber = async (
    id: number,
    payload: { phone_number?: string; label?: string },
  ) => {
    loading.value = true
    try {
      const response = await api.patch(`/registered-sender-numbers/${id}/`, payload)
      message('success', '', '발신번호가 수정되었습니다.')
      await fetchSenderNumbers() // 목록 갱신
      return response.data
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.phone_number?.[0] ||
        err.response?.data?.message ||
        '발신번호 수정 중 오류가 발생했습니다.'
      message('danger', '수정 실패', errorMsg)
      errorHandle(err.response?.data || { message: errorMsg })
      throw err
    } finally {
      loading.value = false
    }
  }

  // 발신번호 삭제 (soft delete)
  const deleteSenderNumber = async (id: number) => {
    loading.value = true
    try {
      await api.delete(`/registered-sender-numbers/${id}/`)
      message('warning', '', '발신번호가 삭제되었습니다.')
      await fetchSenderNumbers() // 목록 갱신
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || '발신번호 삭제 중 오류가 발생했습니다.'
      message('danger', '삭제 실패', errorMsg)
      errorHandle(err.response?.data || { message: errorMsg })
      throw err
    } finally {
      loading.value = false
    }
  }

  // 메시지 템플릿 목록 조회
  const fetchMessageTemplates = async () => {
    loading.value = true
    try {
      const response = await api.get('/message-templates/')
      // DRF pagination response: { count, next, previous, results }
      const data = response.data.results || response.data
      messageTemplates.value = Array.isArray(data) ? data : []
      return response.data
    } catch (err: any) {
      messageTemplates.value = [] // Ensure it remains an array on error
      errorHandle(err.response?.data || { message: '템플릿 목록 조회 중 오류가 발생했습니다.' })
      throw err
    } finally {
      loading.value = false
    }
  }

  // 메시지 템플릿 생성
  const createMessageTemplate = async (payload: {
    title: string
    message_type: string
    content: string
    variables?: string[]
  }) => {
    loading.value = true
    try {
      const response = await api.post('/message-templates/', payload)
      message('success', '', '메시지 템플릿이 등록되었습니다.')
      await fetchMessageTemplates() // 목록 갱신
      return response.data
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.title?.[0] ||
        err.response?.data?.message ||
        '템플릿 등록 중 오류가 발생했습니다.'
      message('danger', '등록 실패', errorMsg)
      errorHandle(err.response?.data || { message: errorMsg })
      throw err
    } finally {
      loading.value = false
    }
  }

  // 메시지 템플릿 수정
  const updateMessageTemplate = async (id: number, payload: Partial<MessageTemplate>) => {
    loading.value = true
    try {
      const response = await api.patch(`/message-templates/${id}/`, payload)
      message('success', '', '메시지 템플릿이 수정되었습니다.')
      await fetchMessageTemplates() // 목록 갱신
      return response.data
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.title?.[0] ||
        err.response?.data?.message ||
        '템플릿 수정 중 오류가 발생했습니다.'
      message('danger', '수정 실패', errorMsg)
      errorHandle(err.response?.data || { message: errorMsg })
      throw err
    } finally {
      loading.value = false
    }
  }

  // 메시지 템플릿 삭제 (soft delete)
  const deleteMessageTemplate = async (id: number) => {
    loading.value = true
    try {
      await api.delete(`/message-templates/${id}/`)
      message('warning', '', '메시지 템플릿이 삭제되었습니다.')
      await fetchMessageTemplates() // 목록 갱신
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || '템플릿 삭제 중 오류가 발생했습니다.'
      message('danger', '삭제 실패', errorMsg)
      errorHandle(err.response?.data || { message: errorMsg })
      throw err
    } finally {
      loading.value = false
    }
  }

  // 수신자 그룹 조회
  const fetchRecipientGroup = async (projectId: number, groupType: string): Promise<any> => {
    loading.value = true
    try {
      const response = await api.get('/messages/recipient-groups/', {
        params: { project: projectId, group_type: groupType },
      })

      // 디버그 정보 출력
      if (response.data.debug) {
        console.log('🔍 백엔드 디버그 정보:', response.data.debug)
      }

      return response.data
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.error ||
        err.response?.data?.message ||
        '수신자 그룹 조회 중 오류가 발생했습니다.'
      message('danger', '조회 실패', errorMsg)
      errorHandle(err.response?.data || { message: errorMsg })
      throw err
    } finally {
      loading.value = false
    }
  }

  // 메시지 발송 기록 목록 조회
  const fetchMessageSendHistory = async (
    params: HistoryListParams,
  ): Promise<HistoryListResponse> => {
    loading.value = true
    try {
      const response = await api.get<HistoryListResponse>('/message-send-history/', { params })
      messageSendHistory.value = response.data
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || '발송 기록 조회 중 오류가 발생했습니다.'
      message('danger', '조회 실패', errorMsg)
      errorHandle(err.response?.data || { message: errorMsg })
      throw err
    } finally {
      loading.value = false
    }
  }

  // 메시지 발송 기록 상세 조회
  const fetchMessageSendHistoryDetail = async (id: number): Promise<MessageSendHistory> => {
    loading.value = true
    try {
      const response = await api.get<MessageSendHistory>(`/message-send-history/${id}/`)
      currentHistory.value = response.data
      return response.data
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || '발송 기록 상세 조회 중 오류가 발생했습니다.'
      message('danger', '조회 실패', errorMsg)
      errorHandle(err.response?.data || { message: errorMsg })
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    // state
    billIssue,
    sendHistory,
    balance,
    loading,
    senderNumbers,
    messageTemplates,
    messageSendHistory,
    currentHistory,

    // Sales Bill Issue actions
    fetchSalesBillIssue,
    createSalesBillIssue,
    patchSalesBillIssue,
    updateSalesBillIssue,
    deleteSalesBillIssue,

    // SMS/MMS/Kakao actions
    sendSMS,
    sendMMS,
    sendKakao,
    fetchSendHistory,
    fetchBalance,
    fetchErrorCodes,

    // Sender Number actions
    fetchSenderNumbers,
    createSenderNumber,
    updateSenderNumber,
    deleteSenderNumber,

    // Message Template actions
    fetchMessageTemplates,
    createMessageTemplate,
    updateMessageTemplate,
    deleteMessageTemplate,

    // Recipient Group actions
    fetchRecipientGroup,

    // Message Send History actions
    fetchMessageSendHistory,
    fetchMessageSendHistoryDetail,
  }
})
