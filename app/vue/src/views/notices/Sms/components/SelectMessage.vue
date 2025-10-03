<script lang="ts" setup>
import { computed, watch } from 'vue'

// Props 정의
const activeTab = defineModel<string>('activeTab')
const smsForm = defineModel<any>('smsForm') as any
const kakaoForm = defineModel<any>('kakaoForm') as any
const messageCount = defineModel<number>('messageCount') as any

// Emits 정의
const emit = defineEmits<{
  selectTemplate: []
  previewMessage: []
  'update:messageCount': [value: number]
}>()

// Computed 속성들
const project = computed(() => '동춘1구역9블럭지역주택조합')

// SMS 메시지 변경 감지 및 자동 타입 변경
watch(
  () => smsForm.value?.message,
  newMessage => {
    if (newMessage === undefined) return

    const messageLength = newMessage.length

    // 메시지 길이에 따라 자동으로 SMS/LMS 전환
    if (messageLength > 90 && smsForm.value?.messageType === 'SMS')
      smsForm.value.messageType = 'LMS'
    else if (messageLength <= 90 && smsForm.value?.messageType === 'LMS')
      smsForm.value.messageType = 'SMS'
  },
  { immediate: true, deep: true },
)

const handleSelectTemplate = () => {
  emit('selectTemplate')
}

const handlePreviewMessage = () => {
  emit('previewMessage')
}
</script>

<template>
  <CCol :md="6" :xs="12">
    <CCard class="mb-4">
      <CCardHeader class="p-0">
        <v-tabs v-model="activeTab" align-tabs="center">
          <v-tab value="sms" prepend-icon="mdi-message-text" variant="tonal">
            <span class="strong">SMS 전송</span>
          </v-tab>
          <v-tab value="kakao" prepend-icon="mdi-chat" variant="tonal">
            <span class="strong">카카오 알림톡</span>
          </v-tab>
        </v-tabs>
      </CCardHeader>

      <CCardBody>
        <v-tabs-window v-model="activeTab">
          <!-- SMS 전송 탭 -->
          <v-tabs-window-item value="sms">
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
                <v-btn
                  size="small"
                  color="primary"
                  variant="outlined"
                  @click="handleSelectTemplate"
                >
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
                  {{ smsForm?.message?.length || 0 }}/{{
                    smsForm.messageType === 'SMS' ? '90' : '2000'
                  }}자
                </small>
              </div>
              <CFormTextarea
                v-model="smsForm.message"
                rows="6"
                placeholder="전송할 메시지를 입력하세요..."
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
              @click="handlePreviewMessage"
              prepend-icon="mdi-eye"
              block
              class="mb-3"
            >
              미리보기
            </v-btn>
          </v-tabs-window-item>

          <!-- 카카오 알림톡 탭 -->
          <v-tabs-window-item value="kakao">
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
                안녕하세요 [이름]님,<br />
                [프로젝트] 관련하여 안내드립니다.<br />
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
              <CFormInput label="링크 URL" placeholder="https://example.com" class="mb-3" />
            </div>
          </v-tabs-window-item>
        </v-tabs-window>
      </CCardBody>
    </CCard>
  </CCol>
</template>
