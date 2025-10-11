<script lang="ts" setup>
import { computed, watch, ref, onMounted, nextTick } from 'vue'
import { useNotice } from '@/store/pinia/notice'
import SenderNumberModal from './SenderNumberModal.vue'
import MessageTemplateModal from './MessageTemplateModal.vue'
import SpecialCharModal from './SpecialCharModal.vue'

// Props 정의
const activeTab = defineModel<string>('activeTab')
const smsForm = defineModel<any>('smsForm') as any
const kakaoForm = defineModel<any>('kakaoForm') as any
const messageCount = defineModel<number>('messageCount') as any

// Emits 정의
const emit = defineEmits<{
  selectTemplate: []
  'update:messageCount': [value: number]
}>()

// Store
const notiStore = useNotice()

// Sender number management
const senderNumberModal = ref()
const editingSenderNumber = ref<{ id: number; phone_number: string; label: string } | null>(null)

// Template management
const templateModal = ref()
const selectedTemplate = ref<string>('')

// Preview management
const showPreview = ref(false)

// Special character modal
const specialCharModal = ref()
const messageTextareaEl = ref<HTMLTextAreaElement | null>(null)
const cursorPosition = ref(0)

// Computed for sender number options
const senderNumberOptions = computed(() => {
  if (!Array.isArray(notiStore.senderNumbers)) return []
  return notiStore.senderNumbers.map(item => ({
    value: item.phone_number,
    label: item.label ? `${item.phone_number} (${item.label})` : item.phone_number,
  }))
})

// Computed for template options
const templateOptions = computed(() => {
  if (!Array.isArray(notiStore.messageTemplates)) return []
  return notiStore.messageTemplates.map(item => ({
    value: item.id.toString(),
    label: `${item.title} (${item.message_type})`,
    template: item,
  }))
})

// Load sender numbers and templates on mount
onMounted(async () => {
  try {
    await notiStore.fetchSenderNumbers()
    await notiStore.fetchMessageTemplates()
  } catch (error) {
    console.error('데이터 조회 실패:', error)
  }
})

const handleOpenSenderModal = () => {
  editingSenderNumber.value = null
  senderNumberModal.value?.openModal()
}

const handleOpenTemplateModal = () => {
  templateModal.value?.openModal()
}

const handleTemplateSelect = () => {
  nextTick(() => {
    if (!selectedTemplate.value) return

    const template = notiStore.messageTemplates.find(
      t => t.id.toString() === selectedTemplate.value,
    )

    if (template) {
      smsForm.value.messageType = template.message_type
      smsForm.value.message = template.content
    }
  })
}

// textarea 엘리먼트 업데이트
const updateTextareaRef = (event: Event) => {
  const target = event.target as HTMLTextAreaElement
  messageTextareaEl.value = target
  cursorPosition.value = target.selectionStart || 0
}

// 특수문자 모달 열기
const handleOpenSpecialCharModal = () => {
  specialCharModal.value?.openModal()
}

// 특수문자 삽입
const insertSpecialChar = (char: string) => {
  const currentMessage = smsForm.value.message || ''
  const position = cursorPosition.value

  // 커서 위치에 특수문자 삽입
  smsForm.value.message = currentMessage.slice(0, position) + char + currentMessage.slice(position)

  // 다음 틱에서 커서 위치를 삽입된 문자 다음으로 이동
  nextTick(() => {
    const el = messageTextareaEl.value as HTMLTextAreaElement | null
    if (el) {
      const newPosition = position + char.length
      el.focus()
      el.setSelectionRange(newPosition, newPosition)
      cursorPosition.value = newPosition
    }
  })
}

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
</script>

<template>
  <CCol :xs="12">
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
                  prepend-icon="mdi-plus"
                  @click="handleOpenTemplateModal"
                >
                  관리
                </v-btn>
              </div>
              <CFormSelect
                v-model="selectedTemplate"
                :options="[{ value: '', label: '직접 입력' }, ...templateOptions]"
                @change="handleTemplateSelect"
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
                @click="updateTextareaRef"
                @keyup="updateTextareaRef"
                @focus="updateTextareaRef"
              />
              <v-btn
                size="small"
                color="grey"
                variant="outlined"
                prepend-icon="mdi-code-braces"
                class="mt-2"
                @click="handleOpenSpecialCharModal"
              >
                특수문자
              </v-btn>
            </div>

            <!-- 발송자 번호 -->
            <div class="mb-3">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <CFormLabel>발송자 번호</CFormLabel>
                <v-btn
                  size="small"
                  color="primary"
                  variant="outlined"
                  prepend-icon="mdi-plus"
                  @click="handleOpenSenderModal"
                >
                  등록
                </v-btn>
              </div>
              <CFormSelect
                v-model="smsForm.senderNumber"
                :options="[{ value: '', label: '발신번호 선택' }, ...senderNumberOptions]"
              />
            </div>

            <!-- 미리보기 영역 (토글) -->
            <v-alert v-if="showPreview" type="info" variant="tonal" class="mb-3">
              <strong>📱 {{ smsForm.messageType }} 미리보기</strong>
              <div class="d-flex mt-3">
                <div class="p-3 rounded message-preview-box">
                  {{ smsForm.message || '메시지를 입력하세요...' }}
                </div>
              </div>
              <small class="text-muted d-block mt-2">
                타입: {{ smsForm.messageType }} | 길이: {{ smsForm.message?.length || 0 }}자
              </small>
            </v-alert>

            <!-- 미리보기 버튼 -->
            <v-btn
              color="info"
              variant="outlined"
              @click="showPreview = !showPreview"
              :prepend-icon="showPreview ? 'mdi-eye-off' : 'mdi-eye'"
              block
              class="mb-3"
            >
              {{ showPreview ? '미리보기 숨기기' : '미리보기' }}
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

    <!-- Sender Number Modal -->
    <SenderNumberModal ref="senderNumberModal" :edit-item="editingSenderNumber" />

    <!-- Message Template Modal -->
    <MessageTemplateModal ref="templateModal" />

    <!-- Special Character Modal -->
    <SpecialCharModal ref="specialCharModal" @insert="insertSpecialChar" />
  </CCol>
</template>

<style scoped lang="scss">
.message-preview-box {
  max-width: 360px;
  width: 100%;
  background: lightyellow;
  color: #333;
  border: 1px solid #e0e0e0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 15px;
  line-height: 1.5;
}
.dark-theme {
  .message-preview-box {
    background: #475b49;
    border-color: #3a3b45;
    color: #fff;
  }
}
</style>
