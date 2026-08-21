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

export function useSSE() {
  const approvalStore = useApproval()
  const accountStore = useAccount()
  const issueStore = useIssue()

  const connect = () => {
    const token = Cookies.get('accessToken')
    if (!token) return

    // 기존 연결이 이미 열려있다면 중복 연결 방지
    if (eventSource.value && eventSource.value.readyState !== EventSource.CLOSED) {
      return
    }

    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }

    try {
      const url = `/api/v1/notifications/stream/?token=${encodeURIComponent(token)}`
      const es = new EventSource(url)

      es.addEventListener('connected', () => {
        // SSE 스트림 정상 연결 확인
      })

      es.addEventListener('notification', (event: MessageEvent) => {
        try {
          const payload: SSENotificationPayload = JSON.parse(event.data)

          // 1. 전자결재 이벤트 -> 대기함, 기안함, 완료함 및 헤더 배지 즉각 동기화
          if (payload.category === 'approval') {
            approvalStore.fetchMyPending()
            approvalStore.fetchMyDrafted()
            approvalStore.fetchMyApproved()
          }

          // 2. 업무/할일 이벤트 -> 담당 업무 및 할일 목록 즉각 갱신
          if (payload.category === 'work') {
            const userPk = accountStore.userInfo?.pk
            issueStore.fetchIssueByMember(userPk ? String(userPk) : undefined)
            accountStore.fetchTodoList()
          }

          // 3. 알림 사운드 재생 (딩-동♪)
          playNotificationSound()

          // 4. 인앱 토스트 팝업 알림
          message('info', payload.title, payload.body, 5000)
        } catch (err) {
          console.error('Failed to parse SSE notification payload:', err)
        }
      })

      es.onerror = () => {
        es.close()
        eventSource.value = null
        // 10초 후 자동 재연결 시도
        if (Cookies.get('accessToken')) {
          reconnectTimer = setTimeout(() => {
            connect()
          }, 10000)
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
  }

  return {
    connect,
    disconnect,
    eventSource,
  }
}
