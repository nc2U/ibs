<script lang="ts" setup>
import { computed, onBeforeMount, reactive, ref, watch } from 'vue'
import { onBeforeRouteUpdate, useRouter } from 'vue-router'
import { isValidate } from '@/utils/helper'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import MyMenuLinks from '@/views/_Work/Settings/Users/components/atomicViews/MyMenuLinks.vue'
import AvatarInput from '@/views/_Work/Settings/Users/components/atomicViews/AvatarInput.vue'
import SignInput from '@/views/_Work/Settings/Users/components/atomicViews/SignInput.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const refAlertModal = ref<InstanceType<typeof AlertModal>>()
const refConfirmModal = ref<InstanceType<typeof ConfirmModal>>()

const router = useRouter()

const form = reactive({
  pk: null as number | null,
  user: null as number | null,
  email: '',

  // Profile fields
  name: '',
  birth_date: '',
  cell_phone: '',
  image: undefined as File | undefined,
  sign_image: undefined as File | undefined,
  sign_type: 'STAMP' as 'STAMP' | 'SIGN',

  // notification fields
  auto_watch_created: true,
  auto_watch_assigned: true,
  meeting_created_notification: true,
  meeting_confirmed_notification: true,

  subscribed_projects: [] as number[],
})

const validated = ref(false)
const isSaving = ref(false)

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)
const profile = computed(() => accStore.profile)

const createProfile = (payload: FormData) => accStore.createProfile(payload)
const patchProfile = (payload: { pk: number; form: FormData }) => accStore.patchProfile(payload)

const workStore = useWork()
const allActiveProjects = computed(() => workStore.getAllActiveProjects)
const subscribedProjects = computed(() => workStore.subscribedProjects)

const transProfileForm = (img?: File) => (form.image = img)

const formDataSetup = async () => {
  form.image = undefined
  form.sign_image = undefined
  if (userInfo.value) {
    form.user = userInfo.value.pk || null
    form.email = userInfo.value.email || ''

    if (profile.value) {
      form.pk = profile.value?.pk || null
      form.name = profile.value.name || ''
      form.birth_date = profile.value.birth_date || ''
      form.cell_phone = profile.value.cell_phone || ''
      form.sign_type = (profile.value.sign_type as 'STAMP' | 'SIGN') ?? 'STAMP'
      form.auto_watch_created = profile.value.auto_watch_created ?? true
      form.auto_watch_assigned = profile.value.auto_watch_assigned ?? true
      form.meeting_created_notification = profile.value.meeting_created_notification ?? true
      form.meeting_confirmed_notification = profile.value.meeting_confirmed_notification ?? true
    } else {
      form.name = ''
      form.birth_date = ''
      form.cell_phone = ''
      form.sign_type = 'STAMP'
      form.auto_watch_created = true
      form.auto_watch_assigned = true
      form.meeting_created_notification = true
      form.meeting_confirmed_notification = true
    }

    if (userInfo.value.pk) {
      await workStore.fetchSubscribedProjects(userInfo.value.pk)
      form.subscribed_projects = (subscribedProjects.value ?? []).map((item: any) => item.project)
    } else {
      form.subscribed_projects = []
    }
  } else {
    form.pk = null
    form.user = null
    form.email = ''

    form.name = ''
    form.birth_date = ''
    form.cell_phone = ''
    form.auto_watch_created = true
    form.auto_watch_assigned = true
    form.meeting_created_notification = true
    form.meeting_confirmed_notification = true

    form.subscribed_projects = []
  }
}

watch([userInfo, profile], () => {
  if (!isSaving.value) formDataSetup()
})

const onSubmit = async (event: Event) => {
  if (userInfo.value) {
    if (isValidate(event)) {
      validated.value = true
      return
    } else refConfirmModal.value?.callModal()
  } else refAlertModal.value?.callModal()
}

