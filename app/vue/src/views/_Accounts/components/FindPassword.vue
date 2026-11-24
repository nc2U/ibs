<script lang="ts" setup>
import { ref } from 'vue'
import { isValidate } from '@/utils/helper'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

defineProps({
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['on-submit', 'to-login'])

const confModal = ref()
const email = ref('')
const validated = ref(false)

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    confModal.value?.callModal()
    validated.value = false
  }
}

const modalAction = () => {
  confModal.value?.close()
  emit('on-submit', { email: email.value.trim() })
}

const toLogin = () => emit('to-login')
</script>

<template>
  <CForm novalidate :validated="validated" class="needs-validation" @submit.prevent="onSubmit">
    <CRow>
      <CCol><h3>비밀번호 찾기</h3></CCol>
    </CRow>
    <v-divider />
    <p class="text-medium-emphasis">
      가입하신 이메일 주소를 입력해 주세요.<br />
      이메일 주소로 비밀번호를 재설정할 수 있는 링크를 보내드립니다.
    </p>
    <p class="text-medium-emphasis mb-4">비밀번호 재설정 링크는 10분 간 유효합니다.</p>
    <CInputGroup class="mb-3">
      <CInputGroupText>
        <CIcon icon="cil-user" />
      </CInputGroupText>
      <CFormInput
        v-model="email"
        type="email"
        autocomplete="email"
        placeholder="이메일주소를 입력해주세요"
        required
      />
      <CFormFeedback invalid>가입 시 등록한 이메일을 입력하세요.</CFormFeedback>
    </CInputGroup>

    <CRow>
      <CCol xs="12" class="d-grid">
        <v-btn
          color="info"
          class="px-4"
          size="large"
          type="submit"
          :loading="loading"
          :disabled="loading"
        >
          이메일 전송하기
        </v-btn>
      </CCol>
    </CRow>
    <CRow>
      <CCol class="text-end">
        <CButton type="button" color="link" class="px-0" @click="toLogin">
          로그인 화면으로
        </CButton>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="confModal">
    <template #header>비밀번호 재설정 확인</template>
    <template #default> 비밀번호 재설정을 위한 이메일을 전송하시겠습니까?</template>
    <template #footer>
      <v-btn color="info" :loading="loading" :disabled="loading" @click="modalAction">확인</v-btn>
    </template>
  </ConfirmModal>
</template>
