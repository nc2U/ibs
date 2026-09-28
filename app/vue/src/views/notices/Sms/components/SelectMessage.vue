<script lang="ts" setup>
import { computed, watch, ref, onMounted, nextTick } from 'vue'
import { useNotice } from '@/store/pinia/notice'
import { usePerms } from '@/composables/usePerms.ts'
import SenderNumberModal from './SenderNumberModal.vue'
import MessageTemplateModal from './MessageTemplateModal.vue'
import SpecialCharModal from './SpecialCharModal.vue'
import KakaoGuideModal from './KakaoGuideModal.vue'

// Props 정의
const activeTab = defineModel<string>('activeTab')
const smsForm = defineModel<any>('smsForm') as any
const kakaoForm = defineModel<any>('kakaoForm') as any
const messageCount = defineModel<number>('messageCount') as any

// Emits 정의
const emit = defineEmits<{
  selectTemplate: []
  'update:messageCount': [value: number]
  'update:hasVariables': [value: boolean]
  'update:variableNames': [value: string[]]
  'update:attachedImages': [value: File[]]
}>()

const { can, PERM } = usePerms()
const canNoticeManage = computed(() => can(PERM.NOTICE_CREATE) || can(PERM.NOTICE_UPDATE))

// Store
const notiStore = useNotice()

// Variable extraction function
const extractVariables = (content: string): string[] => {
  const regex = /\{([^}]+)\}/g
  const variables: string[] = []
  let match

  while ((match = regex.exec(content)) !== null) {
    const varName = match[1].trim()
    if (!variables.includes(varName)) {
      variables.push(varName)
    }
  }

  return variables
}

// Kakao variable extraction function (#{변수} or {변수})
const extractKakaoVariables = (content: string): string[] => {
  const regex = /#\{([^}]+)\}|\{([^}]+)\}/g
  const variables: string[] = []
  let match

  while ((match = regex.exec(content)) !== null) {
    const varName = (match[1] || match[2]).trim()
    if (!variables.includes(varName)) {
      variables.push(varName)
    }
  }

  return variables
}

// Sender number management
const senderNumberModal = ref()
const editingSenderNumber = ref<{ id: number; phone_number: string; label: string } | null>(null)

// Template management
const templateModal = ref()
const selectedTemplate = ref<string>('')

// Kakao guide modal
const kakaoGuideModal = ref()
const handleOpenKakaoGuide = () => {
  kakaoGuideModal.value?.openModal()
}

// Kakao template state
const selectedKakaoTemplateId = ref<string>('')
const kakaoVariableNames = ref<string[]>([])

// Preview management
const showPreview = ref(false)

// Special character modal
const specialCharModal = ref()
const messageTextareaEl = ref<HTMLTextAreaElement | null>(null)
const cursorPosition = ref(0)

// MMS image upload
const attachedImages = ref<File[]>([])
const imagePreviewUrls = ref<string[]>([])
const isDragging = ref(false)
const uploadError = ref<string>('')
const fileInputRef = ref<HTMLInputElement | null>(null)

// Computed for sender number options
const senderNumberOptions = computed(() => {
  if (!Array.isArray(notiStore.senderNumbers)) return []
  return notiStore.senderNumbers.map(item => ({
    value: item.phone_number,
    label: item.label ? `${item.phone_number} (${item.label})` : item.phone_number,
  }))
})

// Computed for SMS template options (exclude KAKAO)
const templateOptions = computed(() => {
  if (!Array.isArray(notiStore.messageTemplates)) return []
  return notiStore.messageTemplates
    .filter(item => item.message_type !== 'KAKAO')
    .map(item => ({
      value: item.id.toString(),
      label: `${item.title} (${item.message_type})`,
      template: item,
    }))
})

// Computed for Kakao template options (only KAKAO)
const kakaoTemplateOptions = computed(() => {
  if (!Array.isArray(notiStore.messageTemplates)) return []
  return notiStore.messageTemplates
    .filter(item => item.message_type === 'KAKAO')
    .map(item => ({
      value: item.id.toString(),
      label: item.template_code
        ? `${item.title} [${item.template_code}]`
        : `${item.title} (코드 미등록)`,
      template: item,
    }))
})

