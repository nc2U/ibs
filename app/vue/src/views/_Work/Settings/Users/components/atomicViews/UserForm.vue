<script lang="ts" setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { generatePassword, isValidate } from '@/utils/helper'
import { useAccount } from '@/store/pinia/account'
import type { User } from '@/store/types/accounts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps<{ user: User | null }>()

const validated = ref(false)

const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)
const refConfirmModal = ref<InstanceType<typeof ConfirmModal> | null>(null)

const router = useRouter()

const accStore = useAccount()
const superAuth = computed(() => !!accStore.superAuth)
const isSelf = computed(() => !!props.user?.pk && props.user.pk === accStore.userInfo?.pk)

const form = reactive({
  email: '',
  username: '',
  password: '',
  pass_conf: '',

  is_active: true,
  is_staff: false,
  work_manager: false,

  // Notification fields
  mail_sending: true,
  send_option: '1' as '1' | '2',
  expired: 24,
})

// 수정 모드에서 '재설정 링크 포함 메일 발송' 선택 시 비밀번호 직접 입력은 비활성화
const isEditResetLinkMode = computed(
  () => !!props.user?.pk && form.mail_sending && form.send_option === '1',
)

watch(isEditResetLinkMode, active => {
  if (active) {
    form.password = ''
    form.pass_conf = ''
  }
})

const formCheck = computed(() => {
  if (props.user) {
    const noPasswordChange = !form.password
    const noResetLinkSend = !(form.mail_sending && form.send_option === '1')
    const sameActive = form.is_active === props.user.is_active
    const sameStaff = form.is_staff === props.user.is_staff
    const sameManager = form.work_manager === props.user.work_manager
    return noPasswordChange && noResetLinkSend && sameActive && sameStaff && sameManager
  } else return false
})

const formDataSetup = () => {
  validated.value = false
  if (props.user) {
    form.username = props.user.username || ''
    form.email = props.user.email || ''
    form.password = ''
    form.pass_conf = ''
    form.is_active = props.user.is_active
    form.is_staff = props.user.is_staff
    form.work_manager = props.user.work_manager
    form.mail_sending = false
  } else {
    form.username = ''
    form.email = ''
    form.password = ''
    form.pass_conf = ''
    form.is_active = true
    form.is_staff = false
    form.work_manager = false
    form.mail_sending = true
  }
  form.send_option = '1'
  form.expired = 24
}

watch(
  () => props.user,
  () => formDataSetup(),
  { immediate: true },
)

const genPass = ref('')

const applyGen = () => {
  if (isEditResetLinkMode.value) {
    form.send_option = '2'
  }
  form.password = genPass.value
  form.pass_conf = genPass.value
  genPass.value = ''
}

const onSubmit = async (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
    return
  }

  if (props.user?.pk && form.mail_sending && form.send_option === '2' && !form.password) {
    refAlertModal.value?.callModal('', '비밀번호 포함 메일을 발송하려면 새 비밀번호를 입력하세요.')
    return
  }

  if (form.password && form.password !== form.pass_conf) {
    refAlertModal.value?.callModal('', '비밀번호가 일치하지 않습니다.')
    return
  }

  refConfirmModal.value?.callModal()
}

const onSubmitConfirm = async () => {
  try {
    if (!props.user) {
      // Create user
      const payload = {
        email: form.email,
        username: form.username,
        password: form.password,
        mail_sending: form.mail_sending,
        send_option: form.send_option,
        expired: form.expired,
      }
      const created = await accStore.adminCreateUser(payload)
      if (!created) return
      validated.value = false
      refConfirmModal.value?.close()
      if (created.pk) {
        await router.push({ name: '사용자 - 수정', params: { userId: created.pk } })
      } else {
        await router.push({ name: '사용자' })
      }
    } else {
      // Edit User account info
      const userPayload: any = {
        email: form.email,
        is_active: form.is_active,
        work_manager: form.work_manager,
        ...(superAuth.value ? { is_staff: form.is_staff } : {}),
        mail_sending: form.mail_sending,
        ...(form.mail_sending
          ? { send_option: form.send_option, expired: form.expired }
          : {}),
        ...(!isEditResetLinkMode.value && form.password ? { password: form.password } : {}),
      }
      const updated = await accStore.adminUpdateUser(userPayload)
      if (!updated) return
      form.password = ''
      form.pass_conf = ''
      form.mail_sending = false
      validated.value = false
      refConfirmModal.value?.close()
      if (props.user.pk) {
        await accStore.fetchUser(props.user.pk)
      }
    }
  } catch (err: any) {
    console.error(err)
    refAlertModal.value?.callModal('', '사용자 정보 저장 중 오류가 발생했습니다.')
  }
}
</script>