const onSubmitConfirm = async () => {
  isSaving.value = true
  try {
    const { pk, image, sign_image, subscribed_projects, ...profileFields } = form
    const targetSubscribed = [...subscribed_projects]
    if (!profileFields.birth_date) profileFields.birth_date = ''

    const submitData = new FormData()

    Object.entries(profileFields).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        submitData.append(key, value as any)
      }
    })

    if (image instanceof File) submitData.append('image', image)
    if (sign_image instanceof File) submitData.append('sign_image', sign_image)

    // 1. 프로필 업데이트 (이미지 포함)
    const profileSaved = pk
      ? await patchProfile({ pk, form: submitData })
      : await createProfile(submitData)

    if (!profileSaved) return

    // 2. 워크스페이스 구독 업데이트 (프로필 저장 성공 후 캡처한 스냅샷으로 저장)
    if (userInfo.value?.pk) {
      const subSaved = await workStore.createSubscribedProjects({
        user: userInfo.value.pk,
        project_ids: targetSubscribed,
      })
      if (!subSaved) return
      form.subscribed_projects = [...targetSubscribed]
    }

    validated.value = false
    refConfirmModal.value?.close()
  } catch (err: any) {
    console.error('Error during onSubmitConfirm:', err)
    refAlertModal.value?.callModal('', '사용자 정보 저장 중 오류가 발생했습니다.')
  } finally {
    isSaving.value = false
  }
}

onBeforeMount(async () => {
  await formDataSetup()
})

onBeforeRouteUpdate(async () => {
  await formDataSetup()
})
</script>

