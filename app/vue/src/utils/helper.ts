import { createToast, type ToastType, type Position, type TransitionType } from 'mosha-vue-toastify'
import { useDownload } from '@/utils/useDownload.ts'
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'

export const message = (
  type: ToastType = 'success',
  title = '알림!',
  description = '해당 내용이 저장되었습니다!',
  duration = 2500,
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
  // Handle different error response structures
  const errorData = err?.data || err

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

const md = new MarkdownIt('default', { html: true })

export const markdownRender = (content: string) => {
  const result = md.render(content)
  return DOMPurify.sanitize(result)
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
    // pk -> Board 매핑
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
export const { downloadFile } = useDownload()