<template>
  <CForm class="row needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CCol class="col-lg-6">
      <CRow>
        <CCol lg="12">
          <!-- Account Info Card -->
          <CCard class="mb-4">
            <CCardHeader class="fw-bold">
              <v-icon icon="mdi-account-cog" class="me-1" color="primary" />
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
                    :disabled="isEditResetLinkMode"
                    :required="!user"
                  />
                </CCol>
                <CCol sm="4">
                  <v-btn
                    color="info"
                    size="small"
                    class="mt-1"
                    :disabled="isEditResetLinkMode"
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
                    :disabled="isEditResetLinkMode"
                    :required="!user"
                  />
                </CCol>
                <CCol v-if="genPass" sm="4">
                  <div
                    class="p-1 mb-1 bg-yellow-lighten-1 text-center fw-bold"
                    style="width: 120px; display: inline-block; vertical-align: middle"
                  >
                    {{ genPass }}
                  </div>
                  <div style="display: inline-block; vertical-align: middle" class="ms-2">
                    <v-btn color="success" size="small" @click="applyGen">적용</v-btn>
                    <v-btn color="light" size="small" class="me-1" @click="genPass = ''" flat>
                      취소
                    </v-btn>
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
                        :disabled="isSelf"
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
                        :disabled="!superAuth || isSelf"
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
                        :disabled="isSelf && !superAuth"
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
        <CCardHeader class="fw-bold">
          <v-icon icon="mdi-email-arrow-right-outline" class="me-1" color="primary" />
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
                  :label="
                    user?.pk
                      ? '사용자에게 비밀번호 안내 메일 보내기'
                      : '새로 생성한 사용자에게 알림 메일 보내기'
                  "
                />
              </CCol>
            </CRow>

            <CRow class="ps-4">
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
                <div v-if="isEditResetLinkMode" class="form-text ms-4">
                  재설정 링크 발송 시 사용자가 직접 새 비밀번호를 설정합니다.
                </div>
              </CCol>

              <CRow class="mb-3">
                <CCol sm="4" class="ps-5 pt-1">
                  <span>링크 만료 시간 : </span>
                </CCol>
                <CCol sm="4">
                  <CFormSelect
                    v-model.number="form.expired as any"
                    size="sm"
                    :disabled="!form.mail_sending || form.send_option !== '1'"
                  >
                    <option v-for="i in 24" :value="i" :key="i">
                      {{ String(i).padStart(2, '0') }}
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
      <div class="text-end mb-4">
        <v-btn type="submit" :color="user?.pk ? 'success' : 'primary'" :disabled="formCheck">
          저장
        </v-btn>
        <v-btn color="light" class="ms-2" @click="router.push({ name: '사용자' })" flat>
          취소
        </v-btn>
      </div>
    </CCol>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #icon>
      <v-icon icon="mdi-mail" size="22" color="indigo" class="me-2" />
    </template>
    <template #header>사용자 정보 전송 확인</template>
    <template #default> 변경된 사용자 정보를 전송하시겠습니까? </template>
    <template #footer>
      <v-btn color="success" size="small" @click="onSubmitConfirm">보내기</v-btn>
    </template>
  </ConfirmModal>
  <AlertModal ref="refAlertModal" />
</template>
