import api from '@/api'
import Cookies from 'js-cookie'
import { Buffer } from 'buffer'
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useWork } from '@/store/pinia/work_project'
import { usePermission } from '@/store/pinia/work_permission'
import { useLogging } from '@/store/pinia/work_logging'
import { useSearch } from '@/store/pinia/work_search'
import { useInform } from '@/store/pinia/work_inform'
import { useApproval } from '@/store/pinia/approval'
import { useChat } from '@/store/pinia/chat'
import { errorHandle, message } from '@/utils/helper'
import { useDocs } from '@/store/pinia/docs'
import type { LocationQueryValue } from 'vue-router'
import type { User, Profile, Scrape, Todo } from '@/store/types/accounts'

export type UserByAdmin = {
  username: string
  email: string
  password: string
  mail_sending: boolean
  send_option: '1' | '2'
  expired: number

  pk?: number
  is_active?: boolean
  is_staff?: boolean
  work_manager?: boolean
}
export type UserUpdateByAdmin = Pick<UserByAdmin, 'email'> & Partial<Omit<UserByAdmin, 'email'>>
type LoginUser = { email: string; password: string; redirect?: string }

const extractId = (token: string): number | null => {
  try {
    const parts = token.split('.')
    if (parts.length < 2 || !parts[1]) return null
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const payload = Buffer.from(base64, 'base64')
    const result = JSON.parse(payload.toString())
    return result?.user_id ?? null
  } catch {
    return null
  }
}

