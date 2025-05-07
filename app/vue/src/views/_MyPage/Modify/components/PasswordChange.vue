<script lang="ts" setup>
import { ref, reactive } from 'vue'

defineProps({ username: String })
const emit = defineEmits(['change-password'])

const validated = ref(false)
const showPassword = ref(false)
const confirm_message = ref('비밀번호를 한번 더 입력하세요.')

const form = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const onSubmit = (event: Event) => {
  const e = event.currentTarget as HTMLInputElement
  if (!e.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()

    validated.value = true
  } else {
    if (form.new_password === form.confirm_password) emit('change-password', form)
    else alert('비밀번호가 서로 다릅니다.')
  }
}
</script>

<template>
  <CCardBody class="p-5">
    <CRow>
      <CCol><h5>회원 비밀번호 변경</h5></CCol>
    </CRow>

    <v-divider />

    <CForm
      class="needs-validation px-5"
      novalidate
      :validated="validated"
      @submit.prevent="onSubmit"
    >
      <CRow class="pt-3 mb-3">
        <CFormLabel class="col-sm-4 col-lg-2 col-form-label">이름</CFormLabel>
        <CCol sm="6" lg="4" xl="2" class="pt-2">{{ username }}</CCol>
      </CRow>

      <CRow class="my-3">
        <CFormLabel class="col-sm-4 col-lg-2 col-form-label">현재비밀번호</CFormLabel>
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
              id="button-addon2"
              @click="showPassword = !showPassword"
            >
              <v-icon :icon="!showPassword ? 'mdi-eye' : 'mdi-eye-off'" />
            </v-btn>
            <CFormFeedback invalid>현재 비밀번호를 입력하세요.</CFormFeedback>
          </CInputGroup>
        </CCol>
      </CRow>
      <CRow class="my-3">
        <CFormLabel class="col-sm-4 col-lg-2 col-form-label">새로운비밀번호</CFormLabel>
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
              id="button-addon2"
              @click="showPassword = !showPassword"
            >
              <v-icon :icon="!showPassword ? 'mdi-eye' : 'mdi-eye-off'" />
            </v-btn>
            <CFormFeedback invalid>새로운 비밀번호를 입력하세요.</CFormFeedback>
          </CInputGroup>
        </CCol>
      </CRow>
      <CRow class="my-3">
        <CFormLabel class="col-sm-4 col-lg-2 col-form-label">재입력</CFormLabel>
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
              id="button-addon2"
              @click="showPassword = !showPassword"
            >
              <v-icon :icon="!showPassword ? 'mdi-eye' : 'mdi-eye-off'" />
            </v-btn>
            <CFormFeedback invalid>비밀번호를 한번 더 입력하세요.</CFormFeedback>
          </CInputGroup>
        </CCol>
      </CRow>
      <CRow class="mb-3">
        <CCol class="col-sm-4 col-lg-2"></CCol>
        <CCol sm="6" lg="4" xl="3" class="text-right">
          <v-btn type="submit" color="success">수정하기</v-btn>
        </CCol>
      </CRow>
    </CForm>
  </CCardBody>
</template>
