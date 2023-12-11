import api from '@/api'
import Cookies from 'js-cookie'
import { Buffer } from 'buffer'
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper'
import { type User, type StaffAuth, type Profile, type Todo } from '@/store/types/accounts'

type LoginUser = { email: string; password: string }

const extractId = (token: string) => {
  const base64Payload = token.split('.')[1]
  const payload = Buffer.from(base64Payload, 'base64')
  const result = JSON.parse(payload.toString())
  return result.user_id ? result.user_id : null
}

export const useAccount = defineStore('account', () => {
  // states
  const usersList = ref<User[]>([])
  const user = ref<User | null>(null)
  const accessToken = ref<string>('')
  const userInfo = ref<User | null>(null)
  const profile = ref<Profile | null>(null)
  const todoList = ref<Todo[]>([])

  // getters
  const superAuth = computed(() => userInfo.value?.is_superuser)
  const staffAuth = computed(() => (userInfo.value?.staffauth ? userInfo.value.staffauth : null))
  const isAuthorized = computed(() => !!accessToken.value && !!userInfo.value)
  const myTodos = computed(() =>
    todoList.value.filter(todo => !todo.soft_deleted && todo.user === userInfo.value?.pk),
  )
  const getUsers = computed(() =>
    usersList.value.map((u: User) => ({ value: u.pk, label: u.username })),
  )

  // actions
  const fetchUsersList = () =>
    api
      .get('/user/')
      .then(res => (usersList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const fetchUser = (pk: number) =>
    api
      .get(`/user/${pk}/`)
      .then(res => (user.value = res.data))
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

  const login = (payload: LoginUser) => {
    Cookies.remove('accessToken')
    return api
      .post('/token/', payload)
      .then(res => {
        setToken(res.data.access)
        return api.get(`/user/${extractId(accessToken.value)}/`)
      })
      .then(res => {
        setUser(res.data)
        message('info', '', '로그인 성공 알림!', 2000, 'top-center', 'bounce')
      })
      .catch(() => message('warning', '', '이메일 또는 비밀번호를 확인하여 주세요.'))
  }

  const loginByToken = (token?: string) => {
    if (token) {
      setToken(token)
      return api
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
    } else return Promise.resolve()
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

  const createAuth = (payload: StaffAuth, userPk: number) => {
    payload.user = userPk
    return api
      .post(`/staff-auth/`, payload)
      .then(() => {
        return api.get(`/user/${userPk}/`).then(() => fetchUser(userPk).then(() => message()))
      })
      .catch(err => errorHandle(err.response.data))
  }

  const patchAuth = (payload: StaffAuth, userPk: number) => {
    const { pk, ...authData } = payload
    return api
      .patch(`/staff-auth/${pk}/`, authData)
      .then(() => {
        return api.get(`/user/${userPk}/`).then(() => fetchUser(userPk).then(() => message()))
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchProfile = () =>
    userInfo.value?.profile
      ? api
          .get(`/profile/${userInfo.value?.profile}/`)
          .then(res => (profile.value = res.data))
          .catch(err => errorHandle(err.response.data))
      : null

  const createProfile = (payload: FormData) => {
    api.defaults.headers.post['Content-Type'] = 'multipart/form-data'
    return api
      .post(`/profile/`, payload)
      .then(() => {
        const cookedToken = Cookies.get('accessToken')
        loginByToken(cookedToken).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))
  }

  const patchProfile = (payload: { pk: number; form: FormData }) => {
    const { pk, form } = payload
    api.defaults.headers.patch['Content-Type'] = 'multipart/form-data'
    return api
      .patch(`/profile/${pk}/`, form)
      .then(() => {
        const cookedToken = Cookies.get('accessToken')
        loginByToken(cookedToken).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchTodoList = () => {
    const url = userInfo.value ? `/todo/?user=${userInfo.value.pk}&soft_deleted=false` : '/todo/'
    return api
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
    accessToken,
    userInfo,
    profile,
    todoList,

    superAuth,
    staffAuth,
    isAuthorized,
    myTodos,
    getUsers,

    fetchUsersList,
    fetchUser,
    signup,
    login,
    loginByToken,
    logout,

    createAuth,
    patchAuth,

    fetchProfile,
    createProfile,
    patchProfile,

    fetchTodoList,
    createTodo,
    patchTodo,
    deleteTodo,
  }
})