// Handle Kakao template selection
const handleKakaoTemplateSelect = () => {
  nextTick(() => {
    if (!selectedKakaoTemplateId.value) {
      kakaoForm.value.templateId = ''
      kakaoForm.value.message = ''
      kakaoForm.value.parameters = {}
      kakaoVariableNames.value = []
      return
    }

    const template = notiStore.messageTemplates.find(
      t => t.id.toString() === selectedKakaoTemplateId.value,
    )

    if (template) {
      kakaoForm.value.templateId = template.template_code || ''
      kakaoForm.value.message = template.content

      const vars = extractKakaoVariables(template.content)
      kakaoVariableNames.value = vars

      // parameters 객체 초기화
      const params: Record<string, string> = {}
      vars.forEach(v => {
        params[v] = kakaoForm.value.parameters?.[v] || ''
      })
      kakaoForm.value.parameters = params
    }
  })
}

// Real-time Kakao preview with replaced variables
const kakaoPreviewMessage = computed(() => {
  if (!kakaoForm.value.message) return ''
  let result = kakaoForm.value.message
  const params = kakaoForm.value.parameters || {}

  for (const [key, value] of Object.entries(params)) {
    const displayVal = (value as string) || `[${key}]`
    const regexHash = new RegExp(`#{${key}}`, 'g')
    const regexBrace = new RegExp(`{${key}}`, 'g')
    result = result.replace(regexHash, displayVal).replace(regexBrace, displayVal)
  }

  return result
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
    if (!selectedTemplate.value) {
      // 템플릿 선택 해제 시 (직접 입력 선택 시)
      // 변수 상태 초기화
      emit('update:hasVariables', false as any)
      emit('update:variableNames', [] as any)
      // 메시지 내용 초기화
      smsForm.value.message = ''
      return
    }

    const template = notiStore.messageTemplates.find(
      t => t.id.toString() === selectedTemplate.value,
    )

    if (template) {
      smsForm.value.messageType = template.message_type
      smsForm.value.message = template.content

      // 템플릿 내용에서 변수 추출
      const variables = extractVariables(template.content)
      const hasVariables = variables.length > 0

      // 부모 컴포넌트에 변수 정보 전달
      emit('update:hasVariables', hasVariables as any)
      emit('update:variableNames', variables as any)
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

// MMS 이미지 업로드 관련 함수
const validateImage = (file: File): { valid: boolean; error?: string } => {
  // 1. 파일 형식 체크: JPG만 허용
  const validTypes = ['image/jpeg', 'image/jpg']
  if (!validTypes.includes(file.type)) {
    return { valid: false, error: 'JPG 파일만 업로드 가능합니다.' }
  }

  // 2. 파일 크기 체크: 100KB 미만
  const maxSize = 100 * 1024 // 100KB in bytes
  if (file.size >= maxSize) {
    return {
      valid: false,
      error: `이미지 크기는 100KB 미만이어야 합니다. (현재: ${(file.size / 1024).toFixed(1)}KB)`,
    }
  }

  return { valid: true }
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    addImages(Array.from(target.files))
  }
  // Reset input value to allow selecting the same file again
  if (target) target.value = ''
}

const addImages = (files: File[]) => {
  uploadError.value = ''

  for (const file of files) {
    const validation = validateImage(file)
    if (!validation.valid) {
      uploadError.value = validation.error || '파일 업로드 실패'
      continue
    }

    // 이미 추가된 파일인지 체크
    const isDuplicate = attachedImages.value.some(
      img => img.name === file.name && img.size === file.size,
    )
    if (isDuplicate) {
      uploadError.value = '이미 추가된 이미지입니다.'
      continue
    }

    // 파일 추가
    attachedImages.value.push(file)

    // 미리보기 URL 생성
    const reader = new FileReader()
    reader.onload = e => {
      if (e.target?.result) {
        imagePreviewUrls.value.push(e.target.result as string)
      }
    }
    reader.readAsDataURL(file)
  }
}

const removeImage = (index: number) => {
  attachedImages.value.splice(index, 1)
  imagePreviewUrls.value.splice(index, 1)
  uploadError.value = ''
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = true
}

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = false
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = false

  if (event.dataTransfer?.files) {
    addImages(Array.from(event.dataTransfer.files))
  }
}

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

// Computed for total image size
const totalImageSize = computed(() => {
  return attachedImages.value.reduce((sum, file) => sum + file.size, 0)
})

const formattedTotalSize = computed(() => {
  const sizeInKB = totalImageSize.value / 1024
  return `${sizeInKB.toFixed(1)}KB`
})

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

// 메시지 타입 변경 감지 - MMS가 아닐 때 첨부 이미지 초기화
watch(
  () => smsForm.value?.messageType,
  newType => {
    if (newType !== 'MMS' && attachedImages.value.length > 0) {
      attachedImages.value = []
      imagePreviewUrls.value = []
      uploadError.value = ''
      emit('update:attachedImages', [])
    }
  },
)

// 첨부 이미지 변경 감지 - 부모 컴포넌트에 전달
watch(
  attachedImages,
  newImages => {
    emit('update:attachedImages', newImages)
  },
  { deep: true },
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
                  v-if="canNoticeManage"
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

            <!-- MMS 이미지 첨부 (MMS 선택 시에만 표시) -->
            <div v-if="smsForm.messageType === 'MMS'" class="mb-3">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <CFormLabel>이미지 첨부</CFormLabel>
                <small class="text-muted">JPG 파일만 가능 (100KB 미만)</small>
              </div>

              <!-- 파일 입력 (숨김) -->
              <input
                ref="fileInputRef"
                type="file"
                accept="image/jpeg,image/jpg"
                multiple
                style="display: none"
                @change="handleFileSelect"
              />

              <!-- 드래그 앤 드롭 영역 -->
              <div
                class="upload-area"
                :class="{ dragging: isDragging }"
                @dragover="handleDragOver"
                @dragleave="handleDragLeave"
                @drop="handleDrop"
                @click="triggerFileInput"
              >
                <v-icon size="48" color="grey" class="mb-2">mdi-image-plus</v-icon>
                <p class="text-center text-muted mb-2">
                  클릭하거나 파일을 드래그하여 이미지 업로드
                </p>
                <small class="text-muted">JPG 형식 | 최대 100KB</small>
              </div>

              <!-- 에러 메시지 -->
              <v-alert v-if="uploadError" type="error" variant="tonal" class="mt-2" closable>
                {{ uploadError }}
              </v-alert>

              <!-- 이미지 미리보기 갤러리 -->
              <div v-if="attachedImages.length > 0" class="mt-3">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <small class="text-muted">첨부된 이미지 ({{ attachedImages.length }}개)</small>
                  <small class="text-muted">총 용량: {{ formattedTotalSize }}</small>
                </div>
                <div class="image-preview-gallery">
                  <div
                    v-for="(url, index) in imagePreviewUrls"
                    :key="index"
                    class="image-preview-item"
                  >
                    <img :src="url" :alt="`첨부 이미지 ${index + 1}`" />
                    <div class="image-info">
                      <small>{{ attachedImages[index].name }}</small>
                      <small>{{ (attachedImages[index].size / 1024).toFixed(1) }}KB</small>
                    </div>
                    <v-btn
                      icon
                      size="x-small"
                      color="error"
                      class="remove-btn"
                      @click.stop="removeImage(index)"
                    >
                      <v-icon size="16">mdi-close</v-icon>
                    </v-btn>
                  </div>
                </div>
              </div>
            </div>

            <!-- 발송자 번호 -->
            <div class="mb-3">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <CFormLabel>발송자 번호</CFormLabel>
                <v-btn
                  v-if="canNoticeManage"
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

                  <!-- MMS 이미지 미리보기 -->
                  <div
                    v-if="smsForm.messageType === 'MMS' && imagePreviewUrls.length > 0"
                    class="mt-3"
                  >
                    <div class="preview-images-container">
                      <img
                        v-for="(url, index) in imagePreviewUrls"
                        :key="index"
                        :src="url"
                        :alt="`첨부 이미지 ${index + 1}`"
                        class="preview-image"
                      />
                    </div>
                  </div>
                </div>
              </div>
              <small class="text-muted d-block mt-2">
                타입: {{ smsForm.messageType }} | 길이: {{ smsForm.message?.length || 0 }}자
                <span v-if="smsForm.messageType === 'MMS' && attachedImages.length > 0">
                  | 이미지: {{ attachedImages.length }}개 ({{ formattedTotalSize }})
                </span>
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
            <!-- 1. 필수 사전 절차 안내 배너 -->
            <v-alert
              type="warning"
              variant="tonal"
              density="compact"
              class="mb-3"
              icon="mdi-shield-alert-outline"
            >
              <div class="d-flex justify-content-between align-items-center">
                <div>
                  <strong>카카오 알림톡 서비스 연동 안내</strong>
                  <div class="text-caption text-medium-emphasis mt-1">
                    카카오톡 채널 비즈니스 인증과 iwinv 발신 프로필 등록, 사전 템플릿 검수 승인이
                    필요합니다.
                  </div>
                </div>
                <v-btn
                  size="small"
                  color="warning"
                  variant="flat"
                  prepend-icon="mdi-help-circle-outline"
                  class="ms-2 text-none"
                  @click="handleOpenKakaoGuide"
                >
                  사전 절차 가이드
                </v-btn>
              </div>
            </v-alert>

            <!-- 2. 발송자 번호 선택 (사전 등록된 발신번호) -->
            <div class="mb-3">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <CFormLabel>발송자 번호 (사전 등록 발신번호)</CFormLabel>
                <v-btn
                  v-if="canNoticeManage"
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
                v-model="kakaoForm.senderNumber"
                :options="[{ value: '', label: '발신번호 선택 (필수)' }, ...senderNumberOptions]"
              />
            </div>

            <!-- 3. 승인된 템플릿 선택 -->
            <div class="mb-3">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <CFormLabel>승인된 알림톡 템플릿</CFormLabel>
                <v-btn
                  v-if="canNoticeManage"
                  size="small"
                  color="primary"
                  variant="outlined"
                  prepend-icon="mdi-plus"
                  @click="handleOpenTemplateModal"
                >
                  템플릿 관리
                </v-btn>
              </div>
              <CFormSelect
                v-model="selectedKakaoTemplateId"
                :options="[{ value: '', label: '템플릿을 선택하세요' }, ...kakaoTemplateOptions]"
                @change="handleKakaoTemplateSelect"
              />
              <div v-if="kakaoForm.templateId" class="mt-1 d-flex justify-content-between">
                <small class="text-primary font-weight-bold">
                  템플릿 코드: {{ kakaoForm.templateId }}
                </small>
                <small class="text-medium-emphasis"> 변수 {{ kakaoVariableNames.length }}개 </small>
              </div>
            </div>

            <!-- 4. 템플릿 변수 입력 (템플릿에 가변 변수가 포함된 경우 동적 렌더링) -->
            <div v-if="kakaoVariableNames.length > 0" class="mb-3">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <CFormLabel>템플릿 변수 값 설정</CFormLabel>
                <small class="text-muted">공통 적용 기본값</small>
              </div>
              <CRow>
                <CCol v-for="varName in kakaoVariableNames" :key="varName" :md="6" class="mb-2">
                  <CFormInput
                    v-model="kakaoForm.parameters[varName]"
                    :label="varName"
                    :placeholder="`#{${varName}} 에 들어갈 값`"
                  />
                </CCol>
              </CRow>
              <small class="text-medium-emphasis d-block mt-1">
                ※ 위 입력값은 수신자 메시지의 해당 변수에 치환되어 발송됩니다.
              </small>
            </div>

            <!-- 5. 실시간 알림톡 카드 미리보기 -->
            <div v-if="kakaoForm.message" class="mb-3">
              <CFormLabel>알림톡 도착 미리보기</CFormLabel>
              <div class="kakao-preview-card p-3 rounded">
                <div
                  class="d-flex align-items-center justify-content-between pb-2 mb-2 border-bottom"
                >
                  <div class="d-flex align-items-center">
                    <v-icon icon="mdi-chat" color="amber-darken-3" class="me-2" size="20" />
                    <strong style="color: #3c1e1e; font-size: 13px">알림톡 도착</strong>
                  </div>
                  <small style="color: #796060; font-size: 11px">iwinv 인증 채널</small>
                </div>
                <div
                  class="kakao-preview-body"
                  style="white-space: pre-wrap; font-size: 13px; line-height: 1.6; color: #1e1e1e"
                >
                  {{ kakaoPreviewMessage }}
                </div>
              </div>
            </div>

            <!-- 6. 실패 시 대체 문자(Failover: reSend) 발송 설정 -->
            <CCard class="mb-3 border-dashed bg-light-subtle">
              <CCardBody class="p-3">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <strong>실패 시 대체 문자(SMS/LMS) 발송</strong>
                    <div class="text-caption text-medium-emphasis">
                      알림톡 차단자, 카카오톡 미사용자 등 전송 실패 시 일반 문자로 자동 전환 발송
                    </div>
                  </div>
                  <v-switch
                    v-model="kakaoForm.reSend"
                    color="primary"
                    hide-details
                    density="compact"
                  />
                </div>

                <div v-if="kakaoForm.reSend" class="mt-3 pt-3 border-top">
                  <v-radio-group
                    v-model="kakaoForm.resendType"
                    inline
                    density="compact"
                    class="mb-2"
                  >
                    <v-radio label="알림톡 내용 그대로 발송" value="Y" />
                    <v-radio label="대체 문자 내용 직접 입력" value="N" />
                  </v-radio-group>

                  <div v-if="kakaoForm.resendType === 'N'">
                    <CFormInput
                      v-model="kakaoForm.resendTitle"
                      label="대체 문자 제목 (LMS용)"
                      placeholder="예: [안내] 알림 메시지"
                      class="mb-2"
                    />
                    <CFormTextarea
                      v-model="kakaoForm.resendContent"
                      label="대체 문자 내용"
                      rows="3"
                      placeholder="알림톡 실패 시 대신 발송할 문자 내용을 입력하세요..."
                    />
                  </div>
                </div>
              </CCardBody>
            </CCard>
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

    <!-- Kakao Guide Modal -->
    <KakaoGuideModal ref="kakaoGuideModal" />
  </CCol>
</template>

<style scoped lang="scss">
.kakao-preview-card {
  max-width: 360px;
  width: 100%;
  background: #fae100;
  border: 1px solid #e2cb00;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

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

  // MMS 미리보기 내 이미지
  .preview-images-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
  }

  .preview-image {
    width: 80px;
    height: 80px;
    object-fit: cover;
    border-radius: 4px;
    border: 1px solid #ddd;
  }
}

// MMS 이미지 업로드 영역
.upload-area {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 32px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #fafafa;

  &:hover {
    border-color: #1976d2;
    background-color: #f5f5f5;
  }

  &.dragging {
    border-color: #1976d2;
    background-color: #e3f2fd;
  }
}

// 이미지 미리보기 갤러리
.image-preview-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.image-preview-item {
  position: relative;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
  transition: box-shadow 0.2s ease;

  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }

  img {
    width: 100%;
    height: 120px;
    object-fit: cover;
    display: block;
  }

  .image-info {
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 4px;

    small {
      font-size: 11px;
      color: #666;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }

  .remove-btn {
    position: absolute;
    top: 4px;
    right: 4px;
    background-color: rgba(255, 255, 255, 0.9) !important;

    &:hover {
      background-color: rgba(255, 255, 255, 1) !important;
    }
  }
}

.dark-theme {
  .message-preview-box {
    background: #475b49;
    border-color: #3a3b45;
    color: #fff;
  }

  .upload-area {
    background-color: #2a2a2a;
    border-color: #555;

    &:hover {
      border-color: #1976d2;
      background-color: #333;
    }

    &.dragging {
      border-color: #1976d2;
      background-color: #1e3a5f;
    }
  }

  .image-preview-item {
    background: #2a2a2a;
    border-color: #555;

    .image-info small {
      color: #aaa;
    }

    .remove-btn {
      background-color: rgba(50, 50, 50, 0.9) !important;

      &:hover {
        background-color: rgba(50, 50, 50, 1) !important;
      }
    }
  }
}
</style>
