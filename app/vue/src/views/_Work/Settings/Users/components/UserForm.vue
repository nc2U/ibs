<script lang="ts" setup>
import { computed, onBeforeMount, ref, reactive, watch } from 'vue'
import { onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { btnLight } from '@/utils/cssMixins.ts'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import api from '@/api'

const menu = ref<'일반' | '프로젝트'>('일반')

const accStore = useAccount()
const user = computed(() => accStore.user)

const [route, router] = [useRoute(), useRouter()]

const form = reactive({
  username: '',
  email: '',
  password: '',
  pass_conf: '',
  is_active: true,
  is_staff: false,
  is_superuser: false,
  work_manager: false,
  // Profile fields
  name: '',
  birth_date: '',
  cell_phone: '',
  // Notification fields (creation only)
  mail_sending: true,
  send_option: '1',
  expired: 24,
})

const genPass = ref('')
const validated = ref(false)

const formDataSetup = () => {
  if (user.value) {
    form.username = user.value.username || ''
    form.email = user.value.email || ''
    form.password = ''
    form.pass_conf = ''
    form.is_active = user.value.is_active
    form.is_staff = user.value.is_staff
    form.is_superuser = user.value.is_superuser
    form.work_manager = user.value.work_manager

    if (user.value.profile) {
      form.name = user.value.profile.name || ''
      form.birth_date = user.value.profile.birth_date || ''
      form.cell_phone = user.value.profile.cell_phone || ''
    } else {
      form.name = ''
      form.birth_date = ''
      form.cell_phone = ''
    }
  } else {
    form.username = ''
    form.email = ''
    form.password = ''
    form.pass_conf = ''
    form.is_active = true
    form.is_staff = false
    form.is_superuser = false
    form.work_manager = false
    form.name = ''
    form.birth_date = ''
    form.cell_phone = ''
    form.mail_sending = true
    form.send_option = '1'
    form.expired = 24
  }
}

onBeforeMount(async () => {
  if (route.params.userId) {
    await accStore.fetchUser(Number(route.params.userId))
  } else {
    accStore.user = null
  }
  formDataSetup()
})

onBeforeRouteUpdate(async to => {
  if (to.params.userId) {
    await accStore.fetchUser(Number(to.params.userId))
  } else {
    accStore.user = null
  }
  formDataSetup()
})

watch(user, () => formDataSetup())

const generatePassword = () => {
  const chars =
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+[]{}|;:,.<>?'
  let password = ''

  for (let i = 0; i < 8; i++) {
    const array = new Uint32Array(1)
    window.crypto.getRandomValues(array)
    const randomIndex = array[0] % chars.length
    password += chars[randomIndex]
  }

  genPass.value = password
}

const applyGen = () => {
  form.password = genPass.value
  form.pass_conf = genPass.value
  genPass.value = ''
}

const onSubmit = async (event: Event) => {
  const el = event.currentTarget as HTMLFormElement
  if (!el.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()
    validated.value = true
    return
  }

  if (form.password && form.password !== form.pass_conf) {
    alert('비밀번호가 일치하지 않습니다.')
    return
  }

  try {
    if (!user.value) {
      // Create user
      const payload = {
        username: form.username,
        email: form.email,
        password: form.password,
        mail_sending: form.mail_sending,
        send_option: form.send_option as '1' | '2',
        expired: form.expired,
      }
      await accStore.adminCreateUser(payload)
    } else {
      // Edit User account info
      const userPayload: any = {
        email: form.email,
        is_active: form.is_active,
        is_staff: form.is_staff,
        is_superuser: form.is_superuser,
        work_manager: form.work_manager,
      }
      if (form.password) {
        userPayload.password = form.password
      }
      await api.patch(`/user/${user.value.pk}/`, userPayload)

      // Edit User Profile info
      const profilePayload = {
        name: form.name,
        birth_date: form.birth_date,
        cell_phone: form.cell_phone,
      }
      if (user.value.profile) {
        await api.patch(`/profile/${user.value.profile.pk}/`, profilePayload)
      } else {
        await api.post(`/profile/`, { ...profilePayload, user: user.value.pk })
      }
    }

    validated.value = false
    router.push({ name: '사용자' })
  } catch (err: any) {
    console.error(err)
    alert('사용자 정보 저장 중 오류가 발생했습니다.')
  }
}
</script>

<template>
  <CRow>
    <CCol sm="6">
      <CRow class="py-2">
        <CCol class="mb-2">
          <span class="h5 mr-2">
            <router-link :to="{ name: '사용자' }">사용자</router-link>
          </span>
          <span class="mr-2">»</span>
          <span class="h5">{{ user ? user.username : '새 사용자' }}</span>
        </CCol>

        <CCol v-if="user" class="text-right form-text">
          <span class="mr-2">
            <v-icon icon="mdi-account" color="success" size="sm" />
            <router-link :to="{ name: '사용자 - 보기', params: { userId: user.pk } }" class="ml-1">
              사용자 정보
            </router-link>
          </span>
        </CCol>
      </CRow>

      <!-- Edit Mode Tabs -->
      <CRow v-if="user" class="mb-3">
        <CCol>
          <v-tabs v-model="menu" density="compact">
            <v-tab value="일반" variant="tonal"> 일반</v-tab>
            <v-tab value="프로젝트" variant="tonal"> 프로젝트</v-tab>
          </v-tabs>
        </CCol>
      </CRow>

      <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
        <CRow v-if="menu === '일반'">
          <CCol lg="12">
            <!-- Account Info Card -->
            <CCard class="mb-4">
              <CCardHeader class="font-weight-bold">
                <v-icon icon="mdi-account-cog" class="mr-1" color="primary" />
                계정 정보
              </CCardHeader>
              <CCardBody>
                <!-- Username -->
                <CRow class="mb-3">
                  <CFormLabel for="username" class="col-sm-3 col-form-label required"
                    >아이디
                  </CFormLabel>
                  <CCol sm="9">
                    <CFormInput
                      v-model="form.username"
                      id="username"
                      maxlength="30"
                      placeholder="아이디"
                      autocomplete="off"
                      :disabled="!!user"
                      required
                    />
                  </CCol>
                </CRow>

                <!-- Email -->
                <CRow class="mb-3">
                  <CFormLabel for="email" class="col-sm-3 col-form-label required"
                    >이메일</CFormLabel
                  >
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
                  <CFormLabel
                    for="password"
                    class="col-sm-3 col-form-label"
                    :class="{ required: !user }"
                  >
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
                      :required="!user"
                    />
                  </CCol>
                  <CCol sm="4">
                    <v-btn color="info" size="small" class="mt-1" @click="generatePassword">
                      임의 패스워드 생성
                    </v-btn>
                  </CCol>
                </CRow>

                <!-- Password Confirm -->
                <CRow class="mb-3" style="height: 45px">
                  <CFormLabel
                    for="pass_conf"
                    class="col-sm-3 col-form-label"
                    :class="{ required: !user }"
                  >
                    비밀번호 확인
                  </CFormLabel>
                  <CCol sm="5">
                    <CFormInput
                      v-model="form.pass_conf"
                      id="pass_conf"
                      type="password"
                      maxlength="20"
                      placeholder="비밀번호 확인"
                      :required="!user"
                    />
                  </CCol>
                  <CCol v-if="genPass" sm="4">
                    <div
                      class="p-1 mb-1 bg-yellow-lighten-1 text-center font-weight-bold"
                      style="width: 120px; display: inline-block; vertical-align: middle"
                    >
                      {{ genPass }}
                    </div>
                    <div style="display: inline-block; vertical-align: middle" class="ml-2">
                      <v-btn :color="btnLight" size="small" class="mr-1" @click="genPass = ''"
                        >취소
                      </v-btn>
                      <v-btn color="success" size="small" @click="applyGen">적용</v-btn>
                    </div>
                  </CCol>
                </CRow>

                <!-- Permissions / Flags (Only visible when editing an existing user) -->
                <template v-if="user">
                  <v-divider class="my-4" />
                  <CRow class="mb-3">
                    <CFormLabel class="col-sm-3 col-form-label">권한 및 상태</CFormLabel>
                    <CCol sm="9" class="pt-2">
                      <CRow>
                        <CCol xs="6" sm="4" class="mb-2">
                          <CFormCheck v-model="form.is_active" id="is_active" label="활성 사용자" />
                        </CCol>
                        <CCol xs="6" sm="4" class="mb-2">
                          <CFormCheck v-model="form.is_staff" id="is_staff" label="Staff 권한" />
                        </CCol>
                        <CCol xs="6" sm="4" class="mb-2">
                          <CFormCheck
                            v-model="form.is_superuser"
                            id="is_superuser"
                            label="Superuser 권한"
                          />
                        </CCol>
                        <CCol xs="6" sm="4" class="mb-2">
                          <CFormCheck
                            v-model="form.work_manager"
                            id="work_manager"
                            label="업무관리자 권한"
                          />
                        </CCol>
                      </CRow>
                    </CCol>
                  </CRow>
                </template>
              </CCardBody>
            </CCard>

            <!-- Profile Info Card (Only relevant/loaded when editing, or optional during creation) -->
            <!--            <CCard class="mb-4">-->
            <!--              <CCardHeader class="font-weight-bold">-->
            <!--                <v-icon icon="mdi-card-account-details" class="mr-1" color="success" />-->
            <!--                프로필 정보-->
            <!--              </CCardHeader>-->
            <!--              <CCardBody>-->
            <!--                &lt;!&ndash; Real Name &ndash;&gt;-->
            <!--                <CRow class="mb-3">-->
            <!--                  <CFormLabel for="name" class="col-sm-3 col-form-label">이름</CFormLabel>-->
            <!--                  <CCol sm="9">-->
            <!--                    <CFormInput-->
            <!--                      v-model="form.name"-->
            <!--                      id="name"-->
            <!--                      maxlength="50"-->
            <!--                      placeholder="사용자 이름"-->
            <!--                    />-->
            <!--                  </CCol>-->
            <!--                </CRow>-->

            <!--                &lt;!&ndash; Birth Date &ndash;&gt;-->
            <!--                <CRow class="mb-3">-->
            <!--                  <CFormLabel for="birth_date" class="col-sm-3 col-form-label">생년월일</CFormLabel>-->
            <!--                  <CCol sm="9">-->
            <!--                    <DatePicker-->
            <!--                      v-model="form.birth_date"-->
            <!--                      placeholder="생년월일 선택 (YYYY-MM-DD)"-->
            <!--                    />-->
            <!--                  </CCol>-->
            <!--                </CRow>-->

            <!--                &lt;!&ndash; Cell Phone &ndash;&gt;-->
            <!--                <CRow class="mb-3">-->
            <!--                  <CFormLabel for="cell_phone" class="col-sm-3 col-form-label"-->
            <!--                    >휴대폰 번호</CFormLabel-->
            <!--                  >-->
            <!--                  <CCol sm="9">-->
            <!--                    <CFormInput-->
            <!--                      v-model="form.cell_phone"-->
            <!--                      id="cell_phone"-->
            <!--                      maxlength="20"-->
            <!--                      placeholder="휴대폰 번호 (예: 010-1234-5678)"-->
            <!--                    />-->
            <!--                  </CCol>-->
            <!--                </CRow>-->
            <!--              </CCardBody>-->
            <!--            </CCard>-->

            <!-- Mail Notifications Card (Only when creating a new user) -->
            <CCard v-if="!user" class="mb-4">
              <CCardHeader class="font-weight-bold">
                <v-icon icon="mdi-email-send" class="mr-1" color="warning" />
                알림 메일 발송 설정
              </CCardHeader>
              <CCardBody>
                <CRow class="mb-2">
                  <CCol>
                    <CFormCheck
                      v-model="form.mail_sending"
                      type="checkbox"
                      id="inform-mail"
                      label="새로 생성한 사용자에게 알림 메일 보내기"
                    />
                  </CCol>
                </CRow>

                <CRow class="pl-4">
                  <CCol sm="12" class="mb-3">
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

                  <CRow class="mb-3">
                    <CCol sm="4" class="pl-5 pt-1">
                      <span>링크 만료 시간 : </span>
                    </CCol>
                    <CCol sm="4">
                      <CFormSelect
                        v-model.number="form.expired"
                        size="sm"
                        :disabled="!form.mail_sending"
                      >
                        <option v-for="i in 24" :value="i" :key="i">
                          <span v-if="i < 10">0</span>{{ i }}
                        </option>
                      </CFormSelect>
                    </CCol>
                    <CCol sm="4" class="pt-1">시간</CCol>
                  </CRow>

                  <CCol sm="12" class="mb-3">
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
        </CRow>
      </CForm>

      <!-- Project Tab (Placeholder or configuration) -->
      <CRow v-if="menu === '프로젝트' && user">
        <CCol lg="8" class="mx-auto">
          <CCard>
            <CCardHeader class="font-weight-bold">
              <v-icon icon="mdi-shield-account" class="mr-1" color="orange" />
              프로젝트 권한 설정
            </CCardHeader>
            <CCardBody class="text-center py-5">
              <span class="text-grey-darken-1">
                프로젝트 권한 관리 및 소속 제어는 상단 관리자 설정 메뉴를 통해 관리할 수 있습니다.
              </span>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>
    </CCol>

    <CCol sm="6"></CCol>
  </CRow>
</template>
