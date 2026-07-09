<script lang="ts" setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import AlertModal from '@/components/Modals/AlertModal.vue'

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
              <CFormLabel class="col-sm-4 col-lg-2 col-form-label">현재 비밀번호</CFormLabel>
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

  <AlertModal ref="refAlertModal" />
</template>
