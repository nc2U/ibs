<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { generatePassword, isValidate } from '@/utils/helper'
import FormModal from '@/components/Modals/FormModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const emit = defineEmits<{
  'on-created': [pk: number]
}>()

const accStore = useAccount()

const refFormModal = ref<InstanceType<typeof FormModal> | null>(null)
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)

const form = reactive({
  username: '',
  email: '',
  password: '',
  pass_conf: '',
  mail_sending: true,
  send_option: '1' as '1' | '2',
  expired: 24,
})

const genPass = ref('')
const validated = ref(false)
const isSubmitting = ref(false)

const formReset = () => {
  form.username = ''
  form.email = ''
  form.password = ''
  form.pass_conf = ''
  form.mail_sending = true
  form.send_option = '1'
  form.expired = 24
  genPass.value = ''
  validated.value = false
}

const onSubmit = async (event: Event) => {
  if (isSubmitting.value) return
  if (isValidate(event)) {
    validated.value = true
    return
  }

  if (form.password !== form.pass_conf) {
    refAlertModal.value?.callModal('알림', '비밀번호가 일치하지 않습니다.')
    return
  }

  isSubmitting.value = true
  try {
    const created = await accStore.adminCreateUser({
      username: form.username,
      email: form.email,
      password: form.password,
      mail_sending: form.mail_sending,
      send_option: form.send_option,
      expired: form.expired,
    })
    if (created?.pk) {
      formReset()
      refFormModal.value?.close()
      emit('on-created', created.pk)
    }
  } finally {
    isSubmitting.value = false
  }
}

const createRandomPassword = () => {
  genPass.value = generatePassword()
}

const applyGen = () => {
  form.password = genPass.value
  form.pass_conf = genPass.value
  genPass.value = ''
}

const callModal = () => {
  formReset()
  refFormModal.value?.callModal()
}

const closeModal = () => {
  formReset()
  refFormModal.value?.close()
}

defineExpose({ callModal, close: closeModal })
</script>

<template>
  <FormModal ref="refFormModal" @close="formReset">
    <template #icon>
      <v-icon icon="mdi-account-check" color="success" class="me-2" />
    </template>
    <template #header>새 사용자 생성</template>
    <template #default>
      <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
        <CModalBody class="text-body p-4">
          <CRow class="mb-3">
            <CFormLabel for="username" class="col-sm-3 col-form-label required">아이디</CFormLabel>
            <CCol sm="9">
              <CFormInput
                id="username"
                v-model="form.username"
                maxlength="30"
                placeholder="아이디"
                autocomplete="off"
                required
              />
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel for="email" class="col-sm-3 col-form-label required">이메일</CFormLabel>
            <CCol sm="9">
              <CFormInput
                id="email"
                v-model="form.email"
                type="email"
                maxlength="100"
                placeholder="이메일"
                required
              />
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel for="password" class="col-sm-3 col-form-label required">
              비밀번호
            </CFormLabel>
            <CCol sm="5">
              <CFormInput
                id="password"
                v-model="form.password"
                type="password"
                maxlength="20"
                placeholder="비밀번호"
                autocomplete="off"
                required
              />
            </CCol>
            <CCol sm="4">
              <v-btn
                type="button"
                color="info"
                size="small"
                class="mt-1"
                @click="createRandomPassword"
              >
                임의 패스워드 생성
              </v-btn>
            </CCol>
          </CRow>
          <CRow class="mb-4" style="min-height: 45px">
            <CFormLabel for="pass_conf" class="col-sm-3 col-form-label required">
              비밀번호 확인
            </CFormLabel>
            <CCol sm="5">
              <CFormInput
                id="pass_conf"
                v-model="form.pass_conf"
                type="password"
                maxlength="20"
                placeholder="비밀번호 확인"
                required
              />
            </CCol>
            <CCol v-if="genPass" sm="4" class="mt-2 mt-sm-0">
              <div
                class="p-1 mb-1 bg-warning-subtle text-body rounded text-center fw-bold text-break"
                style="min-width: 110px"
              >
                {{ genPass }}
              </div>
              <div class="d-flex gap-1">
                <v-btn type="button" color="light" size="x-small" @click="genPass = ''">취소</v-btn>
                <v-btn type="button" color="success" size="x-small" @click="applyGen">적용</v-btn>
              </div>
            </CCol>
          </CRow>

          <v-divider class="mb-4" />

          <CRow>
            <CCol class="mb-3">
              <CFormCheck
                id="inform-mail"
                v-model="form.mail_sending"
                type="checkbox"
                label="새로 생성한 사용자에게 알림 메일 보내기"
              />
            </CCol>
          </CRow>

          <CRow>
            <CCol sm="12" class="ps-5 mb-3">
              <CFormCheck
                id="content-option1"
                v-model="form.send_option"
                value="1"
                type="radio"
                name="content-option"
                label="패스워드 재설정 링크 포함"
                :disabled="!form.mail_sending"
              />
            </CCol>
            <CRow class="mb-3 align-items-center">
              <CCol sm="5" class="ps-5">
                <span class="ps-4">링크 만료 시간 : </span>
              </CCol>
              <CCol sm="4">
                <CFormSelect
                  :model-value="String(form.expired)"
                  size="sm"
                  :disabled="!form.mail_sending || form.send_option !== '1'"
                  @update:model-value="
                    val => (form.expired = !Array.isArray(val) && Number(val) ? Number(val) : 24)
                  "
                >
                  <option v-for="i in 24" :key="i" :value="String(i)">
                    {{ String(i).padStart(2, '0') }}
                  </option>
                </CFormSelect>
              </CCol>
              <CCol>시간</CCol>
            </CRow>
            <CCol sm="12" class="ps-5 mb-3">
              <CFormCheck
                id="content-option2"
                v-model="form.send_option"
                value="2"
                type="radio"
                name="content-option"
                label="사용자 패스워드 포함"
                :disabled="!form.mail_sending"
              />
            </CCol>
          </CRow>
        </CModalBody>
        <CModalFooter>
          <v-btn
            type="submit"
            size="small"
            color="primary"
            :disabled="isSubmitting"
            :loading="isSubmitting"
          >
            확인
          </v-btn>
          <v-btn type="button" color="light" size="small" :disabled="isSubmitting" flat @click="closeModal">
            닫기
          </v-btn>
        </CModalFooter>
      </CForm>
    </template>
  </FormModal>

  <AlertModal ref="refAlertModal" />
</template>
