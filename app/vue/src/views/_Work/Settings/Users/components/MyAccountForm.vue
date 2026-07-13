<script lang="ts" setup>
import { computed, onBeforeMount, reactive, ref, watch } from 'vue'
import { onBeforeRouteUpdate, useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import AvatarInput from '@/views/_MyPage/Modify/components/AvatarInput.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const refAlertModal = ref<InstanceType<typeof AlertModal>>()
const refConfirmModal = ref<InstanceType<typeof AlertModal>>()

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

  // notification fields
  auto_watch_created: true,
  auto_watch_assigned: true,
  meeting_created_notification: true,
  meeting_confirmed_notification: true,

  subscribed_projects: [] as number[],
})

const validated = ref(false)

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)
const profile = computed(() => accStore.profile)

const createProfile = (payload: FormData) => accStore.createProfile(payload)
const patchProfile = (payload: { pk: number; form: FormData }) => accStore.patchProfile(payload)

const workStore = useWork()
const projectList = computed(() => workStore.getIssueProjPks)
const subscribedProjects = computed(() => workStore.subscribedProjects)

const transProfileForm = (img?: File) => (form.image = img)

const formDataSetup = async () => {
  form.image = undefined
  if (userInfo.value) {
    form.user = userInfo.value.pk || null
    form.email = userInfo.value.email || ''

    if (profile.value) {
      form.pk = profile.value?.pk || null
      form.name = profile.value.name || ''
      form.birth_date = profile.value.birth_date || ''
      form.cell_phone = profile.value.cell_phone || ''
      form.auto_watch_created = profile.value.auto_watch_created ?? true
      form.auto_watch_assigned = profile.value.auto_watch_assigned ?? true
      form.meeting_created_notification = profile.value.meeting_created_notification ?? true
      form.meeting_confirmed_notification = profile.value.meeting_confirmed_notification ?? true
    } else {
      form.name = ''
      form.birth_date = ''
      form.cell_phone = ''
      form.auto_watch_created = true
      form.auto_watch_assigned = true
      form.meeting_created_notification = true
      form.meeting_confirmed_notification = true
    }

    await workStore.fetchSubscribedProjects(profile.value?.user as number)
    form.subscribed_projects = subscribedProjects.value.map((item: any) => item.project) || []

    // try {
    //   const res = await api.get(`/project-subscription/?user=${userInfo.value.pk}`)
    //   form.subscribed_projects = res.data.map((item: any) => item.project)
    // } catch (err) {
    //   form.subscribed_projects = []
    // }
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

watch([userInfo, profile], () => formDataSetup())

const onSubmit = async (event: Event) => {
  if (userInfo.value) {
    const el = event.currentTarget as HTMLFormElement
    if (!el.checkValidity()) {
      event.preventDefault()
      event.stopPropagation()
      validated.value = true
      return
    } else refConfirmModal.value?.callModal()
  } else refAlertModal.value?.callModal()
}

const onSubmitConfirm = async () => {
  try {
    const { pk, image, subscribed_projects, ...profileFields } = form
    if (!profileFields.birth_date) profileFields.birth_date = ''

    const submitData = new FormData()

    Object.entries(profileFields).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        submitData.append(key, value as any)
      }
    })

    if (image instanceof File) submitData.append('image', image)

    // 1. 프로필 업데이트 (이미지 포함)
    if (pk) await patchProfile({ pk, form: submitData })
    else await createProfile(submitData)

    // 2. 프로젝트 구독 업데이트 (await 추가 및 프로필 업데이트 성공 후 실행 보장)
    if (userInfo.value?.pk) {
      await workStore.createSubscribedProjects({
        user: userInfo.value.pk,
        project_ids: form.subscribed_projects,
      })
    }

    validated.value = false
    refConfirmModal.value?.close()
  } catch (err: any) {
    console.error('Error during onSubmitConfirm:', err)
    refAlertModal.value?.callModal('', '사용자 정보 저장 중 오류가 발생했습니다.')
  }
}

onBeforeMount(async () => {
  await workStore.fetchIssueProjectList({})
  await formDataSetup()
})

onBeforeRouteUpdate(async to => {
  await formDataSetup()
})
</script>

<template>
  <div>
    <CRow class="py-2">
      <CCol class="mb-2">
        <span class="h5 mr-2"> 내 계정 </span>
      </CCol>

      <CCol class="text-right form-text">
        <span class="mr-2">
          <TextButton
            name="비밀번호 변경"
            :to="{ name: '사용자 - 비밀번호 변경' }"
            icon="mdi-key-outline"
            icon-color="amber"
          />
        </span>
      </CCol>
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
            <CCardHeader class="font-weight-bold">
              <v-icon icon="mdi-account-cog" class="mr-1" color="primary" />
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
            <CCardHeader class="font-weight-bold">
              <v-icon icon="mdi-account-circle" class="mr-1" color="primary" />
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
        </CCol>

        <CCol class="col-lg-6">
          <!-- Profile Info Card -->
          <CCard class="mb-4">
            <CCardHeader class="font-weight-bold">
              <v-icon icon="mdi-account-check" class="mr-1" color="primary" />
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
                <CFormLabel for="email" class="col-sm-3 col-form-label required">
                  생년월일
                </CFormLabel>
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
                <CFormLabel for="password" class="col-sm-3 col-form-label"> 휴대전화 </CFormLabel>
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
            <CCardHeader class="font-weight-bold">
              <v-icon icon="mdi-cog" class="mr-1" color="primary" />
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

              <!-- 자동 관람 설정 -->
              <v-divider class="my-4" />
              <CRow class="mb-3">
                <CFormLabel class="col-sm-3 col-form-label">업무 관람 설정</CFormLabel>
                <CCol sm="9" class="pt-2">
                  <CRow>
                    <CCol xs="12" class="mb-4" style="width: 420px">
                      <v-autocomplete
                        v-model="form.subscribed_projects"
                        :items="projectList"
                        item-title="label"
                        item-value="value"
                        label="알림 구독 프로젝트"
                        multiple
                        chips
                        closable-chips
                        density="compact"
                        hint="선택한 프로젝트의 모든 업무 생성 및 변경 알림 메일을 수신합니다."
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
          <div class="text-right mb-4">
            <v-btn type="submit" color="primary"> 저장</v-btn>
            <v-btn color="light" class="mr-2" @click="router.push({ name: '사용자' })" flat>
              취소
            </v-btn>
          </div>
        </CCol>
      </CForm>
    </CRow>
  </div>

  <ConfirmModal ref="refConfirmModal">
    <template #default> 내 계정 정보를 저장하시겠습니까? </template>
    <template #footer>
      <v-btn color="success" size="small" @click="onSubmitConfirm">저장</v-btn>
    </template>
  </ConfirmModal>
  <AlertModal ref="refAlertModal"></AlertModal>
</template>
