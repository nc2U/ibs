<script lang="ts" setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import AlertModal from '@/components/Modals/AlertModal.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import { CModal } from '@coreui/vue'

const refAlertModal = ref()

const router = useRouter()
const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)
const usernameVal = computed(() => userInfo.value?.username || '')

const validated = ref(false)
const showPassword = ref(false)

const form = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const isResetModalOpen = ref(false)
const resetEmail = ref('')
const isSendingReset = ref(false)

const openResetModal = () => {
  resetEmail.value = userInfo.value?.email || ''
  isResetModalOpen.value = true
}

const handleSendResetEmail = async () => {
  if (!resetEmail.value || !resetEmail.value.includes('@')) {
    refAlertModal.value.callModal('', '유효한 이메일 주소를 입력해주세요.')
    return
  }
  isSendingReset.value = true
  try {
    await accStore.passReset({ email: resetEmail.value.trim() })
    isResetModalOpen.value = false
  } finally {
    isSendingReset.value = false
  }
}

const onSubmit = async (event: Event) => {
  const e = event.currentTarget as HTMLInputElement
  if (!e.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()

    validated.value = true
  } else {
    if (form.new_password === form.confirm_password) {
      if (await accStore.changePassword(form)) {
        setTimeout(() => {
          router.push({ name: 'Login' })
        }, 1000)
      }
    } else {
      refAlertModal.value.callModal('', '비밀번호가 서로 다릅니다.')
    }
  }
}
</script>

<template>
  <CRow class="py-2">
    <CCol class="mb-2">
      <span class="h5 mr-2"> 비밀번호 변경 </span>
    </CCol>

    <CCol class="text-right form-text">
      <span class="mr-2">
        <TextButton
          name="내 계정"
          :to="{ name: '사용자 - 내 계정' }"
          icon="mdi-pencil"
          icon-color="amber"
        />
      </span>
    </CCol>
  </CRow>

  <CRow>
    <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
      <CCol>
        <CCard class="mb-4">
          <CCardHeader class="font-weight-bold">
            <v-icon icon="mdi-key" class="mr-1" color="warning" />
            비밀번호 변경
          </CCardHeader>
          <CCardBody>
            <CRow class="pl-4 pt-3 mb-3">
              <CFormLabel class="col-sm-4 col-lg-2 col-form-label">이름</CFormLabel>
              <CCol sm="6" lg="4" xl="2" class="pt-2">{{ usernameVal }}</CCol>
            </CRow>

            <CRow class="pl-4 my-3">
              <CFormLabel class="col-sm-4 col-lg-2 col-form-label"> 현재 비밀번호 </CFormLabel>
              <CCol sm="6" lg="4" xl="3">
                <CInputGroup>
                  <CFormInput
                    v-model="form.old_password"
                    :type="!showPassword ? 'password' : ''"
                    required
                    placeholder="현재 패스워드"
                    aria-label="password"
                    aria-describedby="password"
                  />
                  <v-btn
                    type="button"
                    color="secondary"
                    variant="outlined"
                    @click="showPassword = !showPassword"
                  >
                    <v-icon :icon="!showPassword ? 'mdi-eye' : 'mdi-eye-off'" />
                  </v-btn>
                  <CFormFeedback invalid>현재 비밀번호를 입력하세요.</CFormFeedback>
                </CInputGroup>
                <div class="mt-1 text-right">
                  <a
                    href="javascript:void(0)"
                    class="text-decoration-none small text-primary"
                    @click="openResetModal"
                  >
                    <v-icon icon="mdi-help-circle-outline" size="14" class="mr-1" />
                    비밀번호를 잊으셨나요?
                  </a>
                </div>
              </CCol>
            </CRow>
            <CRow class="pl-4 my-3">
              <CFormLabel class="col-sm-4 col-lg-2 col-form-label">새로운 비밀번호</CFormLabel>
              <CCol sm="6" lg="4" xl="3">
                <CInputGroup>
                  <CFormInput
                    v-model="form.new_password"
                    :type="!showPassword ? 'password' : ''"
                    required
                    placeholder="새로운 패스워드"
                    aria-label="password"
                    aria-describedby="password"
                  />
                  <v-btn
                    type="button"
                    color="secondary"
                    variant="outlined"
                    @click="showPassword = !showPassword"
                  >
                    <v-icon :icon="!showPassword ? 'mdi-eye' : 'mdi-eye-off'" />
                  </v-btn>
                  <CFormFeedback invalid>새로운 비밀번호를 입력하세요.</CFormFeedback>
                </CInputGroup>
              </CCol>
            </CRow>
            <CRow class="pl-4 my-3">
              <CFormLabel class="col-sm-4 col-lg-2 col-form-label">비밀번호 확인</CFormLabel>
              <CCol sm="6" lg="4" xl="3">
                <CInputGroup>
                  <CFormInput
                    v-model="form.confirm_password"
                    :type="!showPassword ? 'password' : ''"
                    required
                    placeholder="패스워드 재입력"
                    aria-label="password"
                    aria-describedby="password"
                  />
                  <v-btn
                    type="button"
                    color="secondary"
                    variant="outlined"
                    @click="showPassword = !showPassword"
                  >
                    <v-icon :icon="!showPassword ? 'mdi-eye' : 'mdi-eye-off'" />
                  </v-btn>
                  <CFormFeedback invalid>비밀번호를 한번 더 입력하세요.</CFormFeedback>
                </CInputGroup>
              </CCol>
            </CRow>
            <CRow class="pl-4 mb-3">
              <CCol class="col-sm-4 col-lg-2"></CCol>
              <CCol sm="6" lg="4" xl="3" class="text-right">
                <v-btn type="submit" color="success">수정하기</v-btn>
                <v-btn color="light" @click="router.back()" flat>취소</v-btn>
              </CCol>
            </CRow>
          </CCardBody>
        </CCard>
      </CCol>
    </CForm>
  </CRow>

  <!-- 비밀번호 재설정 이메일 발송 모달 -->
  <CModal :visible="isResetModalOpen" @close="isResetModalOpen = false" alignment="center">
    <CModalHeader>
      <CModalTitle>
        <v-icon icon="mdi-email-lock-outline" class="mr-1" color="primary" />
        비밀번호 재설정 링크 발송
      </CModalTitle>
    </CModalHeader>
    <CModalBody>
      <p class="text-medium-emphasis small mb-3">
        가입된 이메일 주소로 비밀번호 재설정 링크가 포함된 메일을 발송합니다.<br />
        메일 수신 후 안내 링크를 통해 새로운 비밀번호를 설정하실 수 있습니다.
      </p>
      <CFormLabel class="font-weight-bold">이메일 주소</CFormLabel>
      <CFormInput
        v-model="resetEmail"
        type="email"
        placeholder="이메일 주소 입력"
        :disabled="isSendingReset"
      />
    </CModalBody>
    <CModalFooter>
      <CButton color="secondary" variant="ghost" @click="isResetModalOpen = false"> 취소 </CButton>
      <CButton color="primary" :disabled="isSendingReset" @click="handleSendResetEmail">
        <CSpinner v-if="isSendingReset" size="sm" class="mr-1" />
        발송하기
      </CButton>
    </CModalFooter>
  </CModal>

  <AlertModal ref="refAlertModal" />
</template>
