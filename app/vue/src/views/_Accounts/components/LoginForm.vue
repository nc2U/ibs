<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const [route, router] = [useRoute(), useRouter()]
const emit = defineEmits(['on-submit', 'find-email', 'find-pass'])

const email = ref('')
const password = ref('')
const redirect = ref()
const validated = ref(false)
const showPassword = ref(false)

const onSubmit = (event: Event) => {
  const el = event.currentTarget as HTMLInputElement
  if (!el.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()

    validated.value = true
  } else {
    emit('on-submit', {
      email: email.value,
      password: password.value,
      redirect: redirect.value,
    })
    validated.value = false
  }
}

const toRegister = () => {
  router.push({ name: 'Register' })
}

const toFindEmail = () => emit('find-email')

const toFindPassword = () => emit('find-pass')

onMounted(() => (redirect.value = route.query?.redirect))
</script>

<template>
  <CForm novalidate :validated="validated" class="needs-validation" @submit.prevent="onSubmit">
    <h1>로그인</h1>
    <p class="text-muted">Sign In to your account</p>
    <CInputGroup class="mb-3">
      <CInputGroupText>
        <CIcon icon="cil-user" />
      </CInputGroupText>
      <CFormInput
        v-model="email"
        type="email"
        auto-complete="username email"
        placeholder="이메일주소를 입력해주세요"
        required
      />
      <CFormFeedback invalid>이메일을 입력하세요.</CFormFeedback>
    </CInputGroup>
    <CInputGroup class="mb-4">
      <CInputGroupText>
        <CIcon icon="cil-lock-locked" />
      </CInputGroupText>
      <CFormInput
        v-model="password"
        :type="!showPassword ? 'password' : ''"
        auto-complete="current-password"
        placeholder="비밀번호를 입력해주세요"
        required
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
      <CFormFeedback invalid>비밀번호를 입력하세요.</CFormFeedback>
    </CInputGroup>
    <CRow>
      <CCol xs="7">
        <CButton type="button" color="link" class="px-0" @click="toFindPassword">
          비밀번호 찾기
        </CButton>
      </CCol>
      <CCol class="text-right">
        <CButton type="button" color="link" class="px-0" @click="toRegister">
          회원가입 하기
        </CButton>
      </CCol>
      <CCol xs="12" class="d-grid">
        <v-btn color="primary" size="large" type="submit">로그인</v-btn>
      </CCol>
    </CRow>
  </CForm>
</template>
