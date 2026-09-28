<script lang="ts" setup>
import { ref } from 'vue'
import { useNotice } from '@/store/pinia/notice'
import type { MessageTemplate } from '@/store/types/notice'
import FormModal from '@/components/Modals/FormModal.vue'

// Store
const notiStore = useNotice()

// Modal ref
const formModal = ref()

// Form state
const form = ref({
  title: '',
  template_code: '',
  message_type: 'SMS',
  content: '',
})

const submitting = ref(false)
const editingId = ref<number | null>(null)
const showDeleteConfirm = ref(false)
const deletingId = ref<number | null>(null)

const resetForm = () => {
  form.value = {
    title: '',
    template_code: '',
    message_type: 'SMS',
    content: '',
  }
  editingId.value = null
}

const openModal = () => {
  formModal.value?.callModal()
}

const closeModal = () => {
  resetForm()
  formModal.value?.close()
}

const handleSubmit = async () => {
  if (!form.value.title) {
    alert('템플릿 제목을 입력해주세요.')
    return
  }

  if (form.value.message_type === 'KAKAO' && !form.value.template_code) {
    alert('카카오 알림톡은 승인된 템플릿 코드가 필수입니다.')
    return
  }

  if (!form.value.content) {
    alert('메시지 내용을 입력해주세요.')
    return
  }

  submitting.value = true

  try {
    if (editingId.value) {
      // 수정 모드
      await notiStore.updateMessageTemplate(editingId.value, {
        title: form.value.title,
        template_code: form.value.template_code,
        message_type: form.value.message_type as 'SMS' | 'LMS' | 'MMS' | 'KAKAO',
        content: form.value.content,
      })
    } else {
      // 생성 모드
      await notiStore.createMessageTemplate(form.value)
    }
    resetForm()
  } catch (error) {
    console.error('메시지 템플릿 등록/수정 실패:', error)
  } finally {
    submitting.value = false
  }
}

// 템플릿 수정
const handleEdit = (template: MessageTemplate) => {
  editingId.value = template.id
  form.value = {
    title: template.title,
    template_code: template.template_code || '',
    message_type: template.message_type,
    content: template.content,
  }
}

// 수정 취소 (새 템플릿 등록 모드로 전환)
const handleCancelEdit = () => {
  resetForm()
}

// 삭제 확인
const confirmDelete = (id: number) => {
  deletingId.value = id
  showDeleteConfirm.value = true
}

// 삭제 실행
const handleDelete = async () => {
  if (!deletingId.value) return

  try {
    await notiStore.deleteMessageTemplate(deletingId.value)
    showDeleteConfirm.value = false
    deletingId.value = null
  } catch (error) {
    console.error('템플릿 삭제 실패:', error)
  }
}

// 타입별 색상
const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    SMS: 'blue',
    LMS: 'green',
    MMS: 'purple',
    KAKAO: 'warning',
  }
  return colors[type] || 'grey'
}

defineExpose({ openModal, closeModal })
</script>

