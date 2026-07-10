<script lang="ts" setup>
import { computed, onBeforeMount, ref, reactive, watch } from 'vue'
import { onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'
import { generatePassword } from '@/utils/helper.ts'
import { useAccount } from '@/store/pinia/account'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const refAlertModal = ref()
const refConfirmModal = ref()

const menu = ref<'일반' | '프로젝트'>('일반')

const accStore = useAccount()
const user = computed(() => accStore.user)

const [route, router] = [useRoute(), useRouter()]

const form = reactive({
  email: '',
  username: '',
  password: '',
  pass_conf: '',

  is_active: true,
  is_staff: false,
  work_manager: false,

  // Notification fields (creation only)
  mail_sending: true,
  send_option: '1',
  expired: 24,
})

const formCheck = computed(() => {
  if (user.value) {
    const a = !form.password
    const b = form.is_active === user.value.is_active
    const c = form.is_staff === user.value.is_staff
    const d = form.work_manager === user.value.work_manager
    return a && b && c && d
  } else return false
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
    form.work_manager = user.value.work_manager
  } else {
    form.username = ''
    form.email = ''
    form.password = ''
    form.pass_conf = ''
    form.is_active = true
    form.is_staff = false
    form.work_manager = false
  }
  form.mail_sending = !user.value || !!form.password
  form.send_option = '1'
  form.expired = 24
}

watch(user, () => formDataSetup())
watch(form, val => (form.mail_sending = !user.value || !!val.password))

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
    refAlertModal.value.callModal('', '비밀번호가 일치하지 않습니다.')
    return
  }

  refConfirmModal.value.callModal()
}

const onSubmitConfirm = async () => {
  try {
    if (!user.value) {
      // Create user
      const payload = {
        email: form.email,
        username: form.username,
        password: form.password,
        mail_sending: form.mail_sending,
        send_option: form.send_option as '1' | '2',
        expired: form.expired,
      }
      await accStore.adminCreateUser(payload)
    } else {
      // Edit User account info
      const userPayload: any = {
        email: form.email,
        // 비밀번호 관련 필드는 명시적으로 입력했을 때만 포함
        ...(form.password && {
          password: form.password,
          mail_sending: form.mail_sending,
          send_option: form.send_option,
          expired: form.expired,
        }),
        // 권한 필드는 항상 전송 (기존 값 유지)
        is_active: form.is_active,
        is_staff: form.is_staff,
        work_manager: form.work_manager,
      }
      if (form.password) {
        userPayload.password = form.password
      }
      await accStore.adminUpdateUser(userPayload)
    }

    validated.value = false
    refConfirmModal.value.close()
    // await router.push({ name: '사용자' })
  } catch (err: any) {
    console.error(err)
    refAlertModal.value.callModal('', '사용자 정보 저장 중 오류가 발생했습니다.')
  }
}

onBeforeMount(async () => {
  if (route.params.userId) await accStore.fetchUser(Number(route.params.userId))
  else accStore.user = null

  await formDataSetup()
})

onBeforeRouteUpdate(async to => {
  if (to.params.userId) await accStore.fetchUser(Number(to.params.userId))
  else accStore.user = null

  await formDataSetup()
})
</script>

<template>
  <CRow class="py-2">
    <CCol class="mb-2">
      <span class="h5 mr-2">
        <router-link :to="{ name: '사용자' }">사용자</router-link>
      </span>
      <span class="mr-2">»</span>
      <span class="h5">{{ user?.pk ? user.username : '새 사용자' }}</span>
    </CCol>

    <CCol v-if="user?.pk" class="text-right form-text">
      <span class="mr-2">
        <TextButton
          name="사용자 정보"
          icon="mdi-account"
          :to="{ name: '사용자 - 보기', params: { userId: user.pk } }"
        />
      </span>
    </CCol>
  </CRow>

  <!-- Edit Mode Tabs -->
  <CRow v-if="user?.pk" class="mb-3">
    <CCol>
      <v-tabs v-model="menu" density="compact">
        <v-tab value="일반" variant="tonal"> 일반</v-tab>
        <v-tab value="프로젝트" variant="tonal"> 프로젝트</v-tab>
      </v-tabs>
    </CCol>
  </CRow>

  <CRow v-if="menu === '일반'">
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
                  <CFormLabel for="username" class="col-sm-3 col-form-label required">
                    아이디
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
                      :disabled="!!user"
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
                    <v-btn
                      color="info"
                      size="small"
                      class="mt-1"
                      @click="genPass = generatePassword()"
                    >
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
                <v-divider v-if="user?.pk" class="my-4" />
                <CRow v-if="user?.pk" class="mb-3">
                  <CFormLabel class="col-sm-3 col-form-label">권한 및 상태</CFormLabel>
                  <CCol sm="9" class="pt-2">
                    <CRow>
                      <CCol xs="4" class="mb-2">
                        <v-checkbox
                          id="is_active"
                          v-model="form.is_active"
                          color="info"
                          label="활성 사용자"
                          density="compact"
                          messages="사이트 접속 권한"
                        />
                      </CCol>
                      <CCol xs="4" class="mb-2">
                        <v-checkbox
                          id="is_staff"
                          v-model="form.is_staff"
                          color="primary"
                          label="스태프 권한"
                          density="compact"
                          messages="관리자페이지 접속 권한"
                        />
                      </CCol>

                      <CCol xs="4" class="mb-2">
                        <v-checkbox
                          id="work_manager"
                          v-model="form.work_manager"
                          color="success"
                          label="업무관리자"
                          density="compact"
                          messages="업무시스템 관리자"
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
            <v-icon icon="mdi-email-arrow-right-outline" class="mr-1" color="primary" />
            알림 메일 발송 설정
          </CCardHeader>
          <CCardBody>
            <div>
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
          </CCardBody>
        </CCard>

        <!-- Submit & Cancel Footer -->
        <div class="text-right mb-4">
          <v-btn type="submit" :disabled="formCheck" color="primary"> 저장</v-btn>
          <v-btn color="light" class="mr-2" @click="router.push({ name: '사용자' })" flat>
            취소
          </v-btn>
        </div>
      </CCol>
    </CForm>
  </CRow>

  <CRow v-else>
    <CCol>
      <!-- Project Tab (Placeholder or configuration) -->
      <CRow v-if="menu === '프로젝트' && user">
        <CCol lg="12">
          <CCard>
            <CCardHeader class="font-weight-bold">
              <v-icon icon="mdi-shield-account" class="mr-1" color="orange" />
              프로젝트 권한 설정
            </CCardHeader>
            <CCardBody class="text-center py-5">
              <span class="text-grey-darken-1">
                프로젝트 권한 관리 및 소속 제어는 상단 관리자 설정 메뉴를 통해 관리할 수 있습니다.
              </span>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>
    </CCol>
  </CRow>

  <ConfirmModal ref="refConfirmModal">
    <template #default> 사용자 정보를 저장하시겠습니까? </template>
    <template #footer>
      <v-btn color="success" size="small" @click="onSubmitConfirm">저장</v-btn>
    </template>
  </ConfirmModal>
  <AlertModal ref="refAlertModal" />
</template>
