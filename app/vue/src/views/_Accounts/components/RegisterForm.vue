<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { isValidate, message } from '@/utils/helper'

defineProps({
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['on-submit'])

const showPassword = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  passwordConfirm: '',
})

const validated = ref(false)

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (form.password !== form.passwordConfirm) {
      validated.value = false
      message('warning', '', '비밀번호가 일치하지 않습니다.')
      return
    }
    emit('on-submit', {
      username: form.username.trim(),
      email: form.email.trim(),
      password: form.password,
      passwordConfirm: form.passwordConfirm,
    })
    validated.value = false
  }
}

const router = useRouter()
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <h1>회원가입</h1>
    <p class="text-muted">Create your account</p>
    <CInputGroup class="mb-3">
      <CInputGroupText>
        <CIcon icon="cil-user" />
      </CInputGroupText>
      <CFormInput
        v-model="form.username"
        autocomplete="name"
        placeholder="실명을 입력해주세요"
        required
      />
      <CFormFeedback invalid>실명(사용자명)을 입력하세요.</CFormFeedback>
    </CInputGroup>

    <CInputGroup class="mb-3">
      <CInputGroupText>@</CInputGroupText>
      <CFormInput
        v-model="form.email"
        type="email"
        autocomplete="email"
        placeholder="이메일을 입력해주세요"
        required
      />
      <CFormFeedback invalid>이메일을 입력하세요.</CFormFeedback>
    </CInputGroup>

    <CInputGroup class="mb-3">
      <CInputGroupText>
        <CIcon icon="cil-lock-locked" />
      </CInputGroupText>
      <CFormInput
        v-model="form.password"
        :type="showPassword ? 'text' : 'password'"
        autocomplete="new-password"
        placeholder="비밀번호를 입력해주세요"
        required
      />
      <CButton
        type="button"
        color="secondary"
        variant="outline"
        id="button-addon1"
        @click="showPassword = !showPassword"
      >
        <v-icon :icon="!showPassword ? 'mdi-eye' : 'mdi-eye-off'" />
      </CButton>
      <CFormFeedback invalid>비밀번호를 입력하세요.</CFormFeedback>
    </CInputGroup>

    <CInputGroup class="mb-4">
      <CInputGroupText>
        <CIcon icon="cil-lock-locked" />
      </CInputGroupText>
      <CFormInput
        v-model="form.passwordConfirm"
        :type="showPassword ? 'text' : 'password'"
        autocomplete="new-password"
        placeholder="비밀번호 확인"
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
      <CFormFeedback invalid>비밀번호를 한번 더 입력하세요.</CFormFeedback>
    </CInputGroup>

    <CRow>
      <CCol class="d-grid">
        <v-btn type="submit" size="large" color="primary" :loading="loading" :disabled="loading">
          회원 가입
        </v-btn>
      </CCol>
    </CRow>

    <CRow>
      <CCol class="text-end">
        <CButton type="button" color="link" class="px-0" @click="router.push({ name: 'Login' })">
          로그인하러 가기
        </CButton>
      </CCol>
    </CRow>
  </CForm>
</template>
