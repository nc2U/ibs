<script lang="ts" setup>
import { ref, reactive, computed, onMounted, type PropType } from 'vue'
import { btnLight } from '@/utils/cssMixins.ts'
import { type Profile, type User } from '@/store/types/accounts'
import DatePicker from '@/components/DatePicker/index.vue'
import AvatarInput from './AvatarInput.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  userInfo: { type: Object as PropType<User | null>, default: null },
  profile: { type: Object, default: null },
})

const emit = defineEmits(['pass-change', 'on-submit', 'reset-form'])

const refAlertModal = ref()
const refConfirmModal = ref()

const form = reactive<Profile & { email: string }>({
  pk: null,
  user: null,
  email: '',
  name: '',
  birth_date: '',
  cell_phone: '',
  image: undefined,
})

const validated = ref(false)

const formsCheck = computed(() => {
  if (props.userInfo && props.profile) {
    const a = form.email === props.userInfo.email
    const b = form.name === props.profile.name
    const c = form.birth_date === props.profile.birth_date
    const d = form.cell_phone === props.profile.cell_phone
    const e = !form.image || form.image === props.profile.image
    return a && b && c && d && e
  } else return false
})

const confirmText = computed(() => (props.profile?.pk ? '변경' : '등록'))
const btnClass = computed(() => (props.profile?.pk ? 'success' : 'primary'))

const passChange = () => emit('pass-change')

const transProfileForm = (img: File) => (form.image = img)

const onSubmit = (event: Event) => {
  if (props.userInfo) {
    const e = event.currentTarget as HTMLSelectElement
    if (!e.checkValidity()) {
      event.preventDefault()
      event.stopPropagation()

      validated.value = true
    } else {
      refConfirmModal.value.callModal()
    }
  } else {
    refAlertModal.value.callModal()
  }
}

const modalAction = () => {
  emit('on-submit', form)
  validated.value = false
  refConfirmModal.value.close()
}

const formDataReset = () => {
  form.pk = null
  form.user = null
  form.email = ''
  form.name = ''
  form.birth_date = ''
  form.cell_phone = ''
  form.image = undefined
}

const formDataSetup = () => {
  if (props.userInfo && props.profile) {
    form.pk = props.profile.pk
    form.email = props.userInfo.email
    form.user = props.profile.user
    form.name = props.profile.name
    form.birth_date = props.profile.birth_date
    form.cell_phone = props.profile.cell_phone
  }
}

onMounted(() => formDataSetup())
</script>

<template>
  <CForm
    class="needs-validation"
    novalidate
    :validated="validated"
    enctype="multipart/form-data"
    @submit.prevent="onSubmit"
  >
    <CCardBody class="p-5">
      <CRow class="flex-md-row flex-column-reverse">
        <CCol md="4">
          <CRow class="mb-3">
            <h6>사용자 계정</h6>
            <CFormLabel class="col-sm-4 col-form-label"> 이름</CFormLabel>

            <CCol sm="8">{{ userInfo?.username ?? '' }}</CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel class="col-sm-4 col-form-label"> 이메일 주소</CFormLabel>

            <CCol sm="8">
              <CFormInput
                v-model="form.email"
                type="email"
                placeholder="이메일을 입력하세요"
                maxlength="50"
                id="email"
                required
              />
              <CFormFeedback invalid>이메일을 입력하세요.</CFormFeedback>
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel class="col-sm-4 col-form-label"> 패스워드</CFormLabel>

            <CCol sm="8">
              <v-btn type="button" @click="passChange" :color="btnLight">패스워드 변경</v-btn>
            </CCol>
          </CRow>

          <v-divider class="my-4" />

          <CRow class="mb-3">
            <h6>사용자 프로필</h6>
            <CFormLabel for="name" class="col-sm-4 col-form-label"> 닉네임</CFormLabel>

            <CCol sm="8">
              <CFormInput
                v-model="form.name"
                type="text"
                placeholder="성명을 입력하세요"
                maxlength="20"
                id="name"
                required
              />
              <CFormFeedback invalid>성명을 입력하세요.</CFormFeedback>
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel for="birth_date" class="col-sm-4 col-form-label"> 생년월일</CFormLabel>

            <CCol sm="8">
              <DatePicker
                v-model="form.birth_date"
                placeholder="생년월일을 입력하세요"
                maxlength="10"
                id="birth_date"
              />
              <CFormFeedback invalid>생년월일을 입력하세요.</CFormFeedback>
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="cell_phone" class="col-sm-4 col-form-label"> 휴대전화</CFormLabel>

            <CCol sm="8">
              <input
                v-model="form.cell_phone"
                v-maska
                data-maska="['###-###-####', '###-####-####']"
                type="text"
                class="form-control"
                placeholder="휴대전화를 입력하세요"
                maxlength="13"
                id="cell_phone"
              />
              <CFormFeedback invalid>휴대전화를 입력하세요.</CFormFeedback>
            </CCol>
          </CRow>
        </CCol>
        <CCol md="8">
          <AvatarInput
            ref="avatar"
            :image="(profile && profile.image) || '/static/dist/img/NoImage.jpeg'"
            @trans-profile-form="transProfileForm"
          />
        </CCol>
      </CRow>
    </CCardBody>

    <CCardFooter class="text-right">
      <v-btn type="button" color="light" @click="formDataReset"> 취소</v-btn>
      <v-btn type="submit" :color="btnClass" :disabled="formsCheck">
        <CIcon name="cil-check-circle" />
        {{ confirmText }}
      </v-btn>
    </CCardFooter>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header>프로필 정보</template>
    <template #default> 프로필 정보 {{ confirmText }}을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn :color="btnClass" @click="modalAction">
        {{ confirmText }}
      </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
