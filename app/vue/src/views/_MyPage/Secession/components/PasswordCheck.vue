<script lang="ts" setup>
import { ref } from 'vue'

defineProps({ username: { type: String, default: '' } })
const emit = defineEmits(['remove-confirm'])

const validated = ref(false)
const password = ref('')
const showPassword = ref(false)

const onSubmit = (event: Event) => {
  const e = event.currentTarget as HTMLInputElement
  if (!e.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()

    validated.value = true
  } else emit('remove-confirm', password.value)
}

const passReset = () => (password.value = '')
const getPass = () => password.value
defineExpose({ passReset, getPass })
</script>

<template>
  <CCardBody class="p-5">
    <CRow>
      <CCol><h5>회원 비밀번호 확인</h5></CCol>
    </CRow>

    <v-divider />

    <CAlert color="danger">
      회원 탈퇴를 위한 패스워드 입력페이지입니다.<br />
      패스워드를 입력하시면 회원탈퇴가 진행됩니다. <br />
      탈퇴한 회원정보는 복구할 수 없으므로, 신중히 선택하여 주시기 바랍니다.
    </CAlert>

    <CForm
      class="needs-validation px-5"
      novalidate
      :validated="validated"
      @submit.prevent="onSubmit"
    >
      <CRow class="pt-3 mb-3">
        <CFormLabel class="col-sm-2 col-lg-1 col-form-label">이름</CFormLabel>
        <CCol sm="6" lg="4" xl="3" class="pt-2">{{ username }}</CCol>
      </CRow>

      <CRow class="my-3">
        <CFormLabel class="col-sm-2 col-lg-1 col-form-label">패스워드</CFormLabel>
        <CCol sm="6" lg="4" xl="3">
          <CInputGroup>
            <CFormInput
              v-model="password"
              :type="!showPassword ? 'password' : ''"
              required
              placeholder="패스워드 입력"
              aria-label="password"
              aria-describedby="password"
            />
            <CButton
              type="button"
              color="secondary"
              variant="outline"
              id="button-addon2"
              @click="showPassword = !showPassword"
            >
              <v-icon :icon="!showPassword ? 'mdi-eye' : 'mdi-eye-off'" />
            </CButton>
          </CInputGroup>
          <div class="form-text">
            외부로부터 회원님의 정보를 안전하게 보호하기 위해 비밀번호를 확인하셔야 합니다.
          </div>
        </CCol>
      </CRow>
      <CRow class="mb-3">
        <CCol class="col-sm-2 col-lg-1"></CCol>
        <CCol sm="6" lg="4" xl="3" class="text-right">
          <v-btn type="submit" color="danger">확인</v-btn>
        </CCol>
      </CRow>
    </CForm>
  </CCardBody>
</template>
