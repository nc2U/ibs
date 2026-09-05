import api from '@/api'

/**
 * 특정 대상(업무/회의록/문서/전자결재 등)의 상세 화면에 진입했을 때 관련 미확인 알림을 일괄 읽음 처리
 * @param targetType 'issue' | 'meeting' | 'notice' | 'approval' 등
 * @param targetId 대상 객체 PK
 */
export async function markNotificationReadByTarget(targetType: string, targetId: number | string) {
  if (!targetType || !targetId) return
  try {
    await api.post(
      '/notification/read-by-target/',
      { target_type: targetType, target_id: String(targetId) },
      { skipErrorInterceptor: true, hideProgress: true } as any,
    )
  } catch {
    // 백그라운드 읽음 처리 오류는 사용자 화면에 에러를 띄우지 않음
  }
}