export const useAccount = defineStore('account', () => {
  // states
  const user = ref<User | null>(null)
  const userInfo = ref<User | null>(null)
  const usersList = ref<User[]>([])
  const accessToken = ref<string>('')
  const passChecked = ref(false)

  // getters
  const getUsers = computed(() =>
    usersList.value.map((u: User) => ({ value: u.pk as number, label: u.username })),
  )
  const isAuthorized = computed(() => !!accessToken.value && !!userInfo.value)

  // actions
  const fetchUsersList = (isActive: boolean | 'all' = true) => {
    const params: Record<string, string | number | boolean> = {
      limit: 500,
      is_active: isActive,
    }
    return api
      .get('/user/', { params })
      .then(res => (usersList.value = res.data.results ?? res.data ?? []))
      .catch(err => errorHandle(err))
  }

  const fetchUser = (pk: number, params?: Record<string, string | number | boolean>) =>
    api
      .get(`/user/${pk}/`, params ? { params } : undefined)
      .then(res => (user.value = res.data))
      .catch(err => errorHandle(err))

  const removeUser = () => (user.value = null)

  const adminCreateUser = (payload: UserByAdmin) =>
    api
      .post('/admin-create-user/', payload)
      .then(async res => {
        await fetchUsersList('all')
        message('info', '', res.data?.detail || '사용자를 생성하였습니다.')
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const adminUpdateUser = (payload: UserUpdateByAdmin) =>
    api
      .put(`/admin-create-user/`, payload)
      .then(async res => {
        const defaultMsg =
          payload.mail_sending && (payload.password || payload.send_option === '1')
            ? '사용자 정보를 수정하고 안내 메일을 발송했습니다.'
            : '사용자 권한 정보를 수정하였습니다.'
        await fetchUsersList('all')
        message('info', '', res.data?.detail || defaultMsg)
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const signup = (payload: LoginUser & { username: string }) =>
    api
      .post('/user/', payload)
      .then(() => {
        message('info', '', '회원가입이 완료되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  const setToken = (token: string) => {
    accessToken.value = token
    api.defaults.headers.common.Authorization = `Bearer ${accessToken.value}`
    Cookies.set('accessToken', accessToken.value, { expires: 14 })
  }

  const setUser = (user: User) => {
    userInfo.value = user

    const workStore = useWork()
    return Promise.all([
      fetchTodoList(),
      workStore.fetchMyProjectsList(),
      workStore.fetchGroupedPermissions(),
    ]).then(() => fetchProfile())
  }

  const login = async (payload: { email: string; password: string; redirect: string }) => {
    try {
      // 로그인 요청
      const tokenResponse = await api.post('/token/', payload)
      const accessToken = tokenResponse.data.access
      setToken(accessToken)

      // 사용자 정보 요청
      const userId = extractId(accessToken)
      if (!userId) throw new Error('Invalid access token')
      const userResponse = await api.get(`/user/${userId}/`)

      // API 응답을 확인하고 처리
      if (userResponse.data && (userResponse.data.profile || userResponse.data.is_superuser)) {
        await setUser(userResponse.data)
        // 성공 메시지
        message('info', '', '로그인 성공 알림!', 2000, 'top-center', 'bounce')
      } else {
        // 관리자 승인 대기 중 메시지
        message('default', '', '계정이 생성되었으며 관리자 승인 대기중입니다.', 10000)
      }

      return userResponse.data
    } catch (error) {
      // 에러 처리
      console.error('Login failed:', error)
      message('warning', '', '이메일 또는 비밀번호를 확인하여 주세요.', 5000)
    }
  }

  const clearAuthSession = () => {
    userInfo.value = null
    profile.value = null
    todoList.value = []
    accessToken.value = ''
    delete api.defaults.headers.common.Authorization
    Cookies.remove('accessToken')
  }

  const loginByToken = async (token?: string) => {
    if (!token) return await Promise.resolve()

    const userId = extractId(token)
    if (!userId) {
      clearAuthSession()
      return null
    }

    setToken(token)
    return await api
      .get(`/user/${userId}/`)
      .then(res => setUser(res.data))
      .catch(() => {
        clearAuthSession()
      })
  }

  const logout = () => {
    const workStore = useWork()
    const permStore = usePermission()
    const loggingStore = useLogging()
    const searchStore = useSearch()
    const informStore = useInform()
    const approvalStore = useApproval()
    const chatStore = useChat()
    workStore.reset()
    permStore.reset()
    loggingStore.reset()
    searchStore.reset()
    informStore.reset()
    approvalStore.reset()
    chatStore.reset()
    user.value = null
    usersList.value = []
    passChecked.value = false
    docScrape.value = null
    docScrapeList.value = []
    docScrapeCount.value = 0
    scrape.value = null
    scrapeList.value = []
    scrapeCount.value = 0
    clearAuthSession()
    message('info', '', '로그아웃 완료 알림!')
  }

  const checkPassword = (payload: LoginUser) =>
    api
      .post(`/check-password/`, payload)
      .then(() => (passChecked.value = true))
      .catch(() => message('warning', '', '비밀번호를 확인하여 주세요.'))

  const changePassword = (payload: { old_password: string; new_password: string }) =>
    api
      .post(`/change-password/`, payload)
      .then(res => {
        message('success', '', res.data.detail)
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const passReset = (payload: { email: string }) =>
    api
      .post('password-reset/', payload)
      .then(() => {
        message(undefined, '', '비밀번호 초기화 안내메일을 발송했습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  const passResetConfirm = (payload: {
    user_id: LocationQueryValue | LocationQueryValue[]
    token: LocationQueryValue | LocationQueryValue[]
    new_password: string
  }) => {
    const { user_id, token, new_password } = payload
    return api
      .post(`/password-reset-confirm/${user_id}/${token}/`, { new_password })
      .then(res => {
        message('success', '', '비밀번호가 변경되었습니다.')
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })
  }

  // 재설정 링크의 토큰 유효성 검증 (토큰 값은 서버에서만 대조하며 응답으로 받지 않음)
  const checkPassResetToken = (
    user_id: LocationQueryValue | LocationQueryValue[],
    token: LocationQueryValue | LocationQueryValue[],
  ): Promise<boolean> =>
    api
      .get(`/password-reset-confirm/${user_id}/${token}/`)
      .then(res => !!res.data?.valid)
      .catch(() => false)

  // getters
  const superAuth = computed(() => userInfo.value?.is_superuser)
  const workManager = computed(() => userInfo.value?.work_manager || superAuth.value)
  const isStaff = computed(() => !!superAuth.value || !!userInfo.value?.is_hq_staff) // 본사 관리 권한

  const profile = ref<Profile | null>(null)

  // actions
  const fetchProfile = async () => {
    const profilePk = userInfo.value?.profile?.pk ?? null
    return profilePk
      ? await api
          .get(`/profile/${profilePk}/`)
          .then(res => (profile.value = res.data))
          .catch(err => errorHandle(err))
      : null
  }

  const createProfile = async (payload: FormData) =>
    await api
      .post(`/profile/`, payload, { headers: { 'Content-Type': 'multipart/form-data' } })
      .then(async () => {
        const cookedToken = Cookies.get('accessToken')
        await loginByToken(cookedToken)
        message('info', '', '프로필 정보가 생성되었습니다.', 2000, 'top-center', 'bounce')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  const patchProfile = async (payload: { pk: number; form: FormData }) => {
    const { pk, form } = payload
    return await api
      .patch(`/profile/${pk}/`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
      .then(async () => {
        const cookedToken = Cookies.get('accessToken')
        await loginByToken(cookedToken)
        message('info', '', '프로필 정보가 수정되었습니다.', 2000, 'top-center', 'bounce')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })
  }

  // states
  const docScrape = ref<Scrape | null>(null)
  const docScrapeList = ref<Scrape[]>([])
  const docScrapeCount = ref(0)

  // actions
  const docScrapePages = (itemsPerPage: number) => Math.ceil(docScrapeCount.value / itemsPerPage)
  const fetchDocScrape = (pk: number) =>
    api
      .get(`/doc-scrape/${pk}/`)
      .then(res => (docScrape.value = res.data))
      .catch(err => errorHandle(err))

  const fetchDocScrapeList = (page = 1) =>
    api
      .get(`/doc-scrape/?user=${userInfo.value?.pk ?? ''}&page=${page}`)
      .then(res => {
        docScrapeList.value = res.data.results
        docScrapeCount.value = res.data.count
      })
      .catch(err => errorHandle(err))

  const docStore = useDocs()

  const createDocScrape = (payload: { docs: number; user: number }) =>
    api
      .post('/doc-scrape/', payload)
      .then(() => docStore.fetchDocs(payload.docs))
      .catch(err => errorHandle(err))

  const patchDocScrape = (pk: number, title: string) =>
    api
      .patch(`/doc-scrape/${pk}/`, { title })
      .then(() => fetchDocScrapeList().then(() => message()))
      .catch(err => errorHandle(err))

  const deleteDocScrape = (pk: number) =>
    api
      .delete(`/doc-scrape/${pk}/`)
      .then(() =>
        fetchDocScrapeList().then(() =>
          message('warning', '', '해당 문서 스크랩을 취소하였습니다.'),
        ),
      )
      .catch(err => errorHandle(err))

  // states
  const scrape = ref<Scrape | null>(null)
  const scrapeList = ref<Scrape[]>([])
  const scrapeCount = ref(0)

  // actions
  const scrapePages = (itemsPerPage: number) => Math.ceil(scrapeCount.value / itemsPerPage)
  const fetchScrape = (pk: number) =>
    api
      .get(`/post-scrape/${pk}/`)
      .then(res => (scrape.value = res.data))
      .catch(err => errorHandle(err))

  const fetchScrapeList = (page = 1) =>
    api
      .get(`/post-scrape/?user=${userInfo.value?.pk ?? ''}&page=${page}`)
      .then(res => {
        scrapeList.value = res.data.results
        scrapeCount.value = res.data.count
      })
      .catch(err => errorHandle(err))

  // const documentStore = useDocument()

  const createScrape = (payload: { post: number; user: number }) =>
    api
      .post('/post-scrape/', payload)
      .then(() => console.log('fetchPost()')) //documentStore.fetchPost(payload.post))
      .catch(err => errorHandle(err))

  const patchScrape = (pk: number, title: string) =>
    api
      .patch(`/post-scrape/${pk}/`, { title })
      .then(() => fetchScrapeList().then(() => message()))
      .catch(err => errorHandle(err))

  const deleteScrape = (pk: number) =>
    api
      .delete(`/post-scrape/${pk}/`)
      .then(() =>
        fetchScrapeList().then(() =>
          message('warning', '', '해당 포스트 스크랩을 취소하였습니다.'),
        ),
      )
      .catch(err => errorHandle(err))

  // states
  const todoList = ref<Todo[]>([])

  // getters
  const myTodos = computed(() =>
    todoList.value.filter(todo => !todo.soft_deleted && todo.user === userInfo.value?.pk),
  )

  const fetchTodoList = async () => {
    const url = userInfo.value ? `/todo/?user=${userInfo.value.pk}&soft_deleted=false` : '/todo/'
    return await api
      .get(url)
      .then(res => {
        todoList.value = res.data.results
      })
      .catch(err => errorHandle(err))
  }

  const createTodo = (payload: Todo) =>
    api
      .post('/todo/', payload)
      .then(() => {
        fetchTodoList().then(() =>
          api
            .get(`/user/${userInfo.value?.pk}/`)
            .then(res => {
              userInfo.value = res.data
            })
            .catch(err => errorHandle(err)),
        )
      })
      .catch(err => errorHandle(err))

  const patchTodo = (payload: Todo) =>
    api
      .patch(`/todo/${payload.pk}/`, payload)
      .then(() => fetchTodoList())
      .catch(err => errorHandle(err))

  const deleteTodo = (pk: number) =>
    api
      .delete(`/todo/${pk}/`)
      .then(() => {
        fetchTodoList().then(() =>
          api
            .get(`/user/${userInfo.value?.pk}/`)
            .then(res => {
              userInfo.value = res.data
            })
            .catch(err => errorHandle(err)),
        )
      })
      .catch(err => errorHandle(err))

  const convertTodoToIssue = async (
    pk: number,
    payload: {
      project: number
      tracker?: number
      priority?: number
      subject?: string
      description?: string
    },
  ) =>
    await api
      .post(`/todo/${pk}/convert_to_issue/`, payload)
      .then(res => {
        fetchTodoList()
        return res.data
      })
      .catch(err => errorHandle(err))

  return {
    user,
    userInfo,
    usersList,
    accessToken,
    passChecked,

    getUsers,
    isAuthorized,

    fetchUsersList,
    fetchUser,
    removeUser,
    adminCreateUser,
    adminUpdateUser,
    signup,
    login,
    loginByToken,
    logout,
    checkPassword,
    changePassword,
    passReset,
    passResetConfirm,

    checkPassResetToken,

    superAuth,
    workManager,
    isStaff,

    profile,

    fetchProfile,
    createProfile,
    patchProfile,

    docScrape,
    docScrapeList,
    docScrapeCount,

    docScrapePages,
    fetchDocScrape,
    fetchDocScrapeList,
    createDocScrape,
    patchDocScrape,
    deleteDocScrape,

    scrape,
    scrapeList,
    scrapeCount,

    scrapePages,
    fetchScrape,
    fetchScrapeList,
    createScrape,
    patchScrape,
    deleteScrape,

    todoList,
    myTodos,

    fetchTodoList,
    createTodo,
    patchTodo,
    deleteTodo,
    convertTodoToIssue,
  }
})
