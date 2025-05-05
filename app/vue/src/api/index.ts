import axios from 'axios'
import router from '@/router'
import Cookies from 'js-cookie'
import { start, close } from '@/utils/nprogress'

const api = axios.create({ baseURL: '/api/v1/' })

// 요청 인터셉터
api.interceptors.request.use(
  config => {
    start() // 진행바 시작
    return config
  },
  error => {
    close() // 에러 시 진행바 닫기
    return Promise.reject(error)
  },
)

// 응답 인터셉터
api.interceptors.response.use(
  response => {
    close() // 정상 응답 시 진행바 닫기
    return response
  },
  async error => {
    close() // 에러 발생 시 진행바 닫기
    if (error.response && error.response.status === 401) {
      const redirectPath = Cookies.get('redirectPath') || '/'
      // 로그인 페이지로 리다이렉트
      await router.push({
        name: 'Login',
        query: { redirect: redirectPath },
      })
    }
    return Promise.reject(error)
  },
)

// CSRF 토큰 설정 (Django와 같은 백엔드와 호환)
api.defaults.xsrfCookieName = 'csrftoken'
api.defaults.xsrfHeaderName = 'X-CSRFToken'

export default api
