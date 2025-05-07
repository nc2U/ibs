<script lang="ts" setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from '@/utils/helper'

const emit = defineEmits(['on-submit'])

const form = reactive({
  password: '',
  passwordConfirm: '',
})

const validated = ref(false)

const onSubmit = (event: Event) => {
  const el = event.currentTarget as HTMLInputElement
  if (!el.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()

    validated.value = true
  } else {
    if (form.password === form.passwordConfirm) {
      emit('on-submit', form.password)
      validated.value = false
    } else message('warning', '', '입력하신 비밀번호가 서로 같지 않습니다.')
  }
}

const router = useRouter()
</script>

<template>
  <CForm novalidate :validated="validated" class="needs-validation" @submit.prevent="onSubmit">
    <CRow>
      <CCol><h3>비밀번호 변경</h3></CCol>
    </CRow>

    <v-divider />

    <p class="text-muted mb-4">계정의 새 비밀번호를 설정합니다.</p>

    <CInputGroup class="mb-3">
      <CInputGroupText>
        <CIcon icon="cil-lock-locked" />
      </CInputGroupText>
      <CFormInput
        ref="passwordForm"
        v-model="form.password"
        type="password"
        autocomplete="password"
        placeholder="새 비밀번호"
        required
      />
      <CFormFeedback invalid>새 비밀번호를 입력하세요.</CFormFeedback>
    </CInputGroup>

    <CInputGroup class="mb-4">
      <CInputGroupText>
        <CIcon icon="cil-lock-locked" />
      </CInputGroupText>
      <CFormInput
        v-model="form.passwordConfirm"
        type="password"
        autocomplete="password-confirm"
        placeholder="비밀번호 확인"
        required
      />
      <CFormFeedback invalid>비밀번호를 한번 더 입력하세요.</CFormFeedback>
    </CInputGroup>

    <CRow>
      <CCol xs="12" class="d-grid">
        <v-btn color="info" size="large" class="px-4" type="submit">비밀번호 제출</v-btn>
      </CCol>
    </CRow>
    <CRow>
      <CCol class="text-right">
        <CButton type="button" color="link" class="px-0" @click="router.replace({ name: 'Login' })">
          로그인 화면으로
        </CButton>
      </CCol>
    </CRow>
  </CForm>
</template>