<template>
  <FormModal ref="formModal">
    <template #icon>
      <v-icon icon="mdi-text-box" size="small" color="primary" class="mr-2" />
    </template>
    <template #header>
      {{ editingId ? '메시지 템플릿 수정' : '메시지 템플릿 등록' }}
    </template>

    <CModalBody>
      <!-- 템플릿 제목 -->
      <CFormInput
        v-model="form.title"
        label="템플릿 제목"
        placeholder="예: 납입 안내 템플릿"
        required
        class="mb-3"
      />

      <!-- 메시지 타입 -->
      <CFormSelect
        v-model="form.message_type"
        label="메시지 타입"
        :options="[
          { value: 'SMS', label: 'SMS (90자 이내)' },
          { value: 'LMS', label: 'LMS (장문메시지)' },
          { value: 'MMS', label: 'MMS (멀티미디어)' },
          { value: 'KAKAO', label: '카카오 알림톡' },
        ]"
        class="mb-3"
      />

      <!-- 카카오 알림톡 승인 템플릿 코드 -->
      <div v-if="form.message_type === 'KAKAO'" class="mb-3">
        <CFormInput
          v-model="form.template_code"
          label="카카오 템플릿 코드 (templateCode)"
          placeholder="iwinv 콘솔에서 승인받은 템플릿 코드 (예: TEMPLATE_001)"
          required
        />
        <small class="text-primary mt-1 d-block">
          ※ iwinv/카카오톡 채널에서 사전 검수 승인된 템플릿 코드를 정확히 입력해야 합니다.
        </small>
      </div>

      <!-- 메시지 내용 -->
      <div class="mb-3">
        <div class="d-flex justify-content-between align-items-center mb-1">
          <CFormLabel class="mb-0">메시지 내용</CFormLabel>
          <small class="text-muted">
            {{
              form.message_type === 'KAKAO'
                ? '변수 표기: #{변수명} 또는 {변수명}'
                : '변수 표기: {변수명}'
            }}
          </small>
        </div>
        <CFormTextarea
          v-model="form.content"
          rows="6"
          :placeholder="
            form.message_type === 'KAKAO'
              ? '카카오에 승인된 템플릿 본문과 토씨 하나까지 정확히 일치해야 합니다.\n예: 안녕하세요 #{이름}님, #{프로젝트} 안내드립니다.'
              : '메시지 내용을 입력하세요...'
          "
        />
      </div>
    </CModalBody>

    <CModalFooter>
      <v-btn
        :color="editingId ? 'success' : 'primary'"
        size="small"
        @click="handleSubmit"
        :loading="submitting"
      >
        {{ editingId ? '수정' : '등록' }}
      </v-btn>

      <v-btn v-if="editingId" size="small" color="primary" @click="handleCancelEdit">
        새 템플릿
      </v-btn>
      <v-btn color="light" size="small" @click="closeModal" :disabled="submitting" flat>
        취소
      </v-btn>
    </CModalFooter>

    <!-- 등록된 템플릿 목록 -->
    <CModalBody>
      <v-divider class="my-4" />

      <!-- 목록 헤더 -->
      <div class="d-flex justify-content-between align-items-center mb-1">
        <h6 class="mb-0">
          <v-icon icon="mdi-format-list-bulleted" class="me-2" size="small" />
          등록된 템플릿 ({{ notiStore.messageTemplates.length }}개)
        </h6>
      </div>

      <!-- 템플릿 목록 -->
      <div style="max-height: 300px; overflow-y: auto">
        <v-alert v-if="notiStore.messageTemplates.length === 0" type="info" variant="tonal">
          등록된 템플릿이 없습니다.
        </v-alert>

        <v-list v-else density="compact">
          <v-list-item
            v-for="template in notiStore.messageTemplates"
            :key="template.id"
            :class="{ 'bg-primary-lighten-5': editingId === template.id }"
            class="py-0"
          >
            <template #prepend>
              <v-chip size="small" :color="getTypeColor(template.message_type)" class="me-2">
                {{ template.message_type }}
              </v-chip>
            </template>

            <v-list-item class="text-truncate">
              {{ template.title }}
              <small
                v-if="template.template_code"
                class="text-amber-darken-3 font-weight-bold ms-1"
              >
                [{{ template.template_code }}]
              </small>
              - <span class="text-grey">{{ template.content }}</span>
            </v-list-item>

            <template #append>
              <v-btn
                icon="mdi-pencil"
                size="20"
                rounded
                variant="text"
                color="success"
                @click="handleEdit(template)"
              />
              <v-btn
                icon="mdi-delete"
                size="20"
                rounded
                variant="text"
                color="grey"
                @click="confirmDelete(template.id)"
              />
            </template>
          </v-list-item>
        </v-list>
      </div>
    </CModalBody>
  </FormModal>

  <!-- 삭제 확인 다이얼로그 -->
  <v-dialog v-model="showDeleteConfirm" max-width="400px">
    <v-card>
      <v-card-title class="">템플릿 삭제</v-card-title>
      <v-card-text>
        정말 이 템플릿을 삭제하시겠습니까? 삭제된 템플릿은 복구할 수 없습니다.
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn size="small" color="error" @click="handleDelete"> 삭제 </v-btn>
        <v-btn size="small" @click="showDeleteConfirm = false" flat> 취소 </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
