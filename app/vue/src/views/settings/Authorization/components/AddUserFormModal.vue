<script setup lang="ts">
import { ref, reactive } from 'vue'
import { btnLight } from '@/utils/cssMixins.ts'
import FormModal from '@/components/Modals/FormModal.vue'

const emit = defineEmits(['on-submit'])

const refFormModal = ref()

const form = reactive({
  username: '',
  email: '',
  password: '',
  pass_conf: '',

  mail_sending: true,
  send_option: '1',
  expired: 24,
})

const genPass = ref()

const validated = ref()

const onSubmit = (event: Event) => {
  const el = event.currentTarget as HTMLInputElement
  if (!el.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()

    validated.value = true
  } else {
    if (form.password !== form.pass_conf) {
      alert('비밀번호가 일치하지 않습니다.')
      return
    }
    emit('on-submit', { ...form })
    validated.value = false
    formReset()
    refFormModal.value.close()
  }
}

const formReset = () => {
  form.username = ''
  form.email = ''
  form.password = ''
  form.pass_conf = ''
  form.mail_sending = true
  form.send_option = '1'
  form.expired = 24
}

const generatePassword = () => {
  const chars =
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+[]{}|;:,.<>?'
  let password = ''

  for (let i = 0; i < 8; i++) {
    const randomIndex = Math.floor(Math.random() * chars.length)
    password += chars[randomIndex]
  }

  genPass.value = password
}

const applyGen = () => {
  form.password = genPass.value
  form.pass_conf = genPass.value
  genPass.value = ''
}

const callModal = () => refFormModal.value.callModal()

defineExpose({ callModal })
</script>

<template>
  <FormModal ref="refFormModal">
    <template #icon>
      <v-icon icon="mdi-account-check" color="success" class="mr-2" />
    </template>
    <template #header>사용자 정보 입력</template>
    <template #default>
      <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
        <CModalBody class="text-body p-4">
          <CRow class="mb-3">
            <CFormLabel for="username" class="col-sm-3 col-form-label required">아이디</CFormLabel>
            <CCol sm="9">
              <CFormInput
                v-model="form.username"
                id="username"
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
                v-model="form.email"
                id="email"
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
                v-model="form.password"
                id="password"
                type="password"
                maxlength="20"
                placeholder="비밀번호"
                autocomplete="off"
                required
              />
            </CCol>
            <CCol sm="4">
              <v-btn color="info" size="small" class="mt-1" @click="generatePassword">
                임의 패스워드 생성
              </v-btn>
            </CCol>
          </CRow>
          <CRow class="mb-4" style="height: 45px">
            <CFormLabel for="pass_conf" class="col-sm-3 col-form-label required">
              비밀번호 확인
            </CFormLabel>
            <CCol sm="5">
              <CFormInput
                v-model="form.pass_conf"
                id="pass_conf"
                type="password"
                maxlength="20"
                placeholder="비밀번호 확인"
                required
              />
            </CCol>
            <CCol v-if="genPass" sm="4">
              <div class="p-1 mb-1 bg-yellow-lighten-1 text-center" style="width: 90px">
                {{ genPass }}
              </div>
              <v-btn :color="btnLight" size="small" @click="genPass = ''">취소</v-btn>
              <v-btn color="success" size="small" @click="applyGen">적용</v-btn>
            </CCol>
          </CRow>

          <v-divider class="mb-4" />

          <CRow>
            <CCol class="mb-3">
              <CFormCheck
                v-model="form.mail_sending"
                type="checkbox"
                id="inform-mail"
                label="새로 생성한 사용자에게 알림 메일 보내기"
              />
            </CCol>
          </CRow>

          <CRow>
            <CCol sm="12" class="pl-5 mb-3">
              <CFormCheck
                v-model="form.send_option"
                value="1"
                type="radio"
                name="content-option"
                id="content-option1"
                label="패스워드 재설정 링크 포함"
                :disabled="!form.mail_sending"
              />
            </CCol>
            <CRow>
              <CCol sm="5" class="pl-5 mb-3">
                <span class="pl-4">링크 만료 시간 : </span>
              </CCol>
              <CCol sm="4">
                <CFormSelect v-model.number="form.expired" size="sm" :disabled="!form.mail_sending">
                  <option v-for="i in 24" :value="i" :key="i">
                    <span v-if="i < 10">0</span>{{ i }}
                  </option>
                </CFormSelect>
              </CCol>
              <CCol>시간</CCol>
            </CRow>
            <CCol sm="12" class="pl-5 mb-3">
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
        </CModalBody>
        <CModalFooter>
          <v-btn :color="btnLight" size="small" @click="() => refFormModal.close()"> 닫기</v-btn>
          <v-btn type="submit" size="small" color="primary">확인</v-btn>
        </CModalFooter>
      </CForm>
    </template>
  </FormModal>
</template>
