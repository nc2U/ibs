import { ref } from 'vue'
import Cookies from 'js-cookie'
import { useApproval } from '@/store/pinia/approval'
import { useAccount } from '@/store/pinia/account'
import { useIssue } from '@/store/pinia/work_issue'
import { message } from '@/utils/helper'
import { playNotificationSound } from '@/utils/sound'

export type SSENotificationPayload = {
  category: 'approval' | 'work' | 'meeting' | 'notice' | string
  title: string
  body: string
  target_type?: string
  target_id?: string
  extra?: Record<string, any>
}

const eventSource = ref<EventSource | null>(null)
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let currentConnectedToken: string | null = null
let retryCount = 0

export function useSSE() {
  const approvalStore = useApproval()
  const accountStore = useAccount()
  const issueStore = useIssue()

  const connect = (force = false) => {
    const token = Cookies.get('accessToken')
    if (!token) {
      disconnect()
      return
    }

    // 토큰이 변경되었으면 기존 연결 강제 종료 후 재연결
    if (token !== currentConnectedToken) {
      disconnect()
    } else if (!force && eventSource.value && eventSource.value.readyState !== EventSource.CLOSED) {
      // 기존 연결이 정상 유지 중이면 중복 연결 방지
      return
    }

    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }

    try {
      const url = `/api/v1/notifications/stream/?token=${encodeURIComponent(token)}`
      const es = new EventSource(url)
      currentConnectedToken = token

      es.addEventListener('connected', () => {
        // SSE 스트림 정상 연결 확인 시 재시도 카운트 초기화
        retryCount = 0
      })

      es.addEventListener('notification', (event: MessageEvent) => {
        try {
          retryCount = 0 // 정상 수신 시 백오프 초기화
          const payload: SSENotificationPayload = JSON.parse(event.data)

          // 1. 전자결재 이벤트 -> 대기함, 기안함, 완료함 및 헤더 배지 즉각 동기화
          if (payload.category === 'approval') {
            approvalStore.fetchMyPending()
            approvalStore.fetchMyDrafted()
            approvalStore.fetchMyApproved()
          }

          // 2. 업무/할일 이벤트 -> 담당 업무 및 할일 목록 즉각 갱신
          if (payload.category === 'work' || payload.category === 'meeting') {
            const userPk = accountStore.userInfo?.pk
            issueStore.fetchIssueByMember(userPk ? String(userPk) : undefined)
            accountStore.fetchTodoList()
          }

          // 3. 알림 사운드 재생 (딩-동♪)
          playNotificationSound()

          // 4. 인앱 토스트 팝업 알림 (승인은 초록색, 반려는 주황색, 일반은 파란색)
          let toastType: 'success' | 'warning' | 'info' | 'error' = 'info'
          if (payload.title.includes('완료') || payload.title.includes('승인')) {
            toastType = 'success'
          } else if (payload.title.includes('반려')) {
            toastType = 'warning'
          }
          message(toastType, payload.title, payload.body, 5000)
        } catch (err) {
          console.error('Failed to parse SSE notification payload:', err)
        }
      })

      es.onerror = () => {
        es.close()
        eventSource.value = null
        currentConnectedToken = null

        // 지수 백오프(Exponential Backoff): 3초, 6초, 12초... 최대 30초
        const delay = Math.min(3000 * Math.pow(2, retryCount), 30000)
        retryCount++

        if (Cookies.get('accessToken')) {
          reconnectTimer = setTimeout(() => {
            connect()
          }, delay)
        }
      }

      eventSource.value = es
    } catch (err) {
      console.error('SSE connect failed:', err)
    }
  }

  const disconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
    }
    currentConnectedToken = null
    retryCount = 0
  }

  return {
    connect,
    disconnect,
    eventSource,
  }
}
