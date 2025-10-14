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
  'update:hasVariables': [value: boolean]
  'update:variableNames': [value: string[]]
  'update:attachedImages': [value: File[]]
}>()

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
