<script lang="ts" setup>
import api from '@/api'
import { computed, onBeforeMount, ref, reactive, watch } from 'vue'
import { onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import AvatarInput from '@/views/_MyPage/Modify/components/AvatarInput.vue'

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)
const profile = computed(() => accStore.profile)

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
  image: undefined as File | undefined,
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

const transProfileForm = (img?: File) => (form.image = img)

const formDataSetup = async () => {
  if (userInfo.value) {
    form.username = userInfo.value.username || ''
    form.email = userInfo.value.email || ''
    form.password = ''
    form.pass_conf = ''
    form.is_active = userInfo.value.is_active
    form.is_staff = userInfo.value.is_staff
    form.is_superuser = userInfo.value.is_superuser
    form.work_manager = userInfo.value.work_manager

    if (userInfo.value.profile) {
      form.name = userInfo.value.profile.name || ''
      form.birth_date = userInfo.value.profile.birth_date || ''
      form.cell_phone = userInfo.value.profile.cell_phone || ''
      form.auto_watch_created = userInfo.value.profile.auto_watch_created ?? true
      form.auto_watch_assigned = userInfo.value.profile.auto_watch_assigned ?? true
      form.meeting_notification = userInfo.value.profile.meeting_notification ?? true
    } else {
      form.name = ''
      form.birth_date = ''
      form.cell_phone = ''
      form.auto_watch_created = true
      form.auto_watch_assigned = true
      form.meeting_notification = true
    }

    try {
      const res = await api.get(`/project-subscription/?user=${userInfo.value.pk}`)
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

const loading = ref(true)

onBeforeMount(async () => {
  await workProjectStore.fetchVisibleProjectsList({})
  if (route.params.userId) {
    await accStore.fetchUser(Number(route.params.userId))
  } else {
    accStore.user = null
  }
  await formDataSetup()
  loading.value = false // 로딩 완료
})

onBeforeRouteUpdate(async to => {
  if (to.params.userId) await accStore.fetchUser(Number(to.params.userId))
  else accStore.user = null

  await formDataSetup()
})

watch(userInfo, () => formDataSetup())

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
    if (!userInfo.value) {
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
      targetUserId = userInfo.value.pk as number
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

      // Edit User Profile info
      const profilePayload = {
        name: form.name,
        birth_date: form.birth_date,
        cell_phone: form.cell_phone,
        auto_watch_created: form.auto_watch_created,
        auto_watch_assigned: form.auto_watch_assigned,
        meeting_notification: form.meeting_notification,
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
  <div v-if="loading"></div>
  <div v-else>
    <CRow class="py-2">
      <CCol class="mb-2">
        <span class="h5 mr-2"> 내 계정 </span>
      </CCol>

      <CCol class="text-right form-text">
        <span class="mr-2">
          <TextButton
            name="비밀번호 변경"
            :to="{ name: '비밀번호 변경' }"
            icon="mdi-key-outline"
            icon-color="amber"
          />
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
          <!-- Account Info Card -->
          <CCard class="mb-4">
            <CCardHeader class="font-weight-bold">
              <v-icon icon="mdi-account-cog" class="mr-1" color="primary" />
              계정 정보
            </CCardHeader>
            <CCardBody>
              <!-- Username -->
              <CRow class="mb-3">
                <CFormLabel for="username" class="col-sm-3 col-form-label required">
                  아이디
                </CFormLabel>
                <CCol sm="9">
                  <span>{{ form.username }}</span>
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
                  :class="{ required: !userInfo }"
                >
                  비밀번호
                </CFormLabel>
                <CCol sm="5">
                  <v-btn color="light" @click="router.push({ name: '비밀번호 변경' })">
                    비밀번호 변경
                  </v-btn>
                </CCol>
              </CRow>
            </CCardBody>
          </CCard>

          <!-- Profile Image Card -->
          <CCard class="mb-4">
            <CCardHeader class="font-weight-bold">
              <v-icon icon="mdi-account-circle" class="mr-1" color="primary" />
              아바타
            </CCardHeader>
            <CCardBody>
              <!-- Username -->
              <CRow class="mb-3">
                <CFormLabel for="username" class="col-sm-3 col-form-label"></CFormLabel>
                <CCol sm="9">
                  <AvatarInput
                    ref="avatar"
                    :image="(profile && profile.image) || '/static/dist/img/NoImage.jpeg'"
                    @trans-profile-form="transProfileForm"
                  />
                </CCol>
              </CRow>
            </CCardBody>
          </CCard>
        </CCol>

        <CCol class="col-lg-6">
          <!-- Profile Info Card -->
          <CCard class="mb-4">
            <CCardHeader class="font-weight-bold">
              <v-icon icon="mdi-account-check" class="mr-1" color="primary" />
              내 프로필
            </CCardHeader>
            <CCardBody>
              <!-- Username -->
              <CRow class="mb-3">
                <CFormLabel for="username" class="col-sm-3 col-form-label required">
                  이름
                </CFormLabel>
                <CCol sm="9">
                  <CFormInput
                    v-model="form.name"
                    type="text"
                    placeholder="성명을 입력하세요"
                    maxlength="20"
                    id="name"
                    required
                  />
                  <CFormFeedback invalid>성명을 입력하세요.</CFormFeedback>
                </CCol>
              </CRow>

              <CRow class="mb-3">
                <CFormLabel for="email" class="col-sm-3 col-form-label required">
                  생년월일
                </CFormLabel>
                <CCol sm="9">
                  <DatePicker
                    v-model="form.birth_date"
                    placeholder="생년월일을 입력하세요"
                    maxlength="10"
                    id="birth_date"
                  />
                  <CFormFeedback invalid>생년월일을 입력하세요.</CFormFeedback>
                </CCol>
              </CRow>

              <CRow class="mb-3">
                <CFormLabel
                  for="password"
                  class="col-sm-3 col-form-label"
                  :class="{ required: !userInfo }"
                >
                  휴대전화
                </CFormLabel>
                <CCol>
                  <input
                    v-model="form.cell_phone"
                    v-maska
                    data-maska="['###-###-####', '###-####-####']"
                    type="text"
                    class="form-control"
                    placeholder="휴대전화를 입력하세요"
                    maxlength="13"
                    id="cell_phone"
                  />
                  <CFormFeedback invalid>휴대전화를 입력하세요.</CFormFeedback>
                </CCol>
              </CRow>
            </CCardBody>
          </CCard>

          <!-- Mail Notifications Card -->
          <CCard class="mb-4">
            <CCardHeader class="font-weight-bold">
              <v-icon icon="mdi-cog" class="mr-1" color="primary" />
              업무 및 알림 설정
            </CCardHeader>
            <CCardBody>
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
  </div>
</template>
