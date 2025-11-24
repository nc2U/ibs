import api from '@/api'
import Cookies from 'js-cookie'
import { Buffer } from 'buffer'
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useDocs } from '@/store/pinia/docs'
import { errorHandle, message } from '@/utils/helper'
import type { LocationQueryValue } from 'vue-router'
import type { User, StaffAuth, Profile, Scrape, Todo } from '@/store/types/accounts'

export type UserByAdmin = {
  username: string
  email: string
  password: string
  send_mail: boolean
  send_option: '1' | '2'
  expired: number
}
type LoginUser = { email: string; password: string; redirect?: string }

const extractId = (token: string) => {
  const base64Payload = token.split('.')[1]
  const payload = Buffer.from(base64Payload, 'base64')
  const result = JSON.parse(payload.toString())
  return result.user_id ? result.user_id : null
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
  const fetchUsersList = () =>
    api
      .get('/user/?is_active=true')
      .then(res => (usersList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const fetchUser = (pk: number) =>
    api
      .get(`/user/${pk}/`)
      .then(res => (user.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const removeUser = () => (user.value = null)

  const adminCreateUser = (payload: UserByAdmin) =>
    api
      .post('/admin-create-user/', payload)
      .then(res => {
        console.log(res)
        fetchUsersList().then(r => message('info', '', '사용자를 생성하고 메일을 발송했습니다.'))
      })
      .catch(err => errorHandle(err.response.data))

  const signup = (payload: LoginUser & { username: string }) =>
    api
      .post('/user/', payload)
      .then(() => message('info', '', '회원가입이 완료되었습니다.'))
      .catch(err => errorHandle(err.response.data))

  const setToken = (token: string) => {
    accessToken.value = token
    api.defaults.headers.common.Authorization = `Bearer ${accessToken.value}`
    Cookies.set('accessToken', accessToken.value, { expires: 14 })
  }

  const setUser = (user: User) => {
    userInfo.value = user
    fetchTodoList().then(() => fetchProfile())
  }

  const login = async (payload: { email: string; password: string; redirect: string }) => {
    try {
      // 로그인 요청
      const tokenResponse = await api.post('/token/', payload)
      const accessToken = tokenResponse.data.access
      setToken(accessToken)

      // 사용자 정보 요청
      const userId = extractId(accessToken)
      const userResponse = await api.get(`/user/${userId}/`)

      // API 응답을 확인하고 처리
      if (userResponse.data && (userResponse.data.profile || userResponse.data.is_superuser)) {
        setUser(userResponse.data)
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

  const loginByToken = async (token?: string) => {
    if (token) {
      setToken(token)
      return await api
        .get(`/user/${extractId(token)}/`)
        .then(res => setUser(res.data))
        .catch(() => {
          userInfo.value = null
          profile.value = null
          todoList.value = []
          accessToken.value = ''
          delete api.defaults.headers.common.Authorization
          Cookies.remove('accessToken')
        })
    } else return await Promise.resolve()
  }

  const logout = () => {
    userInfo.value = null
    profile.value = null
    todoList.value = []
    accessToken.value = ''
    delete api.defaults.headers.common.Authorization
    Cookies.remove('accessToken')
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
      .catch(err => errorHandle(err.response.data))

  const passReset = (payload: { email: string }) =>
    api
      .post('password-reset/', payload)
      .then(res => message(undefined, '', '비밀번호 초기화 안내메일을 발송했습니다.'))
      .catch(err => errorHandle(err.response.data))

  const passResetConfirm = (payload: {
    user_id: LocationQueryValue | LocationQueryValue[]
    token: LocationQueryValue | LocationQueryValue[]
    new_password: string
  }) => {
    const { user_id, token, new_password } = payload
    api
      .post(`/password-reset-confirm/${user_id}/${token}/`, { new_password })
      .then(res => {
        message('success', '', '비밀번호가 변경되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err.response.data))
  }

  const resetTokenList = ref<
    {
      pk: number
      user: number
      token: string
      updated: string
      is_expired: boolean
    }[]
  >([])

  const fetchResetTokenList = (user: number) =>
    api
      .get(`/pass-reset-token/?user=${user}`)
      .then(res => (resetTokenList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  // const fetchResetToken = (pk: number) =>
  //   api
  //     .get(`/pass-reset-token/${pk}/`)
  //     .then(res => (resetToken.value = res.data))
  //     .catch(err => errorHandle(err.response.data))

  // getters
  const superAuth = computed(() => userInfo.value?.is_superuser)
  const workManager = computed(() => userInfo.value?.work_manager || superAuth.value)
  const staffAuth = computed(() => (userInfo.value?.staffauth ? userInfo.value.staffauth : null)) // 장고 어드민 관리 권한
  const isStaff = computed(() => staffAuth.value?.is_staff || superAuth.value) // 본사 관리 권한

  const writeComDocs = computed(() => superAuth.value || staffAuth.value?.company_docs == '2')
  const writeProDocs = computed(
    () => superAuth.value || writeComDocs.value || staffAuth.value?.project_docs == '2',
  )
  const isComCash = computed(
    () => superAuth.value || Number(staffAuth.value?.company_ledger || null),
  )
  const writeComCash = computed(() => superAuth.value || staffAuth.value?.company_ledger == '2')
  const writeProCash = computed(
    () => superAuth.value || writeComCash.value || staffAuth.value?.project_ledger == '2',
  )

  // actions
  const createAuth = async (payload: StaffAuth, userPk: number) => {
    payload.user = userPk
    return await api
      .post(`/staff-auth/`, payload)
      .then(() => api.get(`/user/${userPk}/`).then(() => fetchUser(userPk).then(() => message())))
      .catch(err => errorHandle(err.response.data))
  }

  const patchAuth = async (payload: StaffAuth, userPk: number) => {
    const { pk, ...authData } = payload
    return await api
      .patch(`/staff-auth/${pk}/`, authData)
      .then(() => api.get(`/user/${userPk}/`).then(() => fetchUser(userPk).then(() => message())))
      .catch(err => errorHandle(err.response.data))
  }

  // states
  const profile = ref<Profile | null>(null)

  // actions
  const fetchProfile = async () => {
    const profilePk = userInfo.value?.profile?.pk ?? null
    return profilePk
      ? await api
          .get(`/profile/${profilePk}/`)
          .then(res => (profile.value = res.data))
          .catch(err => errorHandle(err.response.data))
      : null
  }

  const createProfile = async (payload: FormData) => {
    api.defaults.headers.post['Content-Type'] = 'multipart/form-data'
    return await api
      .post(`/profile/`, payload)
      .then(() => {
        const cookedToken = Cookies.get('accessToken')
        loginByToken(cookedToken).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))
  }

  const patchProfile = async (payload: { pk: number; form: FormData }) => {
    const { pk, form } = payload
    api.defaults.headers.patch['Content-Type'] = 'multipart/form-data'
    return await api
      .patch(`/profile/${pk}/`, form)
      .then(() => {
        const cookedToken = Cookies.get('accessToken')
        loginByToken(cookedToken).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))
  }

  // states
  const docScrape = ref<Scrape | null>(null)
  const docScrapeList = ref<Scrape[]>([])
  const docScrapeCount = ref(0)

  // actions
  const docScrapePages = (itemsPerPage: number) => Math.ceil(scrapeCount.value / itemsPerPage)
  const fetchDocScrape = (pk: number) =>
    api
      .get(`/doc-scrape/${pk}/`)
      .then(res => (docScrape.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchDocScrapeList = (page = 1) =>
    api
      .get(`/doc-scrape/?user=${userInfo.value?.pk ?? ''}&page=${page}`)
      .then(res => {
        docScrapeList.value = res.data.results
        docScrapeCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))

  const docStore = useDocs()

  const createDocScrape = (payload: { docs: number; user: number }) =>
    api
      .post('/doc-scrape/', payload)
      .then(() => docStore.fetchDocs(payload.docs))
      .catch(err => errorHandle(err.response.data))

  const patchDocScrape = (pk: number, title: string) =>
    api
      .patch(`/doc-scrape/${pk}/`, { title })
      .then(() => fetchScrapeList().then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const deleteDocScrape = (pk: number) =>
    api
      .delete(`/doc-scrape/${pk}/`)
      .then(() =>
        fetchScrapeList().then(() =>
          message('warning', '', '해당 포스트 스크랩을 취소하였습니다.'),
        ),
      )
      .catch(err => errorHandle(err.response.data))

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
      .catch(err => errorHandle(err.response.data))

  const fetchScrapeList = (page = 1) =>
    api
      .get(`/post-scrape/?user=${userInfo.value?.pk ?? ''}&page=${page}`)
      .then(res => {
        scrapeList.value = res.data.results
        scrapeCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))

  // const documentStore = useDocument()

  const createScrape = (payload: { post: number; user: number }) =>
    api
      .post('/post-scrape/', payload)
      .then(() => console.log('fetchPost()')) //documentStore.fetchPost(payload.post))
      .catch(err => errorHandle(err.response.data))

  const patchScrape = (pk: number, title: string) =>
    api
      .patch(`/post-scrape/${pk}/`, { title })
      .then(() => fetchScrapeList().then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const deleteScrape = (pk: number) =>
    api
      .delete(`/post-scrape/${pk}/`)
      .then(() =>
        fetchScrapeList().then(() =>
          message('warning', '', '해당 포스트 스크랩을 취소하였습니다.'),
        ),
      )
      .catch(err => errorHandle(err.response.data))

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
      .catch(err => errorHandle(err.response.data))
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
            .catch(err => errorHandle(err.response.data)),
        )
      })
      .catch(err => errorHandle(err.response.data))

  const patchTodo = (payload: Todo) =>
    api
      .patch(`/todo/${payload.pk}/`, payload)
      .then(() => fetchTodoList())
      .catch(err => errorHandle(err.response.data))

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
            .catch(err => errorHandle(err.response.data)),
        )
      })
      .catch(err => errorHandle(err.response.data))

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
    signup,
    login,
    loginByToken,
    logout,
    checkPassword,
    changePassword,
    passReset,
    passResetConfirm,

    resetTokenList,
    fetchResetTokenList,

    superAuth,
    workManager,
    staffAuth,
    isStaff,
    writeComDocs,
    writeProDocs,
    isComCash,
    writeComCash,
    writeProCash,

    createAuth,
    patchAuth,

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
  }
})
