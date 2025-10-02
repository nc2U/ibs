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
} from '@/store/types/notice'

export const useNotice = defineStore('notice', () => {
  // state & getters
  const billIssue = ref<SalesBillIssue | null>(null)
  const sendHistory = ref<SendHistoryResponse | null>(null)
  const balance = ref<number>(0)
  const loading = ref<boolean>(false)

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

      if (response.data.resultCode === 0) {
        message('success', '', 'SMS가 성공적으로 발송되었습니다.')
      } else {
        message('error', '', response.data.message)
      }

      return response.data
    } catch (err: any) {
      errorHandle(err.response?.data || { message: '발송 중 오류가 발생했습니다.' })
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
      formData.append('recipients', JSON.stringify(payload.recipients))
      formData.append('image', payload.image)
      formData.append('scheduled_send', String(payload.scheduled_send || false))

      if (payload.schedule_date) formData.append('schedule_date', payload.schedule_date)
      if (payload.schedule_time) formData.append('schedule_time', payload.schedule_time)
      if (payload.use_v2_api !== undefined) formData.append('use_v2_api', String(payload.use_v2_api))

      const response = await api.post<SMSResponse>('/messages/send-mms/', formData)

      if (response.data.resultCode === 0) {
        message('success', '', 'MMS가 성공적으로 발송되었습니다.')
      } else {
        message('error', '', response.data.message)
      }

      return response.data
    } catch (err: any) {
      errorHandle(err.response?.data || { message: '발송 중 오류가 발생했습니다.' })
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
        message('success', '', `카카오 알림톡이 성공적으로 발송되었습니다. (성공: ${response.data.success}건)`)
      } else {
        message('error', '', response.data.message)
      }

      return response.data
    } catch (err: any) {
      errorHandle(err.response?.data || { message: '발송 중 오류가 발생했습니다.' })
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

      if (response.data.resultCode === 0) {
        sendHistory.value = response.data
      } else {
        message('error', '', response.data.message)
      }

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

      if (response.data.code === 0) {
        balance.value = response.data.charge
      } else {
        message('error', '', response.data.message)
      }

      return response.data.charge
    } catch (err: any) {
      errorHandle(err.response?.data || { message: '잔액 조회 중 오류가 발생했습니다.' })
      throw err
    } finally {
      loading.value = false
    }
  }

  // 에러 코드 조회
  const fetchErrorCodes = async (): Promise<{ sms_error_codes: Record<string, string>; kakao_error_codes: Record<string, string> }> => {
    try {
      const response = await api.get('/messages/error-codes/')
      return response.data
    } catch (err: any) {
      errorHandle(err.response?.data || { message: '에러 코드 조회 중 오류가 발생했습니다.' })
      throw err
    }
  }

  return {
    // state
    billIssue,
    sendHistory,
    balance,
    loading,

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
  }
})
