<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue'
import { pageTitle, navMenu } from '@/views/notices/_menu/headermixin'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'

const loading = ref(true)
const activeTab = ref('sms')

// 폼 데이터
const smsForm = ref({
  messageType: 'SMS',
  recipients: '',
  message: '',
  senderNumber: '',
  scheduledSend: false,
  scheduleDate: '',
  scheduleTime: '',
})

const kakaoForm = ref({
  templateId: '',
  recipients: '',
  message: '',
  parameters: {},
  scheduledSend: false,
  scheduleDate: '',
  scheduleTime: '',
})

// UI 상태
const recipientsList = ref([])
const messageCount = ref(0)
const sendProgress = ref(0)
const isSending = ref(false)

onBeforeMount(() => {
  loading.value = false
})

// 메소드 (비즈니스 로직은 제외하고 UI만)
const addRecipient = () => {
  // UI만 구현
}

const removeRecipient = (index: number) => {
  // UI만 구현
}

const selectTemplate = () => {
  // UI만 구현
}

const previewMessage = () => {
  // UI만 구현
}

const sendMessage = () => {
  // UI만 구현
  isSending.value = true
  sendProgress.value = 0
}
</script>

<template>
  <Loading v-model:active="loading" />

  <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

  <ContentBody>
    <!-- 메인 탭 구조 -->
    <CCard class="mb-4">
      <CCardBody>
        <v-tabs v-model="activeTab" bg-color="primary" align-tabs="center">
          <v-tab value="sms" prepend-icon="mdi-message-text">
            <span class="text-h6">SMS 전송</span>
          </v-tab>
          <v-tab value="kakao" prepend-icon="mdi-chat">
            <span class="text-h6">카카오 알림톡</span>
          </v-tab>
        </v-tabs>
      </CCardBody>
    </CCard>

    <!-- 탭 컨텐츠 -->
    <v-tabs-window v-model="activeTab">
      <!-- SMS 전송 탭 -->
      <v-tabs-window-item value="sms">
        <CRow>
          <!-- 수신자 관리 섹션 -->
          <CCol :md="6" :xs="12">
            <CCard class="mb-4">
              <CCardHeader>
                <v-icon icon="mdi-account-multiple" class="me-2" />
                <strong>수신자 관리</strong>
              </CCardHeader>
              <CCardBody>
                <!-- 수신자 입력 방법 선택 -->
                <v-expansion-panels class="mb-3">
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      <v-icon icon="mdi-account-plus" class="me-2" />
                      개별 번호 입력
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <CRow class="align-items-end">
                        <CCol :md="8">
                          <CFormInput
                            v-model="smsForm.recipients"
                            placeholder="010-1234-5678"
                            label="휴대폰 번호"
                          />
                        </CCol>
                        <CCol :md="4">
                          <v-btn
                            color="primary"
                            @click="addRecipient"
                            prepend-icon="mdi-plus"
                            block
                          >
                            추가
                          </v-btn>
                        </CCol>
                      </CRow>
                    </v-expansion-panel-text>
                  </v-expansion-panel>

                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      <v-icon icon="mdi-account-group" class="me-2" />
                      그룹 선택
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <CFormSelect
                        label="수신자 그룹"
                        :options="[
                          { value: 'all', label: '전체 계약자' },
                          { value: 'contractors', label: '계약 완료자' },
                          { value: 'applicants', label: '청약자' },
                        ]"
                      />
                    </v-expansion-panel-text>
                  </v-expansion-panel>

                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      <v-icon icon="mdi-file-excel" class="me-2" />
                      Excel 파일 업로드
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-file-input
                        label="Excel 파일 선택"
                        accept=".xlsx,.xls"
                        prepend-icon="mdi-file-excel"
                        show-size
                      />
                      <v-alert type="info" variant="tonal" class="mt-2" density="compact">
                        첫 번째 열에 휴대폰 번호를 입력해주세요.
                      </v-alert>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>

                <!-- 선택된 수신자 목록 -->
                <div class="mt-4">
                  <div class="d-flex justify-content-between align-items-center mb-2">
                    <strong>선택된 수신자 ({{ recipientsList.length }}명)</strong>
                    <v-btn
                      size="small"
                      color="error"
                      variant="outlined"
                      @click="recipientsList = []"
                    >
                      전체 삭제
                    </v-btn>
                  </div>

                  <CCard v-if="recipientsList.length > 0" variant="outline">
                    <CCardBody class="p-2">
                      <div style="max-height: 200px; overflow-y: auto">
                        <v-chip
                          v-for="(recipient, index) in recipientsList"
                          :key="index"
                          class="ma-1"
                          closable
                          @click:close="removeRecipient(index)"
                        >
                          {{ recipient }}
                        </v-chip>
                      </div>
                    </CCardBody>
                  </CCard>

                  <v-alert v-else type="info" variant="tonal" density="compact">
                    수신자를 선택해주세요.
                  </v-alert>
                </div>
              </CCardBody>
            </CCard>
          </CCol>

          <!-- 메시지 작성 섹션 -->
          <CCol :md="6" :xs="12">
            <CCard class="mb-4">
              <CCardHeader>
                <v-icon icon="mdi-message-edit" class="me-2" />
                <strong>메시지 작성</strong>
              </CCardHeader>
              <CCardBody>
                <!-- 메시지 타입 선택 -->
                <CFormSelect
                  v-model="smsForm.messageType"
                  label="메시지 타입"
                  :options="[
                    { value: 'SMS', label: 'SMS (90자 이내)' },
                    { value: 'LMS', label: 'LMS (장문메시지)' },
                    { value: 'MMS', label: 'MMS (멀티미디어)' },
                  ]"
                  class="mb-3"
                />

                <!-- 템플릿 선택 -->
                <div class="mb-3">
                  <div class="d-flex justify-content-between align-items-center mb-2">
                    <CFormLabel>메시지 템플릿</CFormLabel>
                    <v-btn size="small" color="primary" variant="outlined" @click="selectTemplate">
                      템플릿 선택
                    </v-btn>
                  </div>
                  <CFormSelect
                    :options="[
                      { value: '', label: '직접 입력' },
                      { value: 'welcome', label: '환영 메시지' },
                      { value: 'payment', label: '납입 안내' },
                      { value: 'notice', label: '공지사항' },
                    ]"
                  />
                </div>

                <!-- 메시지 입력 -->
                <div class="mb-3">
                  <div class="d-flex justify-content-between align-items-center mb-2">
                    <CFormLabel>메시지 내용</CFormLabel>
                    <small class="text-muted">
                      {{ messageCount }}/{{ smsForm.messageType === 'SMS' ? '90' : '2000' }}자
                    </small>
                  </div>
                  <CFormTextarea
                    v-model="smsForm.message"
                    rows="6"
                    placeholder="전송할 메시지를 입력하세요..."
                    @input="messageCount = smsForm.message.length"
                  />
                </div>

                <!-- 발송자 번호 -->
                <CFormInput
                  v-model="smsForm.senderNumber"
                  label="발송자 번호"
                  placeholder="02-1234-5678"
                  class="mb-3"
                />

                <!-- 미리보기 버튼 -->
                <v-btn
                  color="info"
                  variant="outlined"
                  @click="previewMessage"
                  prepend-icon="mdi-eye"
                  block
                >
                  미리보기
                </v-btn>
              </CCardBody>
            </CCard>
          </CCol>
        </CRow>

        <!-- 발송 옵션 및 실행 -->
        <CCard>
          <CCardHeader>
            <v-icon icon="mdi-send" class="me-2" />
            <strong>발송 설정 및 실행</strong>
          </CCardHeader>
          <CCardBody>
            <CRow>
              <!-- 발송 옵션 -->
              <CCol :md="6" :xs="12">
                <div class="mb-3">
                  <CFormLabel>발송 시점</CFormLabel>
                  <v-radio-group v-model="smsForm.scheduledSend" inline>
                    <v-radio label="즉시 발송" :value="false" />
                    <v-radio label="예약 발송" :value="true" />
                  </v-radio-group>
                </div>

                <div v-if="smsForm.scheduledSend" class="mb-3">
                  <CRow>
                    <CCol :md="6">
                      <CFormInput v-model="smsForm.scheduleDate" type="date" label="발송 날짜" />
                    </CCol>
                    <CCol :md="6">
                      <CFormInput v-model="smsForm.scheduleTime" type="time" label="발송 시간" />
                    </CCol>
                  </CRow>
                </div>
              </CCol>

              <!-- 발송 실행 -->
              <CCol :md="6" :xs="12">
                <div class="text-center">
                  <v-btn
                    color="primary"
                    size="large"
                    @click="sendMessage"
                    :loading="isSending"
                    :disabled="recipientsList.length === 0 || !smsForm.message"
                    prepend-icon="mdi-send"
                    class="mb-3"
                  >
                    {{ smsForm.scheduledSend ? '예약 등록' : 'SMS 전송' }}
                  </v-btn>

                  <div v-if="isSending" class="mt-3">
                    <v-progress-linear v-model="sendProgress" color="primary" height="8" rounded />
                    <small class="text-muted mt-1"> 발송 중... {{ sendProgress }}% </small>
                  </div>
                </div>
              </CCol>
            </CRow>
          </CCardBody>
        </CCard>
      </v-tabs-window-item>

      <!-- 카카오 알림톡 탭 -->
      <v-tabs-window-item value="kakao">
        <CRow>
          <!-- 수신자 관리 섹션 (SMS와 동일) -->
          <CCol :md="6" :xs="12">
            <CCard class="mb-4">
              <CCardHeader>
                <v-icon icon="mdi-account-multiple" class="me-2" />
                <strong>수신자 관리</strong>
              </CCardHeader>
              <CCardBody>
                <!-- 수신자 입력 방법 선택 (SMS와 동일한 구조) -->
                <v-expansion-panels class="mb-3">
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      <v-icon icon="mdi-account-plus" class="me-2" />
                      개별 번호 입력
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <CRow class="align-items-end">
                        <CCol :md="8">
                          <CFormInput
                            v-model="kakaoForm.recipients"
                            placeholder="010-1234-5678"
                            label="휴대폰 번호"
                          />
                        </CCol>
                        <CCol :md="4">
                          <v-btn
                            color="primary"
                            @click="addRecipient"
                            prepend-icon="mdi-plus"
                            block
                          >
                            추가
                          </v-btn>
                        </CCol>
                      </CRow>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </CCardBody>
            </CCard>
          </CCol>

          <!-- 알림톡 작성 섹션 -->
          <CCol :md="6" :xs="12">
            <CCard class="mb-4">
              <CCardHeader>
                <v-icon icon="mdi-chat-processing" class="me-2" />
                <strong>알림톡 작성</strong>
              </CCardHeader>
              <CCardBody>
                <!-- 템플릿 선택 -->
                <CFormSelect
                  v-model="kakaoForm.templateId"
                  label="승인된 템플릿"
                  :options="[
                    { value: 'template1', label: '계약 완료 안내' },
                    { value: 'template2', label: '납입 안내' },
                    { value: 'template3', label: '공사 진행 상황' },
                  ]"
                  class="mb-3"
                />

                <!-- 템플릿 미리보기 -->
                <v-alert type="info" variant="tonal" class="mb-3">
                  <strong>템플릿 미리보기</strong>
                  <div class="mt-2 p-3 bg-grey-lighten-4 rounded">
                    안녕하세요 {{ name }}님,<br />
                    {{ project }} 관련하여 안내드립니다.<br />
                    자세한 내용은 고객센터로 문의하세요.
                  </div>
                </v-alert>

                <!-- 템플릿 변수 입력 -->
                <div class="mb-3">
                  <CFormLabel>템플릿 변수</CFormLabel>
                  <CRow>
                    <CCol :md="6">
                      <CFormInput label="이름 (name)" placeholder="예: 홍길동" class="mb-2" />
                    </CCol>
                    <CCol :md="6">
                      <CFormInput
                        label="프로젝트 (project)"
                        placeholder="예: 동춘지구 A블럭"
                        class="mb-2"
                      />
                    </CCol>
                  </CRow>
                </div>

                <!-- 버튼 설정 -->
                <div class="mb-3">
                  <CFormLabel>버튼 설정</CFormLabel>
                  <v-switch label="웹링크 버튼 추가" color="primary" hide-details class="mb-2" />
                  <CFormInput label="버튼명" placeholder="자세히 보기" class="mb-2" />
                  <CFormInput label="링크 URL" placeholder="https://example.com" />
                </div>
              </CCardBody>
            </CCard>
          </CCol>
        </CRow>

        <!-- 발송 설정 (SMS와 유사) -->
        <CCard>
          <CCardHeader>
            <v-icon icon="mdi-send" class="me-2" />
            <strong>발송 설정 및 실행</strong>
          </CCardHeader>
          <CCardBody>
            <CRow>
              <CCol :md="6" :xs="12">
                <div class="mb-3">
                  <CFormLabel>발송 시점</CFormLabel>
                  <v-radio-group v-model="kakaoForm.scheduledSend" inline>
                    <v-radio label="즉시 발송" :value="false" />
                    <v-radio label="예약 발송" :value="true" />
                  </v-radio-group>
                </div>
              </CCol>

              <CCol :md="6" :xs="12">
                <div class="text-center">
                  <v-btn
                    color="success"
                    size="large"
                    @click="sendMessage"
                    :loading="isSending"
                    :disabled="!kakaoForm.templateId || recipientsList.length === 0"
                    prepend-icon="mdi-chat"
                    class="mb-3"
                  >
                    {{ kakaoForm.scheduledSend ? '예약 등록' : '알림톡 전송' }}
                  </v-btn>
                </div>
              </CCol>
            </CRow>
          </CCardBody>
        </CCard>
      </v-tabs-window-item>
    </v-tabs-window>
  </ContentBody>
</template>

<style scoped>
.v-expansion-panel-text {
  padding: 16px !important;
}

.v-tabs {
  margin-bottom: 0;
}

.text-h6 {
  font-weight: 600;
}

.bg-grey-lighten-4 {
  background-color: #f5f5f5;
}
</style>
