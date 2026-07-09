<script lang="ts" setup>
import { computed, onBeforeMount, ref, reactive, watch } from 'vue'
import { onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project'
import api from '@/api'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

const accStore = useAccount()
const user = computed(() => accStore.user)
const workProjectStore = useWork()
const projectList = computed(() => workProjectStore.getVisibleProjPks)

const [route, router] = [useRoute(), useRouter()]

const form = reactive({
  username: '',
  email: '',
  password: '',
  pass_conf: '',
  is_active: true,
  is_staff: false,
  is_superuser: false,
  work_manager: false,
  // Profile fields
  name: '',
  birth_date: '',
  cell_phone: '',
  auto_watch_created: true,
  auto_watch_assigned: true,
  meeting_notification: true,
  // Notification fields (creation only)
  mail_sending: true,
  send_option: '1',
  expired: 24,
  subscribed_projects: [] as number[],
})

const genPass = ref('')
const validated = ref(false)

const formDataSetup = async () => {
  if (user.value) {
    form.username = user.value.username || ''
    form.email = user.value.email || ''
    form.password = ''
    form.pass_conf = ''
    form.is_active = user.value.is_active
    form.is_staff = user.value.is_staff
    form.is_superuser = user.value.is_superuser
    form.work_manager = user.value.work_manager

    if (user.value.profile) {
      form.name = user.value.profile.name || ''
      form.birth_date = user.value.profile.birth_date || ''
      form.cell_phone = user.value.profile.cell_phone || ''
      form.auto_watch_created = user.value.profile.auto_watch_created ?? true
      form.auto_watch_assigned = user.value.profile.auto_watch_assigned ?? true
      form.meeting_notification = user.value.profile.meeting_notification ?? true
    } else {
      form.name = ''
      form.birth_date = ''
      form.cell_phone = ''
      form.auto_watch_created = true
      form.auto_watch_assigned = true
      form.meeting_notification = true
    }

    try {
      const res = await api.get(`/project-subscription/?user=${user.value.pk}`)
      form.subscribed_projects = res.data.map((item: any) => item.project)
    } catch (err) {
      console.error(err)
      form.subscribed_projects = []
    }
  } else {
    form.username = ''
    form.email = ''
    form.password = ''
    form.pass_conf = ''
    form.is_active = true
    form.is_staff = false
    form.is_superuser = false
    form.work_manager = false
    form.name = ''
    form.birth_date = ''
    form.cell_phone = ''
    form.auto_watch_created = true
    form.auto_watch_assigned = true
    form.meeting_notification = true
    form.mail_sending = true
    form.send_option = '1'
    form.expired = 24
    form.subscribed_projects = []
  }
}

onBeforeMount(async () => {
  await workProjectStore.fetchVisibleProjectsList({})
  if (route.params.userId) {
    await accStore.fetchUser(Number(route.params.userId))
  } else {
    accStore.user = null
  }
  await formDataSetup()
})

onBeforeRouteUpdate(async to => {
  if (to.params.userId) await accStore.fetchUser(Number(to.params.userId))
  else accStore.user = null

  await formDataSetup()
})

watch(user, () => formDataSetup())

const generatePassword = () => {
  const chars =
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+[]{}|;:,.<>?'
  let password = ''

  for (let i = 0; i < 8; i++) {
    const array = new Uint32Array(1)
    window.crypto.getRandomValues(array)
    const randomIndex = array[0] % chars.length
    password += chars[randomIndex]
  }

  genPass.value = password
}

const applyGen = () => {
  form.password = genPass.value
  form.pass_conf = genPass.value
  genPass.value = ''
}

const onSubmit = async (event: Event) => {
  const el = event.currentTarget as HTMLFormElement
  if (!el.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()
    validated.value = true
    return
  }

  if (form.password && form.password !== form.pass_conf) {
    alert('비밀번호가 일치하지 않습니다.')
    return
  }

  try {
    let targetUserId = 0
    if (!user.value) {
      // Create user
      const payload = {
        username: form.username,
        email: form.email,
        password: form.password,
        mail_sending: form.mail_sending,
        send_option: form.send_option as '1' | '2',
        expired: form.expired,
      }
      const res = await accStore.adminCreateUser(payload)
      if (res && res.data && res.data.pk) {
        targetUserId = res.data.pk
      }
    } else {
      // Edit User account info
      targetUserId = user.value.pk as number
      const userPayload: any = {
        email: form.email,
        is_active: form.is_active,
        is_staff: form.is_staff,
        is_superuser: form.is_superuser,
        work_manager: form.work_manager,
      }
      if (form.password) {
        userPayload.password = form.password
      }
      await api.patch(`/user/${user.value.pk}/`, userPayload)

      // Edit User Profile info
      const profilePayload = {
        name: form.name,
        birth_date: form.birth_date,
        cell_phone: form.cell_phone,
        auto_watch_created: form.auto_watch_created,
        auto_watch_assigned: form.auto_watch_assigned,
        meeting_notification: form.meeting_notification,
      }
      if (user.value.profile) {
        await api.patch(`/profile/${user.value.profile.pk}/`, profilePayload)
      } else {
        await api.post(`/profile/`, { ...profilePayload, user: user.value.pk })
      }
    }

    if (targetUserId) {
      const res = await api.get(`/project-subscription/?user=${targetUserId}`)
      const existingSubs = res.data
      const existingProjIds = existingSubs.map((item: any) => item.project)

      const toAdd = form.subscribed_projects.filter((id: number) => !existingProjIds.includes(id))
      const toDelete = existingSubs.filter(
        (item: any) => !form.subscribed_projects.includes(item.project),
      )

      for (const projId of toAdd) {
        await api.post(`/project-subscription/`, { user: targetUserId, project: projId })
      }
      for (const sub of toDelete) {
        await api.delete(`/project-subscription/${sub.pk}/`)
      }
    }

    validated.value = false
    await router.push({ name: '사용자' })
  } catch (err: any) {
    console.error(err)
    alert('사용자 정보 저장 중 오류가 발생했습니다.')
  }
}
</script>

<template>
  <CRow class="py-2">
    <CCol class="mb-2">
      <span class="h5 mr-2"> 내 계정 </span>
    </CCol>

    <CCol v-if="user" class="text-right form-text">
      <span class="mr-2">
        <TextButton name="비밀번호 변경" icon="mdi-key-outline" />
      </span>
    </CCol>
  </CRow>

  <CRow>
    <CForm
      class="row needs-validation"
      novalidate
      :validated="validated"
      @submit.prevent="onSubmit"
    >
      <CCol class="col-lg-6">
        <CRow>
          <CCol lg="12">
            <!-- Account Info Card -->
            <CCard class="mb-4">
              <CCardHeader class="font-weight-bold">
                <v-icon icon="mdi-account-cog" class="mr-1" color="primary" />
                계정 정보
              </CCardHeader>
              <CCardBody>
                <!-- Username -->
                <CRow class="mb-3">
                  <CFormLabel for="username" class="col-sm-3 col-form-label required"
                    >아이디
                  </CFormLabel>
                  <CCol sm="9">
                    <CFormInput
                      v-model="form.username"
                      id="username"
                      maxlength="30"
                      placeholder="아이디"
                      autocomplete="off"
                      :disabled="!!user"
                      required
                    />
                  </CCol>
                </CRow>

                <!-- Email -->
                <CRow class="mb-3">
                  <CFormLabel for="email" class="col-sm-3 col-form-label required">
                    이메일
                  </CFormLabel>
                  <CCol sm="9">
                    <CFormInput
                      v-model="form.email"
                      id="email"
                      type="email"
                      maxlength="100"
                      placeholder="이메일"
                      required
                    />
                  </CCol>
                </CRow>

                <!-- Password -->
                <CRow class="mb-3">
                  <CFormLabel
                    for="password"
                    class="col-sm-3 col-form-label"
                    :class="{ required: !user }"
                  >
                    비밀번호
                  </CFormLabel>
                  <CCol sm="5">
                    <CFormInput
                      v-model="form.password"
                      id="password"
                      type="password"
                      maxlength="20"
                      placeholder="비밀번호"
                      autocomplete="off"
                      :required="!user"
                    />
                  </CCol>
                  <CCol sm="4">
                    <v-btn color="info" size="small" class="mt-1" @click="generatePassword">
                      임의 패스워드 생성
                    </v-btn>
                  </CCol>
                </CRow>

                <!-- Password Confirm -->
                <CRow class="mb-3" style="height: 45px">
                  <CFormLabel
                    for="pass_conf"
                    class="col-sm-3 col-form-label"
                    :class="{ required: !user }"
                  >
                    비밀번호 확인
                  </CFormLabel>
                  <CCol sm="5">
                    <CFormInput
                      v-model="form.pass_conf"
                      id="pass_conf"
                      type="password"
                      maxlength="20"
                      placeholder="비밀번호 확인"
                      :required="!user"
                    />
                  </CCol>
                  <CCol v-if="genPass" sm="4">
                    <div
                      class="p-1 mb-1 bg-yellow-lighten-1 text-center font-weight-bold"
                      style="width: 120px; display: inline-block; vertical-align: middle"
                    >
                      {{ genPass }}
                    </div>
                    <div style="display: inline-block; vertical-align: middle" class="ml-2">
                      <v-btn color="light" size="small" class="mr-1" @click="genPass = ''">
                        취소
                      </v-btn>
                      <v-btn color="success" size="small" @click="applyGen">적용</v-btn>
                    </div>
                  </CCol>
                </CRow>

                <!-- Permissions / Flags (Only visible when editing an existing user) -->
                <v-divider class="my-4" />
                <CRow class="mb-3">
                  <CFormLabel class="col-sm-3 col-form-label">권한 및 상태</CFormLabel>
                  <CCol sm="9" class="pt-2">
                    <CRow>
                      <CCol xs="6" class="mb-2">
                        <CFormCheck v-model="form.is_active" id="is_active" label="활성 사용자" />
                      </CCol>
                      <CCol xs="6" class="mb-2">
                        <CFormCheck v-model="form.is_staff" id="is_staff" label="스태프 권한" />
                      </CCol>

                      <CCol xs="6" class="mb-2">
                        <CFormCheck
                          v-model="form.work_manager"
                          id="work_manager"
                          label="업무관리자 권한"
                        />
                      </CCol>

                      <CCol xs="6" class="mb-2">
                        <CFormCheck
                          v-model="form.is_superuser"
                          id="is_superuser"
                          label="수퍼유저 권한"
                        />
                      </CCol>
                    </CRow>
                  </CCol>
                </CRow>
              </CCardBody>
            </CCard>
          </CCol>
        </CRow>
      </CCol>

      <CCol class="col-lg-6">
        <!-- Mail Notifications Card -->
        <CCard class="mb-4">
          <CCardHeader class="font-weight-bold">
            <template v-if="!user">
              <v-icon icon="mdi-email-arrow-right-outline" class="mr-1" color="primary" />
              알림 메일 발송 설정
            </template>
            <template v-else>
              <v-icon icon="mdi-cog" class="mr-1" color="primary" />
              업무 및 알림 설정
            </template>
          </CCardHeader>
          <CCardBody>
            <div v-if="!user">
              <CRow class="mb-2">
                <CCol>
                  <CFormCheck
                    v-model="form.mail_sending"
                    type="checkbox"
                    id="inform-mail"
                    label="새로 생성한 사용자에게 알림 메일 보내기"
                  />
                </CCol>
              </CRow>

              <CRow class="pl-4">
                <CCol sm="12" class="mb-3">
                  <CFormCheck
                    v-model="form.send_option"
                    value="1"
                    type="radio"
                    name="content-option"
                    id="content-option1"
                    label="패스워드 재설정 링크 포함"
                    :disabled="!form.mail_sending"
                  />
                </CCol>

                <CRow class="mb-3">
                  <CCol sm="4" class="pl-5 pt-1">
                    <span>링크 만료 시간 : </span>
                  </CCol>
                  <CCol sm="4">
                    <CFormSelect
                      v-model.number="form.expired as any"
                      size="sm"
                      :disabled="!form.mail_sending"
                    >
                      <option v-for="i in 24" :value="i" :key="i">
                        <span v-if="i < 10">0</span>{{ i }}
                      </option>
                    </CFormSelect>
                  </CCol>
                  <CCol sm="4" class="pt-1">시간</CCol>
                </CRow>

                <CCol sm="12" class="mb-3">
                  <CFormCheck
                    v-model="form.send_option"
                    value="2"
                    type="radio"
                    name="content-option"
                    id="content-option2"
                    label="사용자 패스워드 포함"
                    :disabled="!form.mail_sending"
                  />
                </CCol>
              </CRow>
              <v-divider class="my-4" />
            </div>

            <!-- 메일 알림 설정 -->
            <CRow class="mb-3">
              <CFormLabel class="col-sm-3 col-form-label">회의 알림 설정</CFormLabel>
              <CCol sm="9" class="pt-2">
                <CRow>
                  <CCol xs="12" class="mb-3">
                    <CFormCheck
                      v-model="form.meeting_notification"
                      id="meeting_notification"
                      label="회의록 참석 시 알림 메일 수신"
                    />
                  </CCol>
                </CRow>
              </CCol>
            </CRow>

            <!-- 자동 관람 설정 -->
            <v-divider class="my-4" />
            <CRow class="mb-3">
              <CFormLabel class="col-sm-3 col-form-label">업무 관람 설정</CFormLabel>
              <CCol sm="9" class="pt-2">
                <CRow>
                  <CCol xs="12" class="mb-4" style="width: 380px">
                    <v-autocomplete
                      v-model="form.subscribed_projects"
                      :items="projectList"
                      item-title="label"
                      item-value="value"
                      label="알림 구독 프로젝트"
                      multiple
                      chips
                      closable-chips
                      density="compact"
                      hint="선택한 프로젝트의 업무 변경 알림 메일을 수신합니다."
                      persistent-hint
                    />
                  </CCol>
                  <CCol xs="12" class="mb-2">
                    <CFormCheck
                      v-model="form.auto_watch_created"
                      id="auto_watch_created"
                      label="내가 생성한 업무 자동 지켜보기 (모니터링)"
                    />
                  </CCol>
                  <CCol xs="12" class="mb-3">
                    <CFormCheck
                      v-model="form.auto_watch_assigned"
                      id="auto_watch_assigned"
                      label="나에게 할당된 업무 자동 지켜보기 (모니터링)"
                    />
                  </CCol>
                </CRow>
              </CCol>
            </CRow>
          </CCardBody>
        </CCard>

        <!-- Submit & Cancel Footer -->
        <div class="text-right mb-4">
          <v-btn type="submit" color="primary"> 저장</v-btn>
          <v-btn color="light" class="mr-2" @click="router.push({ name: '사용자' })" flat>
            취소
          </v-btn>
        </div>
      </CCol>
    </CForm>
  </CRow>
</template>