<template>
  <div>
    <CRow class="py-2 align-items-center">
      <CCol class="mb-2">
        <span class="h5 me-2"> 내 계정 </span>
      </CCol>

      <MyMenuLinks current="account" />
    </CRow>

    <CRow>
      <CForm
        class="row needs-validation"
        novalidate
        :validated="validated"
        @submit.prevent="onSubmit"
      >
        <CCol class="col-lg-6">
          <!-- Account Info Card -->
          <CCard class="mb-4">
            <CCardHeader class="fw-bold">
              <v-icon icon="mdi-account-cog" class="me-1" color="primary" />
              계정 정보
            </CCardHeader>
            <CCardBody>
              <!-- Username -->
              <CRow class="mb-3">
                <CFormLabel for="username" class="col-sm-3 col-form-label">아이디</CFormLabel>
                <CCol sm="9">
                  <span>{{ userInfo?.username }}</span>
                </CCol>
              </CRow>

              <!-- Email -->
              <CRow class="mb-3">
                <CFormLabel for="email" class="col-sm-3 col-form-label required">
                  이메일
                </CFormLabel>
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

              <!-- Password -->
              <CRow class="mb-3">
                <CFormLabel for="password" class="col-sm-3 col-form-label">비밀번호</CFormLabel>
                <CCol sm="5">
                  <v-btn color="light" @click="router.push({ name: '사용자 - 비밀번호 변경' })">
                    비밀번호 변경
                  </v-btn>
                </CCol>
              </CRow>
            </CCardBody>
          </CCard>

          <!-- Profile Image Card -->
          <CCard class="mb-4">
            <CCardHeader class="fw-bold">
              <v-icon icon="mdi-account-circle" class="me-1" color="primary" />
              프로필 이미지
            </CCardHeader>
            <CCardBody>
              <CRow class="pt-3 pb-4">
                <CFormLabel for="avatar" class="col-sm-3 col-form-label"></CFormLabel>
                <CCol sm="9">
                  <AvatarInput
                    ref="avatar"
                    :image="(profile && profile.image) || '/static/dist/img/NoImage.jpeg'"
                    :filename="userInfo?.username || 'profile'"
                    id="avatar"
                    @trans-profile-form="transProfileForm"
                  />
                </CCol>
              </CRow>
            </CCardBody>
          </CCard>

          <!-- Seal / Sign Image Card -->
          <CCard class="mb-4">
            <CCardHeader class="fw-bold">
              <v-icon icon="mdi-draw-pen" class="me-1" color="primary" />
              전자결재 인장 / 서명
            </CCardHeader>
            <CCardBody>
              <CRow class="pt-2 pb-3">
                <CCol>
                  <SignInput
                    :image="profile && profile.sign_image"
                    :sign-type="form.sign_type"
                    @update:image="file => (form.sign_image = file)"
                    @update:sign-type="type => (form.sign_type = type)"
                  />
                </CCol>
              </CRow>
            </CCardBody>
          </CCard>
        </CCol>

        <CCol class="col-lg-6">
          <!-- Profile Info Card -->
          <CCard class="mb-4">
            <CCardHeader class="fw-bold">
              <v-icon icon="mdi-account-check" class="me-1" color="primary" />
              내 프로필
            </CCardHeader>
            <CCardBody>
              <CRow class="mb-3">
                <CFormLabel for="profile-name" class="col-sm-3 col-form-label required">
                  이름
                </CFormLabel>
                <CCol sm="9">
                  <CFormInput
                    v-model="form.name"
                    type="text"
                    placeholder="성명을 입력하세요"
                    maxlength="20"
                    id="profile-name"
                    required
                  />
                  <CFormFeedback invalid>성명을 입력하세요.</CFormFeedback>
                </CCol>
              </CRow>

              <CRow class="mb-3">
                <CFormLabel for="birth_date" class="col-sm-3 col-form-label"> 생년월일 </CFormLabel>
                <CCol sm="9">
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
                <CFormLabel for="cell_phone" class="col-sm-3 col-form-label"> 휴대전화</CFormLabel>
                <CCol>
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
            </CCardBody>
          </CCard>

          <!-- Mail Notifications Card -->
          <CCard class="mb-4">
            <CCardHeader class="fw-bold">
              <v-icon icon="mdi-cog" class="me-1" color="primary" />
              업무 및 알림 설정
            </CCardHeader>
            <CCardBody>
              <!-- 메일 알림 설정 -->
              <CRow class="mb-3">
                <CFormLabel class="col-sm-3 col-form-label">회의 알림 설정</CFormLabel>
                <CCol sm="9" class="pt-2">
                  <CRow>
                    <CCol xs="12" class="mb-2">
                      <CFormCheck
                        v-model="form.meeting_created_notification"
                        id="meeting_created_notification"
                        label="회의록 등록 시 알림 메일 수신"
                      />
                    </CCol>
                    <CCol xs="12" class="mb-2">
                      <CFormCheck
                        v-model="form.meeting_confirmed_notification"
                        id="meeting_confirmed_notification"
                        label="회의록 확정 시 알림 메일 수신"
                      />
                    </CCol>
                  </CRow>
                </CCol>
              </CRow>

              <!-- 자동 알림 설정 -->
              <v-divider class="my-4" />
              <CRow class="mb-3">
                <CFormLabel class="col-sm-3 col-form-label">업무 알림 설정</CFormLabel>
                <CCol sm="9" class="pt-2">
                  <CRow>
                    <CCol xs="12" class="mb-4" style="width: 420px">
                      <v-autocomplete
                        v-model="form.subscribed_projects"
                        :items="allActiveProjects"
                        item-title="label"
                        item-value="value"
                        label="알림 구독 워크스페이스"
                        multiple
                        chips
                        closable-chips
                        density="compact"
                        hint="선택한 워크스페이스의 모든 업무 생성 및 변경 알림 메일을 수신합니다."
                        persistent-hint
                      />
                    </CCol>
                    <CCol xs="12" class="mb-2">
                      <CFormCheck
                        v-model="form.auto_watch_created"
                        id="auto_watch_created"
                        label="내가 생성한 업무 자동 지켜보기 (모니터링)"
                      />
                    </CCol>
                    <CCol xs="12" class="mb-2">
                      <CFormCheck
                        v-model="form.auto_watch_assigned"
                        id="auto_watch_assigned"
                        label="나에게 할당된 업무 자동 지켜보기 (모니터링)"
                      />
                    </CCol>
                  </CRow>
                </CCol>
              </CRow>
            </CCardBody>
          </CCard>

          <!-- Submit & Cancel Footer -->
          <div class="text-end mb-4">
            <v-btn type="submit" color="primary"> 저장</v-btn>
            <v-btn color="light" class="ms-2" @click="router.push({ name: '사용자' })" flat>
              취소
            </v-btn>
          </div>
        </CCol>
      </CForm>
    </CRow>
  </div>

  <ConfirmModal ref="refConfirmModal" item-name="내 프로필" @confirm-func="onSubmitConfirm" />
  <AlertModal ref="refAlertModal"></AlertModal>
</template>
