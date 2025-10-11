<script lang="ts" setup>
import { ref } from 'vue'
import { btnLight } from '@/utils/cssMixins'
import { useNotice } from '@/store/pinia/notice'
import FormModal from '@/components/Modals/FormModal.vue'
import type { MessageTemplate } from '@/store/types/notice'

// Store
const notiStore = useNotice()

// Modal ref
const formModal = ref()

// Form state
const form = ref({
  title: '',
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
        message_type: form.value.message_type as 'SMS' | 'LMS' | 'MMS',
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
        ]"
        class="mb-3"
      />

      <!-- 메시지 내용 -->
      <div class="mb-3">
        <CFormLabel>메시지 내용</CFormLabel>
        <CFormTextarea v-model="form.content" rows="6" placeholder="메시지 내용을 입력하세요..." />
        <small class="text-grey"> 변수 사용 시: {이름}, {금액} 등의 형식으로 입력 가능 </small>
      </div>
    </CModalBody>

    <CModalFooter>
      <v-btn :color="btnLight" size="small" @click="closeModal" :disabled="submitting">
        취소
      </v-btn>
      <v-btn
        :color="editingId ? 'success' : 'primary'"
        size="small"
        @click="handleSubmit"
        :loading="submitting"
      >
        {{ editingId ? '수정' : '등록' }}
      </v-btn>
    </CModalFooter>

    <!-- 등록된 템플릿 목록 -->
    <CModalBody>
      <v-divider class="my-4" />

      <!-- 목록 헤더 -->
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h6 class="mb-0">
          <v-icon icon="mdi-format-list-bulleted" class="me-2" size="small" />
          등록된 템플릿 ({{ notiStore.messageTemplates.length }}개)
        </h6>
        <v-btn
          v-if="editingId"
          size="small"
          variant="outlined"
          color="primary"
          @click="handleCancelEdit"
        >
          새 템플릿 등록
        </v-btn>
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
            class="mb-2"
          >
            <template #prepend>
              <v-chip size="small" :color="getTypeColor(template.message_type)" class="me-2">
                {{ template.message_type }}
              </v-chip>
            </template>

            <v-list-item class="text-truncate">
              {{ template.title }} -
              <span class="text-grey">{{ template.content }}</span>
            </v-list-item>

            <template #append>
              <v-btn
                icon="mdi-pencil"
                size="small"
                variant="text"
                color="primary"
                @click="handleEdit(template)"
              />
              <v-btn
                icon="mdi-delete"
                size="small"
                variant="text"
                color="error"
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
      <v-card-title class="text-h6">템플릿 삭제</v-card-title>
      <v-card-text>
        정말 이 템플릿을 삭제하시겠습니까? 삭제된 템플릿은 복구할 수 없습니다.
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="showDeleteConfirm = false"> 취소 </v-btn>
        <v-btn color="error" @click="handleDelete"> 삭제 </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
