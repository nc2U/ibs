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

export const errorHandle = (err: any) => {
  // Handle different error response structures safely
  const errorData = err?.response?.data || err?.data || err

  if (errorData?.code === 'token_not_valid') {
    console.log('token_not_valid')
  } else if (errorData?.detail === '자격 인증 데이터가 제공되지 않았습니다.') {
    // 401 Unauthorized 에러의 경우 조용히 처리 (이미 API 인터셉터에서 리다이렉트 처리됨)
    console.log('Unauthorized - redirecting to login')
  } else {
    console.log(err)

    // If errorData is an object with error details, iterate through them
    if (errorData && typeof errorData === 'object') {
      for (const key in errorData) {
        if (typeof errorData[key] === 'string') {
          message('danger', `${key} - 에러`, `${errorData[key]}`, 10000)
        } else if (Array.isArray(errorData[key])) {
          // Handle array of error messages
          errorData[key].forEach((msg: string) => {
            message('danger', `${key} - 에러`, msg, 10000)
          })
        }
      }
    } else {
      // Fallback for simple error messages
      message(
        'danger',
        '에러',
        String(errorData || err || '알 수 없는 오류가 발생했습니다.'),
        10000,
      )
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

interface Item {
  pk: number

  [key: string]: any
}

// localStorage 에 저장된 순서가 있을 경우, 그 순서에 맞게 정렬
export const getOrderedList = (objectList: Item[], key: string) => {
  const savedOrder = JSON.parse(localStorage.getItem(key) || '[]') as {
    pk: number
    order: number
  }[]

  if (savedOrder.length) {
    // pk -> Forum 매핑
    const objectMap = new Map(objectList.map(obj => [obj.pk, obj]))
    const ordered = savedOrder.map(item => objectMap.get(item.pk)).filter(Boolean) as any[]

    // 누락된 boardList 항목을 추가로 병합
    const missing = objectList.filter(b => !ordered.some(o => o.pk === b.pk))
    return [...ordered, ...missing]
  } else return [...objectList]
}

// 순서가 바뀌면 저장
export const setLocalStorage = (orderedList: Item[], key: string) => {
  const order = orderedList.map((obj, idx) => ({
    pk: obj.pk,
    order: idx,
  }))
  localStorage.setItem(key, JSON.stringify(order))
}

// 파일 다운로드
export const { downloadFile, downloadViaWindowOpen } = useDownload()

export const cleanupParams = (params: Record<string, any>): Record<string, any> => {
  const cleanedParams: Record<string, any> = {}
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
