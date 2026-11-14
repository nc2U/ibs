import { createToast, type ToastType, type Position, type TransitionType } from 'mosha-vue-toastify'
import { useDownload } from '@/utils/useDownload.ts'
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'

export const message = (
  type: ToastType = 'success',
  title = '알림!',
  description = '해당 내용이 저장되었습니다!',
  duration = 3500,
  position: Position = 'top-right',
  transition: TransitionType = 'slide',
) => {
  createToast(
    { title, description },
    {
      type,
      position,
      transition,
      hideProgressBar: true,
      showIcon: true,
      timeout: duration,
      // toastBackgroundColor: '#4DC374',
    },
  )
}

const isRecord = (val: unknown): val is Record<string, unknown> =>
  typeof val === 'object' && val !== null

/**
 * Extract structured API error payload from an Axios error, response object, or plain error.
 */
export const getErrorData = (err: unknown): unknown => {
  if (isRecord(err)) {
    const response = isRecord(err.response) ? err.response : null
    if (
      response &&
      response.data !== undefined &&
      response.data !== null &&
      response.data !== ''
    ) {
      return response.data
    }
    if (err.data !== undefined && err.data !== null && err.data !== '') {
      return err.data
    }
  }
  return err
}

/**
 * Extract a user-facing error message from an unknown error value.
 */
export const getErrorMessage = (
  err: unknown,
  fallback = '알 수 없는 오류가 발생했습니다.',
): string => {
  const errorData = getErrorData(err)

  if (typeof errorData === 'string' && errorData.trim()) return errorData

  if (isRecord(errorData) && !(errorData instanceof Error)) {
    for (const key of ['detail', 'error', 'message', 'non_field_errors']) {
      const value = errorData[key]
      if (typeof value === 'string' && value.trim()) return value
      if (Array.isArray(value) && value.length > 0) return String(value[0])
    }
    for (const value of Object.values(errorData)) {
      if (typeof value === 'string' && value.trim()) return value
      if (Array.isArray(value) && value.length > 0) return String(value[0])
    }
  }

  if (err instanceof Error && err.message) return err.message
  if (isRecord(err) && typeof err.message === 'string' && err.message) return err.message

  return fallback
}

export const errorHandle = (err: unknown): void => {
  const errorData = getErrorData(err)

  if (isRecord(errorData) && errorData.code === 'token_not_valid') {
    console.log('token_not_valid')
  } else if (isRecord(errorData) && errorData.detail === '자격 인증 데이터가 제공되지 않았습니다.') {
    // 401 Unauthorized 에러의 경우 조용히 처리 (이미 API 인터셉터에서 리다이렉트 처리됨)
    console.log('Unauthorized - redirecting to login')
  } else {
    console.error('[API Error Detail]:', JSON.stringify(errorData, null, 2))
    console.log(err)

    // If errorData is a structured API error object, display each field error message
    if (isRecord(errorData) && !(errorData instanceof Error)) {
      let handled = false
      for (const [key, value] of Object.entries(errorData)) {
        if (typeof value === 'string') {
          message('danger', `${key} - 에러`, value, 10000)
          handled = true
        } else if (Array.isArray(value)) {
          value.forEach((msg: unknown) => {
            message('danger', `${key} - 에러`, String(msg), 10000)
            handled = true
          })
        }
      }
      if (!handled) {
        message('danger', '에러', getErrorMessage(err), 10000)
      }
    } else {
      message('danger', '에러', getErrorMessage(err), 10000)
    }
  }
}

export const hashCode = (s: string) =>
  s.split('').reduce((a, b) => {
    a = (a << 5) - a + b.charCodeAt(0)
    return a & a
  }, 0)

export const isValidate = (event: Event) => {
  const el = event.currentTarget as HTMLInputElement | HTMLSelectElement | HTMLFormElement
  if (!el.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()

    return true
  } else return false
}

const md = new MarkdownIt('default', { html: true, breaks: true })

export const markdownRender = (content: string) => {
  if (!content) return ''
  const normalized = content.replace(/\r\n/g, '\n')
  // 1) 행 시작의 숫자+마침표('1. ', '2. ')가 마크다운 <ol> 리스트로 자동 변환되어 숫자와 텍스트가 분리되는 현상 방지
  const listEscaped = normalized.replace(/^(\s*\d+)\.\s+/gm, '$1\\. ')
  // 2) 3개 이상 연속된 엔터(빈 줄 1개 이상)가 있을 때, 빈 문단 보존
  const preprocessed = listEscaped.replace(/\n{3,}/g, match => {
    const extraEmptyLines = match.length - 2
    return '\n\n' + '<p class="empty-line">&nbsp;</p>\n\n'.repeat(extraEmptyLines)
  })
  const rendered = md.render(preprocessed)
  // 3) HTML 태그 외부의 2개 이상 연속 스페이스('  +')를 &nbsp;로 변환하여 다중 띄어쓰기(스페이스바) 보존
  const parts = rendered.split(/(<[^>]+>)/g)
  for (let i = 0; i < parts.length; i++) {
    if (!parts[i].startsWith('<')) {
      parts[i] = parts[i].replace(/  +/g, match => '&nbsp;'.repeat(match.length))
    }
  }
  return DOMPurify.sanitize(parts.join(''))
}

// localStorage 에 저장된 순서가 있을 경우, 그 순서에 맞게 정렬
export const getOrderedList = <T extends { pk: number }>(objectList: T[], key: string): T[] => {
  const savedOrder = JSON.parse(localStorage.getItem(key) || '[]') as {
    pk: number
    order: number
  }[]

  if (savedOrder.length) {
    // pk -> Forum 매핑
    const objectMap = new Map(objectList.map(obj => [obj.pk, obj]))
    const ordered = savedOrder
      .map(item => objectMap.get(item.pk))
      .filter((item): item is T => item !== undefined)

    // 누락된 boardList 항목을 추가로 병합
    const missing = objectList.filter(b => !ordered.some(o => o.pk === b.pk))
    return [...ordered, ...missing]
  } else return [...objectList]
}

// 순서가 바뀌면 저장
export const setLocalStorage = <T extends { pk: number }>(orderedList: T[], key: string) => {
  const order = orderedList.map((obj, idx) => ({
    pk: obj.pk,
    order: idx,
  }))
  localStorage.setItem(key, JSON.stringify(order))
}

// 파일 다운로드
export const { downloadFile, downloadViaWindowOpen } = useDownload()

export const cleanupParams = (params: Record<string, unknown>): Record<string, unknown> => {
  const cleanedParams: Record<string, unknown> = {}
  for (const key in params) {
    const value = params[key]
    if (value !== null && value !== undefined && value !== '') {
      cleanedParams[key] = value
    }
  }
  return cleanedParams
}

export const generatePassword = () => {
  const chars =
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+[]{}|;:,.<>?'
  let password = ''

  for (let i = 0; i < 8; i++) {
    const array = new Uint32Array(1)
    window.crypto.getRandomValues(array)
    const randomIndex = array[0] % chars.length
    password += chars[randomIndex]
  }

  return password
}
